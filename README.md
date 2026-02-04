# coding-benchmark

A small, focused repo for building **replayable, versioned benchmarks** that measure whether coding agents/LLMs can deliver **real C/C++ engineering outcomes**—not just “good-looking” answers.

## What this repository is for
- **Benchmark data**: cases sourced from real work (issues/PRs/CI failures) and/or carefully authored tasks, each **pinned to an exact commit**.
- **Objective scoring**: success is defined by **machine-checkable signals** (e.g., build/tests/linters) with **FAIL→PASS** and **PASS→PASS** regression safety.
- **Credible evaluation**: determinism (pinned toolchains/containers), clear constraints, and **anti-gaming** rules (no “fix” by skipping tests or disabling CI unless that’s explicitly the task).
- **Ongoing iteration**: datasets and the harness are treated like products—**released, versioned, and re-run** whenever agent capabilities change.

## Current focus (v0.1 direction)
- **Clang initiative**: compiler bugfixes, small implementations, tests/coverage improvements, and optional review/triage tasks—scored by upstream-relevant test targets and policy compliance.
- **Boost / cppalliance CI fixes**: GH Actions failure → patch loop benchmarks, including the hard part: **correctly attributing fixes across repos/dependencies** when a workspace build is involved.

## Initial direction (prep work)
Before we start shipping datasets and a runner, the first push is to make the work **defensible and comparable**:
- **Survey existing agent benchmarks** and map what they measure to our C/C++ suites (Clang workflow + Boost CI reality).
- **Define the evaluation contract**: a canonical case schema, suite-by-suite scoring rubric, and C/C++-specific anti-gaming + determinism controls.
- **Lock a baseline protocol**: which baselines to run (single-shot vs tool-using, retrieval on/off), harness standardization, and leakage/contamination safeguards.

## Design principles (non-negotiables)
- **Replayable and pinned**: repo URL + `base_sha` + exact commands.
- **Gold outcome exists**: reference merge SHA or patch with proof it passes the evaluation steps.
- **Deterministic evaluation**: stable environment notes (or container/toolchain pinning) and flake quarantine.
- **Protected paths by default**: disallow “turn off the checker” fixes; require explicit per-case exceptions.

## What’s in here today
- `Draft Plan/`: working specs that define suites, schemas, and data-collection requirements.

## Contributing (lightweight)
If you add a benchmark case or spec update, aim for:
- a pinned `base_sha` with baseline-failing evidence
- deterministic `evaluation_steps`
- explicit constraints (allowed/forbidden paths; allowed repos if multi-repo)
- a verified gold reference

If you’re looking for the project north star: **a small, high-signal C/C++ benchmark suite with published baselines that can be re-run on every iteration of an agent stack.**

