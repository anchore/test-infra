#!/bin/bash

set -evuo pipefail

RELEASE_ARTIFACTS=( "anchore-engine" "anchore-cli" "enterprise" "anchore-on-prem-ui" )
CIRCLE_BASE_URL="https://circleci.com/api/v1.1/project/github"
GIT_BRANCH=${CIRCLE_BRANCH:=master}
PROJECT_REPONAME=${CIRCLE_PROJECT_REPONAME:=release-candidates}
COMMIT_SHA=${CIRCLE_SHA1:=$(git rev-parse HEAD)}
CIRCLE_PROJECT_USERNAME=${CIRCLE_PROJECT_USERNAME:=anchore}
CIRCLE_API_TOKEN=${CIRCLE_API_TOKEN:=test}

###################################################################
### Utility functions used in all projects for CI build/testing ###
###################################################################

gather_artifacts() {
    local circleRunRepo=$1
    touch artifacts.txt
    for projectRepo in ${RELEASE_ARTIFACTS[@]}; do
        unset commitSHA tempVar
        local commitSHA
        local tempVar
        tempVar="${projectRepo//-/_}_SHA"
        if [[ "$projectRepo" != "$circleRunRepo" ]]; then
            commitSHA=$({ git ls-remote --exit-code git@github.com:anchore/${projectRepo} "refs/heads/${GIT_BRANCH}" || git ls-remote git@github.com:anchore/${projectRepo} refs/heads/master; } | awk '{ print $1 }')
            echo "export $tempVar=$commitSHA" | tee -a artifacts.txt
        elif [[ "$projectRepo" = "$circleRunRepo" ]]; then
            echo "export $tempVar=$COMMIT_SHA" | tee -a artifacts.txt
        fi
    done
    source artifacts.txt
}

trigger_artifact_build() {
    wait_running_jobs release-candidates
    curl --user ${CIRCLE_API_TOKEN}: \
         --data build_parameters[CIRCLE_JOB]=release \
         --data build_parameters[ARTIFACT_PROJECT_REPO]=${PROJECT_REPONAME} \
         --data build_parameters[ARTIFACT_COMMIT_SHA]=${COMMIT_SHA} \
    ${CIRCLE_BASE_URL}/anchore/release-candidates/tree/${GIT_BRANCH}
}

get_running_jobs() {
  local circleApiResponse
  local runningJobs
  local repoName=${1:-$PROJECT_REPONAME}
  circleApiResponse=$(curl --silent --show-error -H "Accept: application/json" --user "${CIRCLE_API_TOKEN}": "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${repoName}/tree/${GIT_BRANCH}")
  runningJobs=$(echo "$circleApiResponse" | jq "map(if .status == \"running\" and .vcs_revision != \"${COMMIT_SHA}\" then .build_num else \"None\" end) - [\"None\"] | .[]")
  echo "$runningJobs"
}

cancel_running_jobs() {
  local runningJobs
  local repoName=${1:-$PROJECT_REPONAME}
  runningJobs=$(get_running_jobs $repoName)
  echo "$runningJobs"
  for buildNum in $runningJobs; do
    echo "Canceling $buildNum"
    curl --silent --show-error -X POST --user "${CIRCLE_API_TOKEN}": "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${repoName}/${buildNum}/cancel" >/dev/null
  done
}

is_running_jobs() {
    local runningJobs
    local repoName=${1:-$PROJECT_REPONAME}
    runningJobs=$(get_running_jobs $repoName)
    if [[ -z "$runningJobs" ]]; then
        echo 'false'
    else
        echo 'true'
    fi
}

wait_running_jobs() {
    local repoName=${1:-$PROJECT_REPONAME}
    local -i timeout=600
    local -i timer=0
    while $(is_running_jobs $repoName); do
        if [[ "$(($timer * 10))" -ge "$timeout" ]]; then
            echo "timed out waiting for jobs to finish"
            exit 1
        else
            echo "waiting for job to finish - ${repoName} build# $(get_running_jobs)"
            sleep 10
        fi
        timer+=1
    done
}

if [[ "$BASH_SOURCE" == "$0" ]]; then
    if declare -f "$1" > /dev/null; then
        "$@"
    else
        display_usage >&2
        printf "%sERROR - %s is not a valid function name %s\n" "$color_red" "$1" "$color_normal" >&2
        exit 1
    fi
fi