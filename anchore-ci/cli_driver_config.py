#!/usr/bin/env python

default_admin_user = "admin"

default_admin_pass = "foobar"

default_system_wait_timeout = 300
default_system_wait_interval = 10

api_url = "http://localhost:8228/v1"

cmd_prefix = "anchore-cli --json "

cli_command_prefix = "kubectl exec anchore-cli -- "

repositories = [
    "docker.io/hello-world",         # 8 tags
    "docker.io/ndslabs/nagios-nrpe", # 6 tags
    "docker.io/mborges/fortran"      # 1 tag
]

test_images = [
    "docker.io/alpine:latest",
    "docker.io/amazonlinux:latest",
    "docker.io/debian:10",
    "docker.io/nginx:latest",
    "docker.io/ubuntu:latest"
]

malware_images = [
    "docker.io/anchore/test_images:alpine_malware_test"
]

clean_images = [
    "docker.io/anchore/test_images:alpine_clean"
]

metadata_types = [
    "manifest",
    "docker_history",
    "dockerfile"
]

vulnerability_types = [
    "os",
    "non-os",
    "all"
]

content_types = [
    "os",
    "files",
    "npm",
    "gem",
    "python",
    "java",
    "binary",
    "go",
    "malware",
    "nuget"
]
