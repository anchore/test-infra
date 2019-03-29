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
)

// VerifyEngineServiceStatus runs anchore-cli and checks that all services are in the up state.
func VerifyEngineServiceStatus(t *testing.T, services []string, env map[string]string) {
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
