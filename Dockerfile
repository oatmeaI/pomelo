FROM python:latest

RUN apt update
RUN apt --assume-yes install caddy

RUN echo "$(date +%s)" # bust cache

COPY ./dist /dist
RUN pip install /dist/pomelo-0.1.0-py3-none-any.whl

CMD caddy start ; pomelo
