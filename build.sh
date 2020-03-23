#!/bin/bash

docker-compose build
docker push dnanexus/cwic-base:latest
