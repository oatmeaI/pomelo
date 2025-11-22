#! /bin/bash
poetry install
poetry build
podman build . -t pomelo
podman image tag pomelo oatmeal/pomelo:latest
