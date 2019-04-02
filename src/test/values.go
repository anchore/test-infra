package test

import "github.com/anchore/test-infra/src/utils"

// EngineValues contains values for a base anchore engine install.
var EngineValues = map[string]string{
	"anchoreGlobal.imageName": utils.EngineImgTag,
}
