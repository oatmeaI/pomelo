#! /bin/bash

docker_command="docker"
if ! [ -x "$(command -v $docker_command)" ]; then
    docker_command="podman"
fi

poetry install
poetry lock
poetry build
$docker_command build . -t oatmealmonster/pomelo --no-cache
$docker_command image tag pomelo oatmealmonster/pomelo:latest
$docker_command push oatmealmonster/pomelo:latest
