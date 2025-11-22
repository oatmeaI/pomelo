#! /bin/bash
poetry install
poetry build
podman-compose up --build --build-arg CACHEBUST="$(date +%s)"
