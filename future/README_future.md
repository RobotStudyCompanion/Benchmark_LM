# future_work/

Forward-looking material that is **not** part of the v0.1 release or the accompanying paper. Nothing in this directory is currently imported by the benchmark suite; it is preserved here as scope for subsequent versions.

## Contents

### `benchmark_prompts.txt`

A revised, more structured question set for a follow-up study. Twenty items organised along two axes:

- **Pedagogical axis (16 items)** — two items each for eight pedagogical sub-axes: simple explanation, level adaptation, analogy generation, assessment design, misconception handling, structured simplification, student guidance, and critical thinking.
- **Bias axis (4 items)** — probes covering Eurocentrism in science history, gender attribution, colonial framing, and Global South contributions.

The paper (v0.1) uses `../questions.txt` — a smaller, gravity-anchored set of ten items. `benchmark_prompts.txt` will not produce results comparable to those in the paper.

## Scope for future versions

1. **Benchmark harness rewrite in sh or C.** The current Python harness incurs non-trivial overhead on the Raspberry Pi (psutil sampling, subprocess calls to `vcgencmd`, Python runtime for the orchestration loop). A sh or C implementation calling Ollama's HTTP API directly, with native perf-counter sampling, might help reduce measurement noise on the slowest platforms and free CPU headroom that currently competes with the model being benchmarked. Target: sub-1% measurement overhead.

2. **Dependency optimisation.** `requirements.txt` currently pulls in `matplotlib`, `pandas`, `deepeval`, and `openai` at the top level, which together install ~200 MB of transitive dependencies. Splitting into `requirements-core.txt` (benchmarking only: `ollama`, `psutil`) and `requirements-analysis.txt` (plotting, rating) would let a Pi deployment install ~20 MB instead of ~200 MB, freeing SD-card capacity relevant to the RSC's on-device footprint budget.
   1. Add support for users preferring alternative remote API services.

3. **Externalise research-critical prompts.** The GPT-4o-mini teaching-effectiveness rating prompt and the benchmark runner's study-companion system prompt currently live as inline Python f-strings, duplicated across three analysis scripts and three benchmark runners respectively. Moving them into versioned plain-text files under a `prompts/` directory would decouple the paper's prompt citation from analyser line numbers, eliminate the three-way duplication risk (silent drift across platforms), and let future rubric revisions ship as `prompts/v2/` alongside `prompts/v1/` for A/B comparisons. The same change opens the door to third-party rubric contributions without a code edit.

4. **Consolidate per-platform scripts.** v0.1 ships `benchmarking_{pi4,pi5,computer}.py` and `analyze_results{_pi4,}.py` / `analyse_results_computer.py` as near-duplicate per-platform files, preserving the provenance of the paper runs. A single platform-aware runner and a single analyser, with `--platform {pi4,pi5,computer,auto}` flags and conditional telemetry blocks, would collapse ~4,000 lines of near-identical code to ~1,500 with no functional loss.

5. **Expanded question set validation.** `benchmark_prompts.txt` needs human rater coverage and inter-rater reliability analysis before it can be published as a successor to `questions.txt`.

## How to contribute

This directory is intentionally low-commitment. Open an issue on the main repository if you want to discuss scope, and use a branch prefixed `future/` for any exploratory work.