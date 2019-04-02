package utils

import "flag"

var EngineImgTag string
var EngineChartPath string

func init() {
	flag.StringVar(&EngineImgTag, "engineImgTag", "dev", "Anchore Engine container image tag to test.")
	flag.StringVar(&EngineChartPath, "engineChartPath", "stable/anchore-engine", "Path of Helm chart for Anchore Engine (defaults to stable/anchore-engine).")
	flag.Parse()
}
