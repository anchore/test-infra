#!/usr/bin/env bash

# Fail on any errors, including in pipelines and when variables are missing
set -euo pipefail

display_usage() {
    cat << EOF
    This script is intended to be invoked as a docker-entrypoint script for the anchore/test-infra images. 
    It is a simple wrapper for invoking CI task scripts/binaries/functions inside the anchore/test-infra image.
    All available task libraries can be found in the following directory of the anchore/test-infra image:

        /anchore-ci/lib

    This script handles UX, sourcing libraries, displaying usage, and verbose output

        usage: $0 < task_name or script/binary >
EOF
}

display_make_usage() {
    printf '\n%s\n' "Use make from the project root directory to invoke pipeline tasks"
    print_colorized WARN "usage: make < target >"
}

# source all CI commands & utility functions
for f in /anchore-ci/lib/*; do
  source "$f"
done

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
if [[ "${VERBOSE:-false}" =~ (true|TRUE|y|Y|1|2) ]]; then
    set -o functrace
    trap 'command printf "%s${INFO}+ $BASH_COMMAND${NORMAL}\n" >&2' DEBUG
    if [[ "${VERBOSE:-false}" = "2" ]]; then
        set -x
    fi
fi

if [[ "${CI}" == "false" ]]; then
    # Allow mounting & using docker socket with circleci user when running container locally
    sudo chown root:docker /var/run/docker.sock
    sudo chmod 770 /var/run/docker.sock
    cd "${WORKING_DIRECTORY}"
fi

# Check if the first argument is a function or executable script
if [[ -x "$1" ]] && [[ "$1" =~ ".sh" ]]; then
    print_colorized WARN "Running script: $1"
    source "$@"

else
    print_colorized WARN "Running command: $@"
    "$@"
fi