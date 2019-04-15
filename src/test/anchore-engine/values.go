package test

import (
	"github.com/anchore/test-infra/src/utils"
)

// EngineValues contains values for a base anchore engine install.
var EngineValues = map[string]string{
	"anchoreGlobal.image":                     utils.EngineImageName,
	"anchoreGlobal.imagePullPolicy":           "Always",
	"anchoreGlobal.serviceDir":                "/config",
	"anchoreAnalyzer.scratchVolume.mountPath": "/tmp",
}

// EnterpriseValues contains values for a base anchore engine install.
var EnterpriseValues = map[string]string{
	"anchoreGlobal.image":                     utils.EngineImageName,
	"anchoreGlobal.imagePullPolicy":           "Always",
	"anchoreEnterpriseGlobal.enabled":         "True",
	"anchoreEnterpriseGlobal.image":           utils.EnterpriseImageName,
	"anchoreEnterpriseGlobal.imagePullPolicy": "Always",
	"anchoreEnterpriseUi.image":               utils.UIImageName,
	"anchoreEnterpriseUi.imagePullPolicy":     "Always",
	"anchoreGlobal.serviceDir":                "/config",
	"anchoreAnalyzer.scratchVolume.mountPath": "/tmp",
}
