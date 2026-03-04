# Sandbox for safe C++ compilation and execution (HumanEval/MultiPL-E style).
# Run with: docker run --rm --network none -v $(pwd):/workspace:ro -i multiple-humaneval-sandbox:latest
# Runs as non-root user so untrusted C++ is not executed as root.
FROM gcc:12-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*

# Dedicated non-root user (fixed UID/GID for reproducible permissions)
RUN addgroup --gid 1000 sandbox && adduser --disabled-password --gecos "" --uid 1000 --gid 1000 sandbox

WORKDIR /workspace
COPY execute.py /workspace/execute.py
RUN chown -R sandbox:sandbox /workspace

ENV HOME=/home/sandbox
ENV TMPDIR=/tmp

USER sandbox
ENTRYPOINT ["python3", "/workspace/execute.py"]
