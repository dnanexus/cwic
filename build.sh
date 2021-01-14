#!/bin/bash

set -eo pipefail

# This script builds the docker image defined by
# docker-compose.yml, ands the "latest" tag, and pushes both.

latest_tag=dnanexus/cwic-base:latest

docker-compose build
resp=$(docker-compose push --ignore-push-failures)
echo

# The response is something like:
# The push refers to repository [docker.io/dnanexus/cwic-base] 0.0.1: digest: sha256:fdde60 size: 3038
img=$(echo ${resp} | awk '{print $6":"$7}' | tr -d "[" | tr -d "]")
img=${img%:}

docker tag $img $latest_tag
docker push $latest_tag

