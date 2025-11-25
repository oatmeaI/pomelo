#! /bin/bash

compose_command="docker-compose"
if ! [ -x "$(command -v $compose_command)" ]; then
    compose_command="podman-compose"
fi

$compose_command -f docker-compose-dev.yml up --build
