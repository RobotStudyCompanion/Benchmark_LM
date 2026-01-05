# Benchmarking_LLM

This project provides tools to benchmark Large Language Models (LLMs) using Ollama, measuring performance metrics like inference time, tokens per second, CPU usage, memory consumption, and energy efficiency.This was made in the purpose of benchmarking models on edge devices (Raspberry Pi) in the context of the devellopement of an LLM solution for the RSC Project : rsc.ee. 
This is part of the master thesis : Benchmarking and Deploying Local Language Models for 
Social Educational Robots using Edge Devices

# Installation

You can download this code using this command :

git clone https://github.com/RobotStudyCompanion/Benchmarking_LLM.git

# Requirements and packages

Python 3.8 or higher
Ollama (you can download on : https://ollama.com/download)

you will need python packages (versions are the one that has been used during the Thesis): 
ollama 0.1.0
psutil 5.9.0
matplotlib 3.7.0
pandas 2.0.0
openai 1.0.0
deepeval 0.21.0

you can download everything using this command :
pip install ollama psutil matplotlib pandas openai deepeval

# Seting up the benchmark : 

open the Excel_models file and add the different models you want to benchmark in the table like the exemple (you can find the ollama_name of the models on the ollama library part of the website).
Save this file as .csv into the folder.

### Configure Questions (Optional)
Some questions are used for the benchmark, you can add, delete, modified every questions for your purpose.
They are stored in question.txt (follow the format)

### Set OpenAI API Key
If you want to test the effectiveness of teaching of your models, you need to import an API key (openAI key).
you can get your API key from: https://platform.openai.com/api-keys

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

# Running the benchmark

Keep in mind that depending on the device used, the benchmark can takes a lot of times. There is no checkpoint save during the process so i strongly advice to perform only a few models at a time.

You can now run benchmarking.py

**What it does:**
1. Auto-detects models installed in Ollama that match `Excel_models.csv`
2. Loads questions from [questions.txt](questions.txt)
3. Runs each question through each model
4. Measures performance metrics:
   - Tokens per second
   - Inference time
   - CPU usage
   - Memory consumption
   - Time to first token
   - Power consumption (on Raspberry Pi)
   - Energy efficiency (tokens per joule)
5. Saves results to:
   - `benchmark.csv` - Summary results
   - `results/benchmark_all_models_YYYYMMDD_HHMMSS.json` - Detailed JSON
   - `result/benchmark_all_models_YYYYMMDD_HHMMSS.csv` - Detailed CSV


## Running MMLU Benchmarks

### MMLU (Massive Multitask Language Understanding) Testing
You can run the MMLU benchmark to test the knowledge of each of you models, i recommend to perform it on a powerfull machine as it require a lot of computational power to go through every questions.

```bash
python MMLU.py
```

**What it does:**
1. Tests models on 6 MMLU task categories:
   - Formal Logic
   - Global Facts
   - College Computer Science
   - College Mathematics
   - Marketing
   - High School Macroeconomics
2. Uses 3-shot learning (provides 3 examples before each question)
3. Evaluates model accuracy on multiple-choice questions
4. Displays the first 3 prompts and responses for debugging
5. Saves progressive checkpoints after each task
6. Saves results to:
   - `MMLU/{model-name}_MMLU.json` - Summary scores by task
   - `MMLU/{model-name}_MMLU.csv` - CSV format results
   - `MMLU/checkpoints/` - Progressive checkpoints per task

**Customizing MMLU tests:**
By default, the script runs a specific model

```python
run_mmlu_single_model('granite4:1b-h')
```

To test a different model, edit this line or modify the script to test all your models:
```python
# Option 1: Test a single model
run_mmlu_single_model('llama3.2:1b')

# Option 2: Test all available models
run_mmlu_for_all_models()
```



# Analysing the results

After running the benchmark on all the models you want to test,
you can run analyse_results.py

**What it does:**
1. Loads all JSON results from `./results/` directory
2. Calculates summary statistics for each model
3. Generates visualization graphs in `./analysis_graphs/`:
   - `tokens_per_second.png` - Performance comparison
   - `energy_efficiency.png` - Energy metrics
   - `inference_time_distribution.png` - Timing distributions
   - `response_vs_performance.png` - Response length analysis
   - `resource_usage.png` - CPU, memory, temperature
   - `model_radar_chart.png` - Multi-dimensional comparison
4. Exports summary to `analysis_summary.csv`
5. (Optional) Rates teaching effectiveness using OpenAI API
   - Generates `teaching_effectiveness_ratings.json`
   - Creates `teaching_effectiveness_scores.png` and `performance_vs_teaching.png`


## Visualizing MMLU Results

If you have MMLU benchmark results, you can visualize them using visualize_mmlu.py:

**What it does:**
1. Loads MMLU results from `./MMLU/` directory (JSON files ending with `_MMLU.json`)
2. Categorizes models into small (<2B) and big (≥2B)
3. Generates visualizations:
   - Overall score comparisons (all models, small models, big models)
   - Task-specific performance graphs
   - Individual model radar charts
4. Saves graphs to `./MMLU/` directory
