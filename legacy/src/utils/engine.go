package utils

import (
	"fmt"
	"regexp"
	"strings"
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/logger"
	"github.com/gruntwork-io/terratest/modules/retry"
	"github.com/gruntwork-io/terratest/modules/shell"

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

// VerifyEngineSystemStatus uses the anchore-cli to check that all services are up.
func VerifyEngineSystemStatus(t *testing.T, services []string, env map[string]string) {
	cmd := shell.Command{
		Command: "anchore-cli",
		Args:    []string{"system", "status"},
		Env:     env,
	}

	retries := 60
	sleep := 10 * time.Second
	statusMsg := "Verify Anchore Engine Status."

	_, err := retry.DoWithRetryE(
		t,
		statusMsg,
		retries,
		sleep,
		func() (string, error) {
			output, err := shell.RunCommandAndGetOutputE(t, cmd)
			logger.Log(t, fmt.Sprintf("\n%s", output))
			if err != nil {
				return "", err
			}
			for _, s := range services {
				re := regexp.MustCompile(fmt.Sprintf(".*(%s)+.*[:].*(up)", s))
				if !re.MatchString(output) {
					return "", fmt.Errorf("service: %s is not ready", s)
				} else if strings.Contains(output, "down") {
					t.Fatal("Anchore Engine services reported down status")
				}
			}
			return output, nil
		},
	)
	if err != nil {
		t.Fatal(t, "Timed out waiting for Anchore Engine to come up")
	}
}
