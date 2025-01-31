FROM python:3.12-alpine AS prepare

RUN apk update

RUN apk add --no-cache unzip wget

# pascal
# RUN apk add --no-cache mono mono-devel
RUN echo "@testing http://dl-4.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
    && apk add --update mono@testing mono-dev@testing \
    && rm -rf /var/cache/apk/*
# c++
RUN apk add --no-cache gcc g++
# java
RUN apk add --no-cache openjdk11-jdk openjdk11-jre
# pypy
RUN apk add --no-cache pypy3@testing
# lua
RUN apk add --no-cache lua5.3
# cobol
# RUN apk add --no-cache gnucobol
# haskell
RUN apk add --no-cache ghc ghc-doc
# fortran
RUN apk add --no-cache gfortran
# rust
RUN apk add --no-cache rust


WORKDIR /pascal
RUN wget "http://pascalabc.net/downloads/PascalABCNETLinux.zip" && \
  unzip "PascalABCNETLinux.zip" "PascalABCNETLinux/*" && \
  echo '#! /bin/sh' >> /bin/pabcnetc && \
  echo 'mono /pascal/PascalABCNETLinux/pabcnetcclear.exe $1' >> /bin/pabcnetc && \
  chmod u+x /bin/pabcnetc && \
  rm PascalABCNETLinux.zip

WORKDIR /node
RUN wget "https://nodejs.org/dist/v18.16.1/node-v18.16.1-linux-x64.tar.xz" && \
  tar -xf node-v18.16.1-linux-x64.tar.xz && \
  mv node-v18.16.1-linux-x64/bin/node /bin/node && \
  rm node-v18.16.1-linux-x64.tar.xz


WORKDIR /go
RUN wget "https://go.dev/dl/go1.23.4.linux-amd64.tar.gz" -O go.tar.gz && \
  tar -C /usr/local -xzf go.tar.gz && \
  rm go.tar.gz
ENV PATH="$PATH:/usr/local/go/bin"

RUN apk add --no-cache librdkafka-dev

FROM prepare AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable


FROM builder AS runner

ADD . /app/
WORKDIR /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

CMD ["uv", "run", "main.py"]
