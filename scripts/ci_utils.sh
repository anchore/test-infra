#!/bin/bash

set -euo pipefail

RELEASE_ARTIFACTS=( "anchore-engine" "anchore-cli" "enterprise" "anchore-on-prem-ui" )
CIRCLE_BASE_URL="https://circleci.com/api/v1.1/project/github"
GIT_BRANCH=${CIRCLE_BRANCH:=master}
PROJECT_REPONAME=${CIRCLE_PROJECT_REPONAME:=release-candidates}
COMMIT_SHA=${CIRCLE_SHA1:=master}
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
    curl --user ${CIRCLE_API_TOKEN}: \
         --data build_parameters[CIRCLE_JOB]=release \
         --data build_parameters[ARTIFACT_PROJECT_REPO]=${PROJECT_REPONAME} \
         --data build_parameters[ARTIFACT_COMMIT_SHA]=${COMMIT_SHA} \
    ${CIRCLE_BASE_URL}/anchore/release-candidates/tree/${GIT_BRANCH}
}

get_running_jobs() {
  local circleApiResponse
  local runningJobs
  circleApiResponse=$(curl --silent --show-error -H "Accept: application/json" --user "${CIRCLE_API_TOKEN}": "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${PROJECT_REPONAME}/tree/${GIT_BRANCH}")
  runningJobs=$(echo "$circleApiResponse" | jq "map(if .status == \"running\" and .vcs_revision != \"${COMMIT_SHA}\" then .build_num else \"None\" end) - [\"None\"] | .[]")
  echo "$runningJobs"
}

cancel_running_jobs() {
  local runningJobs
  runningJobs=$(get_running_jobs)
  echo "$runningJobs"
  for buildNum in $runningJobs; do
    echo "Canceling $buildNum"
    curl --silent --show-error -X POST --user "${CIRCLE_API_TOKEN}": "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${PROJECT_REPONAME}/${buildNum}/cancel" >/dev/null
  done
}

is_running_jobs() {
    local runningJobs
    runningJobs=$(get_running_jobs)
    if [[ -z "$runningJobs" ]]; then
        echo 'false'
    else
        echo 'true'
    fi
}

wait_running_jobs() {
    local -i timeout=${1:-600}
    local -i timer=0
    while $(is_running_jobs); do
        if [[ "$(($timer * 10))" -ge "$timeout" ]]; then
            echo "timed out waiting for jobs to finish"
            exit 1
        else
            echo "waiting for job to finish - ${PROJECT_REPONAME} build# $(get_running_jobs)"
            sleep 10
        fi
        timer+=1
    done
}

ci_test_job() {
    local ci_image=$1
    local ci_function=$2
    local docker_name="${RANDOM:-TEMP}-ci-test"
    docker run --net host -it --name "$docker_name" -v $(dirname "$WORKING_DIRECTORY"):$(dirname "$WORKING_DIRECTORY") -v /var/run/docker.sock:/var/run/docker.sock "$ci_image" /bin/sh -c "\
        cd ${WORKING_DIRECTORY} && \
        cp scripts/build.sh /tmp/build.sh && \
        export WORKING_DIRECTORY=${WORKING_DIRECTORY} && \
        sudo -E bash /tmp/build.sh $ci_function \
    "
    docker stop "$docker_name" && docker rm "$docker_name"
    local docker_id=$(docker inspect $docker_name | jq '.[].Id')
    DOCKER_RUN_IDS+=("$docker_id")
}

load_image() {
    local anchore_version="$1"
    docker load -i "${WORKSPACE}/caches/${PROJECT_REPONAME}-${anchore_version}-dev.tar"
}

push_dockerhub() {
    local anchore_version="$1"
    if [[ "$CI" == true ]]; then
        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
    fi
    if [[ "$GIT_BRANCH" == 'master' ]] && [[ "$CI" == true ]] && [[ ! "$anchore_version" == 'dev' ]]; then
        docker tag "${IMAGE_REPO}:dev-${anchore_version}" "${IMAGE_REPO}:${anchore_version}"
        echo "Pushing to DockerHub - ${IMAGE_REPO}:${anchore_version}"
        docker push "${IMAGE_REPO}:${anchore_version}"
        if [ "$anchore_version" == "$LATEST_VERSION" ]; then
            docker tag "${IMAGE_REPO}:dev-${anchore_version}" "${IMAGE_REPO}:latest"
            echo "Pushing to DockerHub - ${IMAGE_REPO}:latest"
            docker push "${IMAGE_REPO}:latest"
        fi
    else
        docker tag "${IMAGE_REPO}:dev-${anchore_version}" "anchore/private_testing:${PROJECT_REPONAME}-${anchore_version}"
        echo "Pushing to DockerHub - anchore/private_testing:${PROJECT_REPONAME}-${anchore_version}"
        if [[ "$CI" == false ]]; then
            sleep 10
        fi
        docker push "anchore/private_testing:${PROJECT_REPONAME}-${anchore_version}"
    fi
}

save_image() {
    local anchore_version="$1"
    mkdir -p "${WORKSPACE}/caches"
    docker save -o "${WORKSPACE}/caches/${PROJECT_REPONAME}-${anchore_version}-dev.tar" "${IMAGE_REPO}:dev-${anchore_version}"
}


setup_build_environment() {
    # Copy source code to $WORKING_DIRECTORY for mounting to docker volume as working dir
    if [[ ! -d "$WORKING_DIRECTORY" ]]; then
        mkdir -p "$WORKING_DIRECTORY"
        cp -a . "$WORKING_DIRECTORY"
    fi
    mkdir -p "${WORKSPACE}/caches"
    pushd "$WORKING_DIRECTORY"
    install_dependencies || true
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