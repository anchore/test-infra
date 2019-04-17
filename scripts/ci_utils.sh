#!/bin/bash

# Utility functions used in all projects for CI build/testing.

export release_artifacts=( "anchore-engine" "anchore-cli" "enterprise" "anchore-on-prem-ui" )

# function push_dockerhub {

# }

# function docker_build {

# }

function gather_artifacts {
    declare circle_run_repo=$1    
    for i in ${release_artifacts[@]}; do
        unset COMMIT_SHA VAR
        declare COMMIT_SHA
        declare VAR
        VAR="${i//-/_}_SHA"
        set -ex
        touch artifacts.txt
        if [[ "$i" != "$circle_run_repo" ]]; then
            COMMIT_SHA=$(git ls-remote git@github.com:anchore/${i} "refs/heads/${CIRCLE_BRANCH:-master}" | awk '{ print $1 }')
            echo "export $VAR=$COMMIT_SHA" | tee -a artifacts.txt
        elif [[ "$i" = "$circle_run_repo" ]]; then
            echo "export $VAR=$CIRCLE_SHA1" | tee -a artifacts.txt
        fi
    done
    source artifacts.txt
}

function trigger_artifact_build {
    declare circle_run_repo=$1
    if [[ ! -f artifacts.txt ]]; then
        gather_artifacts $circle_run_repo
    fi
    source artifacts.txt
    set -eux
    curl --user ${CIRCLE_API_TOKEN}: \
         --data build_parameters[CIRCLE_JOB]=build \
         --data build_parameters[anchore_engine_SHA]=${anchore_engine_SHA} \
         --data build_parameters[anchore_cli_SHA]=${anchore_cli_SHA} \
         --data build_parameters[enterprise_SHA]=${enterprise_SHA} \
         --data build_parameters[anchore_on_prem_ui_SHA]=${anchore_on_prem_ui_SHA} \
    https://circleci.com/api/v1.1/project/github/anchore/release-candidates/tree/${CIRCLE_BRANCH}
}