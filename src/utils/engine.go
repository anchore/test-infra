package utils

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/logger"

	http_helper "github.com/gruntwork-io/terratest/modules/http-helper"
	"github.com/gruntwork-io/terratest/modules/k8s"
)

// VerifyEngineServiceStatus runs anchore-cli and checks that all services are in the up state.
func VerifyEngineServiceStatus(t *testing.T, kubectlOptions *k8s.KubectlOptions, serviceName string) {
	tunnel := CreateTunnelFromService(t, kubectlOptions, serviceName)
	defer tunnel.Close()
	tunnel.ForwardPort(t)
	endpoint := fmt.Sprintf("http://%s", tunnel.Endpoint())
	if strings.Contains(serviceName, "api") {
		verifyEngineAPIPod(t, kubectlOptions, endpoint)
		// } else {
		// verifyEngineServicePod(t, kubectlOptions, endpoint)
	}
}

// verifyEngineAPIPod will hit the health endpoint to verify the service responds.
func verifyEngineAPIPod(t *testing.T, kubectlOptions *k8s.KubectlOptions, baseURL string) {
	retries := 60
	sleep := 10 * time.Second
	endpoint := fmt.Sprintf("%s/v1/", baseURL)
	logger.Logf(t, "Checking URL - %s", endpoint)
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

// verifyEngineServicePod will hit the health endpoint to verify the service responds.
func verifyEngineServicePod(t *testing.T, kubectlOptions *k8s.KubectlOptions, baseURL string) {
	retries := 60
	sleep := 10 * time.Second
	endpoint := fmt.Sprintf("%s/health", baseURL)
	logger.Logf(t, "Checking URL - %s", endpoint)
	http_helper.HttpGetWithRetryWithCustomValidation(
		t,
		endpoint,
		retries,
		sleep,
		func(statusCode int, body string) bool {
			return statusCode == 200
		},
	)
}
