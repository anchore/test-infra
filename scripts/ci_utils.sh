#!/bin/bash

# Utility functions used in all projects for CI build/testing.

RELEASE_ARTIFACTS=( "anchore-engine" "anchore-cli" "enterprise" "anchore-on-prem-ui" )
CIRCLE_BASE_URL:="https://circleci.com/api/v1.1/project/github"
echo ${CIRCLE_BRANCH:=master}

gather_artifacts() {
    local circleRunRepo=$1
    touch artifacts.txt
    for projectRepo in ${RELEASE_ARTIFACTS[@]}; do
        unset commitSHA tempVar
        local commitSHA
        local tempVar
        tempVar="${projectRepo//-/_}_SHA"
        set -ex
        if [[ "$projectRepo" != "$circleRunRepo" ]]; then
            commitSHA=$({ git ls-remote --exit-code git@github.com:anchore/${projectRepo} "refs/heads/${CIRCLE_BRANCH:-master}" || git ls-remote git@github.com:anchore/${projectRepo} refs/heads/master; } | awk '{ print $1 }')
            echo "export $tempVar=$commitSHA" | tee -a artifacts.txt
        elif [[ "$projectRepo" = "$circleRunRepo" ]]; then
            echo "export $tempVar=$CIRCLE_SHA1" | tee -a artifacts.txt
        fi
    done
}

trigger_artifact_build() {
    local circleRunRepo=$1
    if [[ ! -f artifacts.txt ]]; then
        gather_artifacts $circleRunRepo
    fi
    source artifacts.txt
    set -eux
    curl --user ${CIRCLE_API_TOKEN}: \
         --data build_parameters[CIRCLE_JOB]=build \
         --data build_parameters[anchore_engine_SHA]=${anchore_engine_SHA} \
         --data build_parameters[anchore_cli_SHA]=${anchore_cli_SHA} \
         --data build_parameters[enterprise_SHA]=${enterprise_SHA} \
         --data build_parameters[anchore_on_prem_ui_SHA]=${anchore_on_prem_ui_SHA} \
    ${CIRCLE_BASE_URL}/anchore/release-candidates/tree/${CIRCLE_BRANCH}
}

get_running_jobs() {
  local circleApiResponse
  local runningJobs

  circleApiResponse=$(curl --silent --show-error --user ${CIRCLE_API_TOKEN} "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}/tree/${CIRCLE_BRANCH}" -H "Accept: application/json")
  runningJobs=$(echo "$circleApiResponse" | jq "map(if .status == \"running\" and .vcs_revision != \"${CIRCLE_SHA1}\" then .build_num else \"None\" end) - [\"None\"] | .[]")
  echo "$runningJobs"
}

cancel_running_jobs() {
  local runningJobs
  runningJobs=$(get_running_jobs)
  for buildNum in $runningJobs;
  do
    echo Canceling "$buildNum"
    curl --silent --show-error -X POST --user ${CIRCLE_API_TOKEN} "${CIRCLE_BASE_URL}/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}/${buildNum}/cancel" >/dev/null
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

setup_and_print_env_vars() {
    # Export & print all project env vars to the screen
    echo "${color_yellow}"
    printf "%s\n\n" "- ENVIRONMENT VARIABLES SET -"
    echo "BUILD_VERSIONS=${BUILD_VERSIONS[@]}"
    printf "%s\n" "LATEST_VERSION=$LATEST_VERSION"
    for var in ${PROJECT_VARS[@]}; do
        export "$var"
        printf "%s" "${color_yellow}"
        printf "%s\n" "$var"
    done
    echo "${color_normal}"
    # If running tests manually, sleep for a few seconds to give time to visually double check that ENV is setup correctly
    if [[ "$CI" == false ]]; then
        sleep 5
    fi
    # Setup a variable for docker image cleanup at end of script
    declare -a DOCKER_RUN_IDS
    export DOCKER_RUN_IDS
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