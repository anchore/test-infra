#!/bin/bash

pushd src/test/anchore-engine
go test -c .
popd