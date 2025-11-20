# FROM python:3.14
FROM ghcr.io/linuxserver/baseimage-ubuntu:noble
COPY ../pomelo pomelo
WORKDIR pomelo
RUN apt update
RUN apt --assume-yes install python3 pipx python-is-python3 caddy
ENV PATH="$PATH:/root/.local/bin"
RUN pipx install poetry
RUN pipx ensurepath
RUN poetry config virtualenvs.in-project true
RUN poetry config installer.max-workers 10
RUN chmod +x entrypoint.sh
CMD bash ./entrypoint.sh
