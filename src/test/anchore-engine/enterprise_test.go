package test

import (
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/helm"
	"github.com/gruntwork-io/terratest/modules/k8s"
	"github.com/gruntwork-io/terratest/modules/random"
	"github.com/gruntwork-io/terratest/modules/shell"

	"github.com/anchore/test-infra/src/test"
	"github.com/anchore/test-infra/src/utils"
)

func TestChartDeploysEnterprise(t *testing.T) {
	testName := "test-ent"

	// Path to the helm chart to test, or name from official stable repo
	helmChartPath := utils.EngineChartPath
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

	// Copy imagepullsecret from default namespace to new namespace
	imgPullSecretConfig, err := k8s.RunKubectlAndGetOutputE(t, kubectlOptions, "get", "secret", "anchore-enterprise-pullcreds", "--namespace=default", "--export", "-o", "yaml")
	if err != nil {
		t.Fatal(err)
	}
	pullSecretFileName := "pullsecret.yaml"
	utils.CreateFileFromString(imgPullSecretConfig, pullSecretFileName)
	defer os.Remove(pullSecretFileName)
	k8s.RunKubectl(t, kubectlOptions, "apply", "-f", pullSecretFileName, "--namespace", namespaceName)

	// Add imagepullsecret to the namespace default service account
	k8s.RunKubectl(t, kubectlOptions, "patch", "sa", "default", "--namespace", namespaceName, "-p", "\"imagePullSecrets\": [{\"name\": \"anchore-enterprise-pullcreds\"}]")

	// Copy enterprise license from default namespace to new namespace
	licenseSecretFileName := "license_secret.yaml"
	licenseSecretConfig, err := k8s.RunKubectlAndGetOutputE(t, kubectlOptions, "get", "secret", "anchore-enterprise-license", "--namespace=default", "--export", "-o", "yaml")
	if err != nil {
		t.Fatal(err)
	}
	utils.CreateFileFromString(licenseSecretConfig, licenseSecretFileName)
	defer os.Remove(licenseSecretFileName)
	k8s.RunKubectl(t, kubectlOptions, "apply", "-f", licenseSecretFileName, "--namespace", namespaceName)

	// Setup the Helm args.
	options := &helm.Options{
		KubectlOptions: kubectlOptions,
		SetValues:      test.EnterpriseValues,
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

	// TODO
	//
	// consider using serviceName : port & creating service names with vars (for testing service ports)
	//
	serviceNames := map[string]string{
		"api":           fmt.Sprintf("%s-anchore-engine-api", releaseName),
		"catalog":       fmt.Sprintf("%s-anchore-engine-catalog", releaseName),
		"policy-engine": fmt.Sprintf("%s-anchore-engine-policy", releaseName),
		"simplequeue":   fmt.Sprintf("%s-anchore-engine-simplequeue", releaseName),
	}

	retries := 60
	sleep := 10 * time.Second
	for _, s := range serviceNames {
		k8s.WaitUntilServiceAvailable(t, kubectlOptions, s, retries, sleep)
		if strings.Contains(s, "api") {
			utils.VerifyEngineServiceStatus(t, kubectlOptions, s)
		}
	}

	//
	// TODO
	//
	// Add a call to anchore-cli system status

	// If the -short option isn't passed to the test, run tox tests & save output to log file.
	if !testing.Short() {
		tunnel := utils.CreateTunnelFromService(t, kubectlOptions, serviceNames["api"])
		defer tunnel.Close()
		tunnel.ForwardPort(t)
		apiEndpoint := fmt.Sprintf("http://%s/v1", tunnel.Endpoint())

		env := map[string]string{
			"ANCHORE_CLI_URL":  apiEndpoint,
			"ANCHORE_CLI_PASS": "foobar",
			"ANCHORE_CLI_USER": "admin",
		}

		cmdTest := shell.Command{
			Command: "tox",
			Args:    []string{"--", "-s", "."},
			Env:     env,
		}

		output, err := shell.RunCommandAndGetOutputE(t, cmdTest)
		utils.CreateFileFromString(output, "enterprise_tests.log")
		fmt.Println(output)
		if err != nil {
			t.Fatalf("Tox tests failed with error: %s", err)
		}
	}
}
