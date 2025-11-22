#! /bin/bash

docker_command="docker"
if ! [ -x "$(command -v $docker_command)" ]; then
    docker_command="podman"
fi

poetry install
poetry build
$docker_command build . -t pomelo
$docker_command image tag pomelo oatmeal/pomelo:latest
