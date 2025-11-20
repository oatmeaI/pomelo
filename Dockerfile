FROM ghcr.io/linuxserver/baseimage-ubuntu:noble
COPY ../pomelo pomelo
RUN apt update
RUN apt --assume-yes install python3 pipx python-is-python3 caddy
ENV PATH="$PATH:/root/.local/bin"
RUN pipx install poetry
RUN pipx ensurepath
RUN poetry config virtualenvs.in-project true
RUN poetry config installer.max-workers 10
RUN chmod +x /pomelo/entrypoint.sh
CMD bash /pomelo/entrypoint.sh
