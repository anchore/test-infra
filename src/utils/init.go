package utils

import "flag"

var EngineImageName string
var EnterpriseImageName string
var UIImageName string
var EngineChartPath string

func init() {
	flag.StringVar(&EngineImageName, "engineImg", "docker.io/anchore/anchore-engine:latest", "Anchore Engine image to test.")
	flag.StringVar(&EnterpriseImageName, "enterpriseImg", "docker.io/anchore/enterprise:latest", "Anchore Enterprise image to test.")
	flag.StringVar(&UIImageName, "uiImg", "docker.io/anchore/enterprise-ui:latest", "Anchore UI image to test.")
	flag.StringVar(&EngineChartPath, "engineChartPath", "stable/anchore-engine", "Path of Helm chart for Anchore Engine (defaults to stable/anchore-engine).")
	flag.Parse()
}
