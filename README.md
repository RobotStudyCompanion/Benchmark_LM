# Benchmark_LM

[![Repo status](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![CI](https://github.com/RobotStudyCompanion/Benchmark_LM/actions/workflows/ci.yml/badge.svg)](https://github.com/RobotStudyCompanion/Benchmark_LM/actions/workflows/ci.yml)
[![Version](https://img.shields.io/github/v/tag/RobotStudyCompanion/Benchmark_LM?label=version)](https://github.com/RobotStudyCompanion/Benchmark_LM/tags)
[![Licence](https://img.shields.io/badge/licence-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.19643021-blue)](https://doi.org/10.5281/zenodo.19643021)

Reproducible benchmark suite for open-source language models on edge hardware, developed for the Robot Study Companion (RSC) project ([rsc.ee](https://rsc.ee)). The suite evaluates each model across three dimensions — inference efficiency (tokens per second, energy consumption), general knowledge (a six-category MMLU subset), and teaching effectiveness (LLM-rated against eight pedagogical criteria) — primarily on the Raspberry Pi 4, with scalability comparisons on the Raspberry Pi 5 and a laptop NVIDIA RTX 4060 GPU.

The benchmark data, MMLU scores, teaching-effectiveness ratings, human rater workbooks, and full methodology live in the accompanying Zenodo record: [10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021).

---

## Scripts

**Benchmark runners** (one per platform, near-identical but differ in output directory and platform-specific telemetry):

| Script | Platform | Notes |
|---|---|---|
| `benchmarking_pi4.py` | Raspberry Pi 4 | Power and energy telemetry via `vcgencmd`, disk-I/O telemetry, thermal wait-for-cooldown between models. |
| `benchmarking_pi5.py` | Raspberry Pi 5 | Same telemetry as the Pi 4 script; underlying power calibration inherited from the Pi 4 (see paper §V-D). |
| `benchmarking_computer.py` | Laptop / desktop | Dual `time.time()` / `time.perf_counter()` timings. No power or disk-I/O telemetry. |

**MMLU evaluation:**

| Script | Purpose |
|---|---|
| `MMLU.py` | Runs the six-category MMLU subset (Formal Logic, Global Facts, College Computer Science, College Mathematics, Marketing, High School Macroeconomics) via DeepEval. |
| `visualize_mmlu.py` | Generates bar and radar plots from the MMLU JSON outputs. |

**Results analysis** (one per platform, sharing the teaching-effectiveness rating path; the `*_pi4` and `*_computer` variants additionally support a `.env` file for the OpenAI API key):

| Script | Purpose |
|---|---|
| `analyze_results.py` | Aggregates JSON results from `./results/` into summary statistics and plots. Optionally rates teaching effectiveness via the OpenAI API. Generic baseline. |
| `analyze_results_pi4.py` | Pi 4 variant with disk-I/O metrics, thermal metrics, and model-size-split (<2 B / ≥2 B) graph generation. |
| `analyse_results_computer.py` | Laptop variant with the model-size split; no Pi-specific telemetry. |
| `compare_platforms.py` | Cross-platform comparison for a single model. Loads results from `results_pi4/`, `results_pi5/`, and `results_computer/`; writes bar charts of TPS, TTFT, inference time, IOPS, and TPJ to `graph_comparison/`. |

**Forward-looking material** lives under [`future/`](future/) and is not used by any script in v0.1.

---

## Requirements

- Linux (tested on Raspberry Pi OS Lite 64-bit, kernel 6.12, Debian 12 bookworm; any modern Linux distribution works for the non-Pi scripts)
- Python 3.8 or higher
- [Ollama](https://ollama.com/download) installed and running
- Python packages pinned in [`requirements.txt`](requirements.txt):
  - `ollama==0.1.0`, `psutil==5.9.0`, `matplotlib==3.7.0`, `pandas==2.0.0`, `openai==1.0.0`, `deepeval==0.21.0`, `python-dotenv>=1.0.0`, `numpy>=1.24.0`

Power and disk-I/O telemetry relies on `vcgencmd` and `psutil.disk_io_counters()` respectively, so these metrics are only populated when running on Raspberry Pi hardware. All other metrics run on any Linux host.

---

## Installation

Clone the repository and run the provided setup script:

```bash
git clone https://github.com/RobotStudyCompanion/Benchmark_LM.git
cd Benchmarking_LLM
./setup.sh
source .venv/bin/activate
```

`setup.sh` creates a `.venv/`, installs the pinned dependencies, and warns if Ollama is not on your `PATH`. It accepts `--force` to recreate the environment, `--clean` to remove it, and `--help` to list all options.

If you prefer to manage your own environment, install the dependencies directly:

```bash
pip install -r requirements.txt
```

Finally, pull each model you wish to benchmark via Ollama, e.g. `ollama pull qwen3:0.6b`.

---

## Configuration

### 1. Models list

Open `Excel_models.xlsx`, add one row per model (see existing rows for the format), and export as a semicolon-delimited CSV named `Excel_models.csv` in the project root. The `Ollama name` column must match the tag used by Ollama exactly — find it on [ollama.com/library](https://ollama.com/library). The benchmark runners auto-detect the intersection of models present both in Ollama and in `Excel_models.csv`.

### 2. Questions (optional)

The ten pedagogical questions used in the study live in `questions.txt` (one per line; lines beginning with `#` are comments). Edit the file to substitute your own set whilst preserving the format.

### 3. OpenAI API key (optional, for teaching-effectiveness rating)

Obtain a key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and provide it via either:

**Environment variable:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Or a `.env` file** at the project root (picked up automatically by `analyze_results_pi4.py` and `analyse_results_computer.py`):
```
OPENAI_API_KEY=your-api-key-here
```

`.env` is listed in `.gitignore` and will not be committed.

---

## Usage

Pick the benchmark runner matching your hardware. The three runners share the same interface and configuration; they differ only in the telemetry they collect and the output directory they write to.

### Raspberry Pi 4

```bash
python benchmarking_pi4.py
```

Runs every configured question against every matching model with streaming enabled. Waits for the CPU to drop below 60 °C between models to avoid thermal throttling. Writes to `results_pi4/` and appends to `benchmark.csv` incrementally.

### Raspberry Pi 5

```bash
python benchmarking_pi5.py
```

Same as above, writing to `results_pi5/`. Power calibration is inherited from the Pi 4 and may inflate absolute Pi 5 TPJ values; see paper §V-D.

### Laptop / desktop

```bash
python benchmarking_computer.py
```

Writes to `results_computer/`. No power or disk-I/O telemetry, but retains dual-timing (`time.time()` and `time.perf_counter()`) measurements.

### MMLU evaluation

MMLU is compute-intensive; run it on a discrete GPU where possible.

```bash
python MMLU.py
```

By default, `MMLU.py` evaluates a single model set in its `__main__` block. Edit that call to change the model, or swap in `run_mmlu_for_all_models()` to cover every Ollama-registered model. Outputs land in `MMLU/` as per-model JSON/CSV plus per-task checkpoints.

### Results analysis

After running a benchmark, analyse the output with the matching script:

```bash
python analyze_results_pi4.py        # reads results_pi4/, writes analysis_graphs_pi4/
python analyse_results_computer.py   # reads results_computer/, writes analysis_graphs_computer/
python analyze_results.py            # generic baseline, reads results/, writes analysis_graphs/
```

Each script writes an `analysis_summary.csv` and a set of plots. If an OpenAI API key is available (see §Configuration), the script also rates each model response against eight teaching criteria (clarity, accuracy, engagement, structure, completeness, appropriate level, examples/analogies, actionable) using `gpt-4o-mini`, writing a `teaching_effectiveness_ratings.json` and two additional plots.

### Cross-platform comparison

Once you have results on two or more platforms:

```bash
python compare_platforms.py
```

Prompts for a model name and writes per-metric bar charts to `graph_comparison/` comparing Pi 4, Pi 5, and laptop performance on TPS, TTFT, inference time, IOPS, and TPJ.

### MMLU visualisation

```bash
python visualize_mmlu.py
```

Reads the JSON files in `MMLU/`, splits models into small (< 2 B) and large (≥ 2 B), and writes overall and per-task bar charts plus a radar chart per model to the same directory.

---

## Future work

The [`future/`](future/) directory holds forward-looking material that is not part of v0.1 or the accompanying paper, including a revised v2 question set (`benchmark_prompts.txt`) with pedagogical and bias axes, and scoping notes for a future C rewrite of the benchmark harness and a split-requirements dependency layout.

---

## Citing

**Zenodo dataset:**

Lamouille, D., Zorec, M. B., Baksh, F., & Kruusamäe, K. (2026). *Supplemental materials to "Benchmarking Local Language Models for Social Robots using Edge Devices"* [Data set]. Zenodo. [https://doi.org/10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021)

The accompanying paper citation will be added once the paper is published. A machine-readable [`CITATION.cff`](CITATION.cff) is provided at the repository root.

---

## Learn more

- **Data, methodology, and caveats:** the Zenodo record ([10.5281/zenodo.19643021](https://doi.org/10.5281/zenodo.19643021)) carries the canonical data dictionary, full methodology, and known caveats alongside the per-run data.
- **The RSC project:** [rsc.ee](https://rsc.ee).

---

## Licence

Apache 2.0 — see [`LICENSE`](LICENSE).