package test

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/helm"
	http_helper "github.com/gruntwork-io/terratest/modules/http-helper"
	"github.com/gruntwork-io/terratest/modules/k8s"
	"github.com/gruntwork-io/terratest/modules/random"
	"github.com/gruntwork-io/terratest/modules/shell"

	"github.com/anchore/test-infra/src/utils"
)

var testName = "test-engine"

func TestChartDeploysEngine(t *testing.T) {
	// Path to the helm chart to test, or name from official stable repo
	helmChartPath := "stable/anchore-engine"
	// helmChartPath, err := filepath.Abs("../../stable/anchore-engine")
	// require.NoError(t, err)

	kubectlOptions := k8s.NewKubectlOptions("", "")

	// Setup a unique namespace to ensure reuse of resource configs on a single cluster.
	// Note that namespaces must be lowercase.
	namespaceName := fmt.Sprintf(
		"%s-%s",
		strings.ToLower(testName),
		strings.ToLower(random.UniqueId()),
	)

	k8s.CreateNamespace(t, kubectlOptions, namespaceName)
	// Set the namespace in the options
	kubectlOptions.Namespace = namespaceName
	// Delete the namespace at the end of the test
	defer k8s.DeleteNamespace(t, kubectlOptions, namespaceName)

	// Setup the Helm args.
	options := &helm.Options{
		KubectlOptions: kubectlOptions,
		// SetValues:      EngineValues,
	}

	// Generate a unique release name to refer to after deployment.
	releaseName := fmt.Sprintf(
		"%s-%s",
		strings.ToLower(testName),
		strings.ToLower(random.UniqueId()),
	)
	// Delete the release at the end of the test
	defer helm.Delete(t, options, releaseName, true)

	// Deploy the chart
	helm.Install(t, options, helmChartPath, releaseName)

	// Open a tunnel to an available Pod using the Service
	serviceName := fmt.Sprintf("%s-anchore-engine-api", releaseName)
	tunnel := utils.CreateTunnelFromService(t, kubectlOptions, serviceName)
	defer tunnel.Close()
	tunnel.ForwardPort(t)
	endpoint := fmt.Sprintf("http://%s/v1", tunnel.Endpoint())

	verifyEngineAPIPod(t, kubectlOptions, endpoint)

	env := map[string]string{
		"ANCHORE_CLI_URL":  endpoint,
		"ANCHORE_CLI_PASS": "foobar",
		"ANCHORE_CLI_USER": "admin",
	}

	engineServices := []string{"analyzer", "catalog", "apiext", "simplequeue", "policy_engine"}
	utils.VerifyEngineServiceStatus(t, engineServices, env)

	if !testing.Short() {
		cmd := shell.Command{
			Command: "tox",
			Args:    []string{"."},
			Env:     env,
		}

		output := shell.RunCommandAndGetOutput(t, cmd)
		utils.CreateFileFromString(output, "tox.log")
	}
}

// verifyEngineAPIPod will hit the endpoint to verify the api responds.
func verifyEngineAPIPod(t *testing.T, kubectlOptions *k8s.KubectlOptions, endpoint string) {
	retries := 60
	sleep := 10 * time.Second

	http_helper.HttpGetWithRetryWithCustomValidation(
		t,
		endpoint,
		retries,
		sleep,
		func(statusCode int, body string) bool {
			return statusCode == 200 && strings.Contains(body, "v1")
		},
	)
}
