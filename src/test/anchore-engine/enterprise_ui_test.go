package test

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/anchore/test-infra/src/utils"
	"github.com/gruntwork-io/terratest/modules/helm"
	http_helper "github.com/gruntwork-io/terratest/modules/http-helper"
	"github.com/gruntwork-io/terratest/modules/k8s"
	"github.com/gruntwork-io/terratest/modules/logger"
	"github.com/gruntwork-io/terratest/modules/random"
)

func TestChartDeploysEnterprise(t *testing.T) {
	// Path to the helm chart we will test
	helmChartPath := "stable/anchore-engine"
	// helmChartPath, err := filepath.Abs("../../stable/anchore-engine")
	// logger.Log(t, err)
	// require.NoError(t, err)

	kubectlOptions := k8s.NewKubectlOptions("", "")

	// To ensure we can reuse the resource config on the same cluster to test different scenarios, we setup a unique
	// namespace for the resources for this test.
	// Note that namespaces must be lowercase.
	namespaceName := fmt.Sprintf("test-ui-%s", strings.ToLower(random.UniqueId()))
	k8s.CreateNamespace(t, kubectlOptions, namespaceName)
	// Make sure we set the namespace on the options
	kubectlOptions.Namespace = namespaceName
	// ... and make sure to delete the namespace at the end of the test
	defer k8s.DeleteNamespace(t, kubectlOptions, namespaceName)

	// Setup the args. For this test, we will set the following input values:
	// - anchoreEnterpriseGlobal.enabled=true
	options := &helm.Options{
		KubectlOptions: kubectlOptions,
		SetValues: map[string]string{
			"anchoreEnterpriseGlobal.enabled": "true",
		},
	}

	// We generate a unique release name so that we can refer to after deployment.
	// By doing so, we can schedule the delete call here so that at the end of the test, we run
	// `helm delete RELEASE_NAME` to clean up any resources that were created.
	releaseName := fmt.Sprintf(
		"test-ui-%s",
		strings.ToLower(random.UniqueId()),
	)
	defer helm.Delete(t, options, releaseName, true)

	// Deploy the chart using `helm install`. Note that we use the version without `E`, since we want to assert the
	// install succeeds without any errors.
	helm.Install(t, options, helmChartPath, releaseName)

	// Now that the chart is deployed, verify the deployment. This function will open a tunnel to the Pod and hit the
	// enterprise ui container endpoint.
	serviceName := fmt.Sprintf("%s-anchore-engine-enterprise-ui", releaseName)
	verifyEnterpriseUIPod(t, kubectlOptions, serviceName)
}

// verifyEnterpriseUIPod will open a tunnel to the Pod and hit the endpoint to verify the nginx welcome page is shown.
func verifyEnterpriseUIPod(t *testing.T, kubectlOptions *k8s.KubectlOptions, serviceName string) {
	// Wait for the pod to come up. It takes some time for the Pod to start, so retry a few times.
	retries := 30
	sleep := 10 * time.Second
	k8s.WaitUntilServiceAvailable(t, kubectlOptions, serviceName, retries, sleep)

	// We will first open a tunnel to the pod, making sure to close it at the end of the test.
	tunnel := k8s.NewTunnel(kubectlOptions, k8s.ResourceTypeService, serviceName, 0, 80)
	defer tunnel.Close()

	podName, _ := utils.GetAttachablePodForService(t, kubectlOptions, serviceName)
	logger.Logf(t, "Pod: %s", podName)
	k8s.WaitUntilPodAvailable(t, kubectlOptions, podName, retries, sleep)
	tunnel.ForwardPort(t)

	// ... and now that we have the tunnel, we will verify that we get back a 200 OK with the nginx welcome page.
	// It takes some time for the Pod to start, so retry a few times.
	endpoint := fmt.Sprintf("http://%s", tunnel.Endpoint())
	http_helper.HttpGetWithRetryWithCustomValidation(
		t,
		endpoint,
		retries,
		sleep,
		func(statusCode int, body string) bool {
			return statusCode == 200 && strings.Contains(body, "anchore")
		},
	)
}
