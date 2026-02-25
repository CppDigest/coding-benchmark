# Defects4C evaluation environment (Child Issue 2).
# Build: docker build -t defects4c-env .
# Run:   docker run --rm -it -v "$(pwd)/../repos:/repos" defects4c-env bash
# Then:  python /app/scripts/checkout_bug.py --bug-id PROJECT@SHA --work-dir /repos
#       python /app/evaluation/run_tests.py --bug-id PROJECT@SHA --work-dir /repos

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    make \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir requests

# App layout: /app = defects4c wrapper (scripts, data, evaluation)
# Build from repo root: docker build -f external/defects4c/docker/Dockerfile external/defects4c
WORKDIR /app
COPY scripts /app/scripts/
COPY data /app/data/
COPY evaluation /app/evaluation/

# Default work dir for cloned repos (mount at run time)
ENV DEFECTS4C_WORK_DIR=/repos
RUN mkdir -p "$DEFECTS4C_WORK_DIR"

WORKDIR /app
CMD ["bash"]
