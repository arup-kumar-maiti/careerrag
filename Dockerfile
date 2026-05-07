FROM python:3.11-slim

WORKDIR /app

COPY . .

ARG VERSION=0
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} pip install --no-cache-dir .
