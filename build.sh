#!/bin/bash

set -xeo pipefail


cleanup() {
    ret="$?"
    set +e
    rm -f anchore-engine.test
    exit "$ret"
}

trap 'cleanup' EXIT SIGINT SIGTERM ERR

dep ensure
pushd src/test/anchore-engine
GOOS=linux GOARCH=amd64 go test -c .
popd
mv src/test/anchore-engine/anchore-engine.test ./
docker build -t 'docker.io/anchore/test-infra:dev' .