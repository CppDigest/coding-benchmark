# Sandbox for safe C++ compilation and execution (HumanEval/MultiPL-E style).
# Run with: docker run --rm --network none -v $(pwd):/workspace:ro -i multiple-humaneval-sandbox:latest
FROM gcc:12-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY execute.py /workspace/execute.py
ENTRYPOINT ["python3", "/workspace/execute.py"]
