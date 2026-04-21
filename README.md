# Benchmarking_LLM

[![Repo status](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Version](https://img.shields.io/github/v/tag/RobotStudyCompanion/Benchmarking_LLM?label=version)](https://github.com/RobotStudyCompanion/Benchmarking_LLM/tags)
[![Licence](https://img.shields.io/badge/licence-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643021.svg)](https://doi.org/10.5281/zenodo.19643021) -->
[![CI](https://github.com/RobotStudyCompanion/Benchmarking_LLM/actions/workflows/ci.yml/badge.svg)](https://github.com/RobotStudyCompanion/Benchmarking_LLM/actions/workflows/ci.yml)

Reproducible benchmark suite for open-source language models on edge hardware, developed for the Robot Study Companion (RSC) project ([rsc.ee](https://rsc.ee)). The suite evaluates each model across three dimensions — inference efficiency (tokens per second, energy consumption), general knowledge (a six-category MMLU subset), and teaching effectiveness (LLM-rated against eight pedagogical criteria) — primarily on the Raspberry Pi 4, with scalability comparisons on the Raspberry Pi 5 and a laptop NVIDIA RTX 4060 GPU.

The benchmark data, MMLU scores, teaching-effectiveness ratings, human rater workbooks, and full methodology live in the accompanying Zenodo record: [10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021).

---

## Scripts

| Script | Purpose |
|---|---|
| `benchmarking.py` | Laptop/desktop benchmark runner. Measures throughput, latency, CPU/memory load, and dual `time.time()`/`time.perf_counter()` timings. |
| `benchmarking_pi4.py` | Raspberry Pi 4 benchmark runner. Adds power and energy telemetry (via `vcgencmd`), thermal wait-for-cooldown between models, and disk-I/O telemetry. |
| `benchmarking_pi5.py` | Raspberry Pi 5 benchmark runner. Same telemetry as the Pi 4 script; note that the underlying power calibration is inherited from the Pi 4 (see paper §V-D). |
| `MMLU.py` | Runs the six-category MMLU subset (Formal Logic, Global Facts, College Computer Science, College Mathematics, Marketing, High School Macroeconomics) via DeepEval. |
| `analyze_results.py` | Aggregates per-run JSON results from `./results/`, produces summary statistics and plots, and optionally rates teaching effectiveness via the OpenAI API. |
| `analyze_results_pi4.py` | Pi 4 variant of the above, extended with disk-I/O metrics, thermal metrics, and model-size-split (<2 B / ≥2 B) graph generation. |
| `analyse_results_computer.py` | Laptop/desktop variant of the analyser, with the model-size split but without Pi-specific telemetry. |
| `visualize_mmlu.py` | Generates bar and radar plots from the MMLU JSON outputs. |
| `compare_platforms.py` | Cross-platform comparison for a single model: loads results from `results_pi4/`, `results_pi5/`, and `results_computer/`, writes bar charts of TPS, TTFT, inference time, IOPS, and TPJ to `graph_comparison/`. |

---

## Requirements

- Linux (tested on Raspberry Pi OS Lite 64-bit, kernel 6.12, Debian 12 bookworm; any modern Linux distribution should work for the non-Pi platforms)
- Python 3.8 or higher
- [Ollama](https://ollama.com/download)
- Python packages (versions used in the study):
  - `ollama` 0.1.0
  - `psutil` 5.9.0
  - `matplotlib` 3.7.0
  - `pandas` 2.0.0
  - `openai` 1.0.0
  - `deepeval` 0.21.0

Power and energy telemetry relies on `vcgencmd` and is therefore only available on Raspberry Pi hardware; all other metrics run on any Linux host.

---

## Installation

```bash
git clone https://github.com/RobotStudyCompanion/Benchmarking_LLM.git
cd Benchmarking_LLM
pip install ollama psutil matplotlib pandas openai deepeval
```

Pull each model you wish to benchmark via Ollama, e.g. `ollama pull qwen3:0.6b`.

---

## Configuration

### 1. Models list

Open `Excel_models.xlsx`, add one row per model (see existing rows for the format), and export as a semicolon-delimited CSV named `Excel_models.csv` in the project root. The `Ollama name` column must match the tag used by Ollama exactly — find it on [ollama.com/library](https://ollama.com/library). `benchmarking.py` auto-detects the intersection of models present both in Ollama and in `Excel_models.csv`.

### 2. Questions (optional)

The ten pedagogical questions used in the study live in `questions.txt` (one per line; lines beginning with `#` are comments). Edit the file to substitute your own set whilst preserving the format.

### 3. OpenAI API key (optional, for teaching-effectiveness rating)

Obtain a key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and export it:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

---

## Usage

### Hardware benchmark

```bash
python benchmarking.py
```

Runs every configured question against every matching model with streaming enabled. `benchmark.csv` is written incrementally, so partial progress survives interruption. Full per-session results land in `results/benchmark_all_models_YYYYMMDD_HHMMSS.{json,csv}`.

### MMLU evaluation

MMLU is compute-intensive; run it on a discrete GPU where possible.

```bash
python MMLU.py
```

By default, `MMLU.py` evaluates a single model set in its `__main__` block. Edit that call to change the model, or swap in `run_mmlu_for_all_models()` to cover every Ollama-registered model. Outputs land in `MMLU/` as per-model JSON/CSV plus per-task checkpoints.

### Hardware-result analysis

```bash
python analyze_results.py
```

Aggregates every JSON file under `results/`, writes `analysis_summary.csv`, and produces six plots under `analysis_graphs/`. If `OPENAI_API_KEY` is set, the script then rates each response against eight teaching criteria (clarity, accuracy, engagement, structure, completeness, appropriate level, examples/analogies, actionable) using `gpt-4o-mini`, writing `teaching_effectiveness_ratings.json` and two additional plots.

### MMLU visualisation

```bash
python visualize_mmlu.py
```

Reads the JSON files in `MMLU/`, splits models into small (< 2 B) and large (≥ 2 B), and writes overall and per-task bar charts plus a radar chart per model to the same directory.

---

## Citing

- Zenodo dataset:
Lamouille, D., Zorec, M. B., Baksh, F., & Kruusamäe, K. (2026). *Supplemental materials to "Benchmarking Local Language Models for Social Robots using Edge Devices"* [Data set]. Zenodo. [https://doi.org/10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021)

- The accompanying paper citation will be added once the paper is published. 
Please find a machine-readable `CITATION.cff` provided at the repository root.

---

## Learn more

- **Data, methodology, and caveats:** the Zenodo record ([10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021)) carries the canonical data dictionary, full methodology, and known caveats alongside the per-run data.
- **The RSC project:** [rsc.ee](https://rsc.ee).

---

## Licence

Apache 2.0 — see [`LICENSE`](LICENSE).