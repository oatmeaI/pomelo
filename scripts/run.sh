#! /bin/bash

compose_command="docker-compose"
if ! [ -x "$(command -v $compose_command)" ]; then
    compose_command="podman-compose"
fi

poetry install
poetry build
$compose_command up --build
