#!/usr/bin/env python

default_admin_user = "admin"

default_admin_pass = "foobar"

default_system_wait_timeout = 300
default_system_wait_interval = 10

api_url = "http://localhost:8228/v1"

test_images = [
    "docker.io/alpine:3.10",
    "docker.io/alpine:latest",
    "docker.io/amazonlinux:latest",
    "docker.io/debian:10",
    "docker.io/nginx:latest",
    "docker.io/node:latest",
    "docker.io/oraclelinux:7",
    "docker.io/ubuntu:latest"
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
