package utils

import (
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/k8s"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/kubernetes/pkg/kubectl/generate"
)

// GetAttachablePodForService finds an active pod associated with the Service and return the pod name.
func GetAttachablePodForService(t *testing.T, kubectlOptions *k8s.KubectlOptions, resourceName string) (string, error) {
	service, err := k8s.GetServiceE(t, kubectlOptions, resourceName)
	if err != nil {
		t.Fatal(err)
	}
	selectorLabelsOfPods := generate.MakeLabels(service.Spec.Selector)
	servicePods, err := k8s.ListPodsE(t, kubectlOptions, metav1.ListOptions{LabelSelector: selectorLabelsOfPods})
	if err != nil {
		t.Fatal(err)
	}
	for _, pod := range servicePods {
		return pod.Name, nil
	}
	return "", nil
}

// CreateTunnelFromService creates a k8s tunnel to the first availabe pod attached to the specified service.
func CreateTunnelFromService(t *testing.T, kubectlOptions *k8s.KubectlOptions, serviceName string) *k8s.Tunnel {
	// Wait for the pod to come up. It takes some time for the Pod to start, so retry a few times.
	retries := 30
	sleep := 10 * time.Second
	k8s.WaitUntilServiceAvailable(t, kubectlOptions, serviceName, retries, sleep)

	// Open a tunnel to the pod, make sure to close it at the end of the test.
	tunnel := k8s.NewTunnel(kubectlOptions, k8s.ResourceTypeService, serviceName, 0, 8228)

	podName, _ := GetAttachablePodForService(t, kubectlOptions, serviceName)
	k8s.WaitUntilPodAvailable(t, kubectlOptions, podName, retries, sleep)

	return tunnel
}

func CreateEnterpriseSecrets(t *testing.T, kubectlOptions *k8s.KubectlOptions) {

}
