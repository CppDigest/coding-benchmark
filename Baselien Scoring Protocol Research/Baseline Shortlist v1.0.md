# Baseline Shortlist v1.0

This document recommends AI models and coding agents for baseline evaluation on C/C++ engineering tasks. Models are tiered by priority and include realistic cost/performance estimates.

**Target dataset**: 60 cases (30 Clang + 30 Boost CI) as defined in v0.1 benchmark specs.

---

## Executive Summary

| Tier | Model | Est. Resolved Rate | Cost/Task | Priority |
|------|-------|-------------------|-----------|----------|
| **1** | Claude Opus 4.5 | 35-45% | $0.45 | Must-run |
| **1** | GPT-5.2 / o3 | 35-45% | $0.30 | Must-run |
| **2** | Claude Sonnet 4.5 | 25-35% | $0.10 | Recommended |
| **2** | Gemini 3 Flash | 25-35% | $0.03 | Recommended |
| **3** | DeepSeek V3.2 | 15-25% | $0.02 | Budget baseline |
| **3** | Qwen3-Coder 72B | 15-25% | $0.02 | Open-source baseline |
| **Agent** | Devin | 30-40% | ~$3.00* | Agentic reference |
| **Agent** | OpenHands + Opus | 30-40% | $0.50 | Open-source agent |
| **Agent** | Aider + Sonnet | 20-30% | $0.15 | Interactive baseline |

*\*Devin pricing is $2.00-2.25/ACU; typical task consumes ~1.5 ACUs. See [Devin section](#devin-cognition) for details.*

---

## Tier 1: Must-Run (Credibility Baselines)

These establish the performance ceiling and are required for credible baseline reporting.

### Claude Opus 4.5

| Attribute | Value |
|-----------|-------|
| **Provider** | Anthropic |
| **API Access** | `api.anthropic.com` |
| **SWE-bench Verified** | ~80.9% (Python-dominated) |
| **Est. C/C++ Rate (TU)** | 35-45% |
| **Pricing** | $15/M input, $75/M output |
| **Cost per Task** | ~$0.45 (50K in, 10K out) |
| **Training Cutoff** | ~April 2025 |
| **Tool-Use** | Excellent (function calling, parallel tools) |

**C/C++ Strengths**:
- Superior architectural understanding and multi-file reasoning
- Strong on modern C++20/23 features
- Excellent at code migration and refactoring
- Best at implicit dependency inference across header files

**C/C++ Weaknesses**:
- Occasionally hallucinates build-system changes (CMake, Bazel)
- Weaker on legacy C-style macros and 1990s idioms

**Recommendation**: Primary reference baseline. Use for TU and RE modes.

---

### GPT-5.2 / o3

| Attribute | Value |
|-----------|-------|
| **Provider** | OpenAI |
| **API Access** | `api.openai.com` |
| **SWE-bench Verified** | ~80.0% |
| **Est. C/C++ Rate (TU)** | 35-45% |
| **Pricing** | $1.75/M input, $14/M output |
| **Cost per Task** | ~$0.30 (50K in, 10K out) |
| **Training Cutoff** | ~2025 (varies by version) |
| **Tool-Use** | Excellent (native function calling) |

**C/C++ Strengths**:
- Best at multi-file refactors and linker/ABI diagnostics
- Strong mathematical reasoning (algorithms, memory calculations)
- Excellent GCC/Clang flag advice
- Multi-tier reasoning modes allow cost/quality tradeoff

**C/C++ Weaknesses**:
- Sometimes generates MSVC-only code
- Can be verbose, hitting context limits faster

**Recommendation**: Secondary reference baseline. Compare against Claude for model diversity.

---

## Tier 2: Value Baselines

High-quality models at significantly lower cost. Recommended for establishing cost-performance frontier.

### Claude Sonnet 4.5

| Attribute | Value |
|-----------|-------|
| **Provider** | Anthropic |
| **API Access** | `api.anthropic.com` |
| **SWE-bench Verified** | ~77% |
| **Est. C/C++ Rate (TU)** | 25-35% |
| **Pricing** | $3/M input, $15/M output |
| **Cost per Task** | ~$0.10 (50K in, 10K out) |
| **Training Cutoff** | ~April 2025 |
| **Tool-Use** | Same as Opus |

**C/C++ Strengths**:
- Nearly as good as Opus on algorithmic fixes
- Excellent cost/performance ratio (4x cheaper, ~85% capability)

**C/C++ Weaknesses**:
- Weaker on tricky template metaprogramming and linkage issues
- Less reliable on complex multi-file changes

**Recommendation**: Use for budget-conscious runs or high-volume validation.

---

### Gemini 3 Flash

| Attribute | Value |
|-----------|-------|
| **Provider** | Google (Vertex AI) |
| **API Access** | Vertex AI / Firebase GenAI |
| **SWE-bench Verified** | ~78% |
| **Est. C/C++ Rate (TU)** | 25-35% |
| **Pricing** | $0.50/M input, $3/M output |
| **Cost per Task** | ~$0.03 (50K in, 10K out) |
| **Training Cutoff** | ~Late 2025 |
| **Tool-Use** | Function calling (JSON) |

**C/C++ Strengths**:
- Exceptional cost-effectiveness (10x cheaper than Opus)
- 1M token context enables full codebase analysis
- Multimodal: can analyze architecture diagrams alongside code
- Good on Android/Bazel codebases

**C/C++ Weaknesses**:
- Weaker on legacy Autotools and pre-C++11 idioms
- Less autonomous than Claude/GPT for complex reasoning

**Recommendation**: Excellent for cost-efficiency baseline. Test whether 10x savings justify any accuracy gap.

---

## Tier 3: Budget / Open-Source Baselines

Establishes lower bound and enables self-hosted/air-gapped evaluation.

### DeepSeek V3.2

| Attribute | Value |
|-----------|-------|
| **Provider** | DeepSeek |
| **API Access** | `api.deepseek.com` or self-host |
| **SWE-bench Verified** | ~66-67% |
| **Est. C/C++ Rate (TU)** | 15-25% |
| **Pricing (API)** | $0.25/M input, $0.38/M output |
| **Cost per Task** | ~$0.02 (50K in, 10K out) |
| **Self-Host** | Apache-2 weights, 33B @ 22GB VRAM |
| **Tool-Use** | External scaffolding required |

**C/C++ Strengths**:
- Large context (128K) for ingesting whole files
- Very low cost for budget-constrained evaluation
- Self-hostable for air-gapped environments
- DeepSeek V3.2 Thinking variant adds explicit reasoning

**C/C++ Weaknesses**:
- Weaker reasoning on subtle UB and template SFINAE
- Requires more scaffolding for effective tool use

**Recommendation**: Budget baseline. Also use for self-hosted/privacy-sensitive scenarios.

---

### Qwen3-Coder 72B

| Attribute | Value |
|-----------|-------|
| **Provider** | Alibaba |
| **API Access** | OpenRouter, Hugging Face, Alibaba Plus |
| **SWE-bench Verified** | ~60% |
| **Est. C/C++ Rate (TU)** | 15-25% |
| **Pricing** | $0.69/M input, $0.95/M output |
| **Cost per Task** | ~$0.02 (50K in, 10K out) |
| **Self-Host** | Apache-2 weights, 72B @ 48GB VRAM (4-bit) |
| **Tool-Use** | External scaffolding required |

**C/C++ Strengths**:
- Surprisingly good on pointer arithmetic and Unicode handling
- 256K native context (up to 1M with extrapolation)
- Fully open-source with permissive licensing

**C/C++ Weaknesses**:
- Limited Western build-system exposure
- Struggles with advanced template metaprogramming
- May hallucinate Chinese comments in sparse prompts

**Recommendation**: Open-source reference baseline. Provides reproducibility without API dependency.

---

## Agentic Baselines

Full agent systems that can iterate autonomously. Essential for comparing against tool-using LLM baselines.

### Devin (Cognition)

| Attribute | Value |
|-----------|-------|
| **Provider** | Cognition AI |
| **Access** | Cloud-only (SaaS, Slack, GitHub, VSCode extension) |
| **SWE-bench** | 13-16% (autonomous, no assistance) |
| **Est. C/C++ Rate** | 30-40% (with specification) |
| **Pricing** | $2.00-2.25/ACU (Agent Compute Unit) |
| **Cost per Task** | ~$2-5 depending on complexity |
| **Self-Host** | Not available |

**C/C++ Strengths**:
- Fully autonomous 30-minute coding sessions
- Builds and runs Dockerized cross-compilers
- Can bisect with git, excellent for CI failures
- 12x efficiency gains on structured migrations (documented)

**C/C++ Weaknesses**:
- Senior-level understanding but junior-level execution
- Cannot handle ambiguous problems requiring design judgment
- Opaque; can "run away" on long compile trees
- Data processed on Cognition infrastructure (no self-host)

**Recommendation**: Reference for fully-agentic baseline. Compare against TU mode to measure scaffolding value.

---

### OpenHands + Claude Opus

| Attribute | Value |
|-----------|-------|
| **Provider** | Open-source framework + Anthropic API |
| **Access** | CLI, Local GUI, Cloud Self-hosted |
| **SWE-bench** | ~65% (with SWE-Agent architecture) |
| **Est. C/C++ Rate** | 30-40% (TU equivalent) |
| **Pricing** | Model API cost + infrastructure |
| **Cost per Task** | ~$0.50 (Opus API + minimal overhead) |
| **Self-Host** | MIT license (framework), Helm Chart available |

**C/C++ Strengths**:
- Open-source with full transparency
- Model-agnostic: swap Claude for GPT, DeepSeek, Qwen
- Strong static code analysis integration
- Self-hostable for enterprise/air-gapped use

**C/C++ Weaknesses**:
- Requires infrastructure management
- Performance depends entirely on backing model
- Less polished than commercial Devin

**Recommendation**: Open-source agent reference. Enables model ablation studies.

---

### Aider + Claude Sonnet

| Attribute | Value |
|-----------|-------|
| **Provider** | Open-source tool + Anthropic API |
| **Access** | CLI (terminal), IDE extensions |
| **SWE-bench** | 18-26% (depending on configuration) |
| **Est. C/C++ Rate** | 20-30% (interactive) |
| **Pricing** | Model API cost only |
| **Cost per Task** | ~$0.15 (Sonnet API) |
| **Self-Host** | GPL-3 license |

**C/C++ Strengths**:
- Repository mapping provides excellent file/dependency understanding
- Git integration for easy change visualization
- Interactive: developer maintains control
- Built-in compile command caching; "--exclude build" filters

**C/C++ Weaknesses**:
- Requires user confirmations; less suitable for fully automated baselines
- Performance ceiling limited by interaction model

**Recommendation**: Interactive baseline. Measures value of human-in-the-loop vs fully autonomous.

---

## Cost Estimation

### Per-Task Costs (60 cases × 3 baselines = 180 runs)

| Model | SS Cost | TU Cost | RE Cost | Total (180 runs) |
|-------|---------|---------|---------|------------------|
| Claude Opus 4.5 | $0.30 | $0.45 | $0.55 | $78 |
| GPT-5.2 | $0.20 | $0.30 | $0.40 | $54 |
| Claude Sonnet 4.5 | $0.07 | $0.10 | $0.12 | $17 |
| Gemini 3 Flash | $0.02 | $0.03 | $0.04 | $5 |
| DeepSeek V3.2 | $0.01 | $0.02 | $0.02 | $3 |
| Qwen3-Coder | $0.01 | $0.02 | $0.02 | $3 |

### Agent Costs (60 TU-equivalent runs)

| Agent | Cost/Task | Total (60 runs) | Notes |
|-------|-----------|-----------------|-------|
| Devin | ~$3.00 | ~$180 | ~1.5 ACUs/task @ $2.00/ACU |
| OpenHands + Opus | $0.50 | $30 | Opus API cost |
| Aider + Sonnet | $0.15 | $9 | Sonnet API cost |

*Note: Devin uses Agent Compute Units (ACUs) at $2.00-2.25/ACU. Tasks typically consume 1-2.5 ACUs depending on complexity. The $3.00 estimate assumes ~1.5 ACUs for a typical C/C++ CI fix task.*

### Recommended Budget

| Scenario | Models Included | Estimated Cost |
|----------|-----------------|----------------|
| **Minimum Viable** | Opus + Sonnet (TU only) | ~$35 |
| **Standard** | Tier 1 + Tier 2 (all baselines) | ~$160 |
| **Comprehensive** | All tiers + agents | ~$400 |
| **With Repeats (3×)** | Comprehensive × 3 | ~$1,200 |

---

## Recommended Evaluation Order

### Phase 1: Establish Ceiling (Week 1)

1. **Claude Opus 4.5 (TU)** - Primary reference
2. **GPT-5.2 (TU)** - Secondary reference
3. Compare to establish model diversity

### Phase 2: Cost-Performance Frontier (Week 2)

4. **Claude Sonnet 4.5 (TU)** - Value tier
5. **Gemini 3 Flash (TU)** - Cost optimization
6. Analyze cost/performance tradeoffs

### Phase 3: Lower Bounds (Week 3)

7. **DeepSeek V3.2 (TU)** - Budget tier
8. **Qwen3-Coder (TU)** - Open-source tier
9. Establish minimum viable performance

### Phase 4: Agent Comparison (Week 4)

10. **OpenHands + Opus** - Open-source agent
11. **Devin** (if budget allows) - Commercial agent
12. **Aider + Sonnet** - Interactive baseline
13. Compare agent scaffolding value

### Phase 5: Additional Baselines (Optional)

14. SS baselines for all models (capability floor)
15. RE baselines for retrieval analysis
16. Repeat runs for confidence intervals

---

## Model Selection Matrix

### By Use Case

| Use Case | Recommended Model(s) |
|----------|---------------------|
| Maximum accuracy | Claude Opus 4.5 |
| Best value | Gemini 3 Flash |
| Self-hosted required | DeepSeek V3.2 or Qwen3-Coder |
| Fully autonomous agent | Devin or OpenHands |
| Interactive development | Aider |
| Memory-safety critical | Claude Opus 4.5 or GPT-5.2 |
| Large codebase (500K+ lines) | Gemini 3 (1M context) |

### By Budget Constraint

| Monthly Budget | Recommended Tier |
|----------------|------------------|
| < $50 | Tier 3 only |
| $50-200 | Tier 2 + Tier 3 |
| $200-500 | All tiers |
| > $500 | All tiers + agents + repeats |

---

## C/C++ Specific Recommendations

### For Clang Benchmark Suite

| Suite | Best Models | Rationale |
|-------|-------------|-----------|
| Issue-Fix | Opus, GPT-5.2 | Complex reasoning, UB detection |
| Feature | Opus, Sonnet | Modern C++ knowledge |
| Tests/Coverage | Sonnet, Flash | Volume-efficient |
| PR Review | Opus, GPT-5.2 | Architectural understanding |
| Triage | Flash, Sonnet | Cost-effective retrieval |

### For Boost CI Benchmark Suite

| Suite | Best Models | Rationale |
|-------|-------------|-----------|
| Single-Repo CI | Sonnet, Flash | High volume, simpler fixes |
| Cross-Repo | Opus, GPT-5.2 | Multi-repo reasoning |
| Build-System (b2/CMake) | GPT-5.2, Opus | Build system expertise |

---

## Appendix: API Endpoints and Configuration

### Claude (Anthropic)

```yaml
endpoint: https://api.anthropic.com/v1/messages
models:
  opus: claude-opus-4.5-20250401
  sonnet: claude-sonnet-4.5-20250401
headers:
  x-api-key: ${ANTHROPIC_API_KEY}
  anthropic-version: "2024-01-01"
```

### GPT (OpenAI)

```yaml
endpoint: https://api.openai.com/v1/chat/completions
models:
  gpt5: gpt-5.2-2026-01-01
  o3: o3-2026-01-01
headers:
  Authorization: Bearer ${OPENAI_API_KEY}
```

### Gemini (Google)

```yaml
endpoint: https://generativelanguage.googleapis.com/v1beta/models
models:
  flash: gemini-3-flash-latest
headers:
  x-goog-api-key: ${GOOGLE_API_KEY}
```

### DeepSeek

```yaml
endpoint: https://api.deepseek.com/v1/chat/completions
models:
  v3: deepseek-chat-v3.2
headers:
  Authorization: Bearer ${DEEPSEEK_API_KEY}
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial shortlist based on research synthesis |

---

*Model capabilities and pricing are subject to change. Verify current information with providers before large-scale evaluation runs.*
