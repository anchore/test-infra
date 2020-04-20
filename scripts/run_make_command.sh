#!/usr/bin/env bash

# Fail on any errors, including in pipelines and when variables are missing
set -euo pipefail

display_usage() {
    cat << EOF
    This script is intended to be invoked from the root project Makefile, it is a simple wrapper
    for calling pipeline task functions found in the following tasks libraries:

        /anchore-ci/make/common_tasks
        /anchore-ci/make/pipeline_tasks

    This script handles UX, sourcing tasks libraries, displaying usage, and verbose output

        usage: $0 < task_name >
EOF
}

display_make_usage() {
    printf "\nUse make from the project root directory to invoke pipeline tasks\n"
    print_colorized WARN "usage: make < task_name >"
}

# source all CI commands & utility functions
for f in /anchore-ci/lib/*; do
  source "$f"
done

if [[ "${CI:-false}" == "false" ]]; then
    # Allow mounting & using docker socket with circleci user when running container locally
    sudo chown root:docker /var/run/docker.sock
    sudo chmod 770 /var/run/docker.sock
    cd "${WORKING_DIRECTORY}"
fi

setup_colors

# Check for valid input arguments
if [[ "$#" -eq 0 ]]; then
    print_colorized ERROR "ERROR - script requires input" >&2
    display_usage
    exit 1

elif [[ "$1" =~ (help|-h) ]]; then
    display_make_usage
    exit
fi

# VERBOSE will trap all bash commands & print to screen, like using set -v but allows printing in color
if [[ "${VERBOSE:-false}" =~ (true|TRUE|y|Y|1) ]]; then
    set -o functrace
    trap 'printf "%s${INFO}+ $BASH_COMMAND${NORMAL}\n" >&2' DEBUG
fi

# Check if the first argument is a function or executable script
if declare -f "$1" &> /dev/null; then
    # run the task function/script with all arguments passed to it
    "$@"

elif [[ -x "$1" ]] && [[ "$1" =~ ".sh" ]]; then
    source "$@"

else
    "$@"
fi