# Anchore Test Infrastructure

Tests are built in go using the TerraTest library and the standard go test library. Used for preparing & managing Anchore Helm deployments for running functional and e2e tests. 

A docker image is the final artifact for running the test suite in CI. Image can be build using the build.sh script.

## Build binary
Binary is built directly in the current working directory. It will be named after the directory it was run in, or the package specified. Using these instructions, you'll get a binary called `anchore-engine.test`.

Package dependencies can be installed with the dep manager. To get dep run `go get -u github.com/golang/dep/cmd/dep`.

```bash
dep ensure
cd src/test/anchore-engine
go test -c .
```

### Build binary for different architecture
To compile a binary for Linux on a macos system, use the following command
```bash
dep ensure
cd src/test/anchore-engine
GOOS=linux GOARCH=amd64 go test -c .
```

## Running tests
Go test can be used to test both the Enterprise & Anchore Engine deployments. After Helm chart is deployed, `tox` is called in the working directory to run python tests within testing Environment. A log of the `tox` tests will be created in the current working directory.

`tox` tests can be skipped (for testing just the helm chart) by using the `-short` option when calling `go test`

### Setup environment
Must have kubectl, helm & anchore-cli installed on the system running tests.

Test will run against a k8s cluster that is configured, using your configuration file at ~/.kube/config

### Run all tests
Using source code
```go
cd src/test/anchore-engine
go test -v . -engineImgTag=dev
```

Using binary
```
./anchore-engine.test -v
```



### Run only Anchore Engine tests
Using source code
```go
go test -run ChartDeploysEngine -engineImgTag=dev
```

Using binary
```
./anchore-engine.test -test.run ChartDeploysEngine -engineImgTag=dev
```

### Run only Anchore Enterprise tests
```go 
go test -run ChartDelpoysEnterprise
```