import ollama
from deepeval.benchmarks import MMLU
from deepeval.benchmarks.mmlu.task import MMLUTask
import pandas as pd
import re
import json
import os
from datetime import datetime
import time
import signal
from contextlib import contextmanager

class OllamaModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.timeout_seconds = 60
        self.max_retries = 3
        self.call_count = 0
        
        # Detect model type and adjust parameters
        if 'deepseek' in model_name.lower():
            self.num_predict = 500
            self.is_reasoning_model = True
        elif 'qwen' in model_name.lower():
            self.num_predict = 200
            self.is_reasoning_model = False
        else:
            self.num_predict = 50
            self.is_reasoning_model = False

    def extract_answer_from_deepseek(self, text: str) -> str:
        """Extract the answer from a DeepSeek-R1 model that uses <think> tags."""
        if '</think>' in text:
            answer_part = text.split('</think>')[-1].strip()
        else:
            answer_part = text.strip()
        
        # Chercher une lettre A/B/C/D
        match = re.search(r'\b[A-D]\b', answer_part, re.IGNORECASE)
        if match:
            return match.group(0).upper()
        
        # Fallback: search the entire text
        match = re.search(r'\b[A-D]\b', text, re.IGNORECASE)
        if match:
            return match.group(0).upper()
        
        return None

    def generate(self, prompt: str) -> str:
        """Generate a response with timeout and automatic retry."""
        
        self.call_count += 1
        
        # Display the first 3 prompts
        if self.call_count <= 3:
            print(f"\n{'='*60}")
            print(f"📝 PROMPT #{self.call_count}")
            print(f"{'='*60}")
            print(prompt[:500])
            if len(prompt) > 500:
                print("... (truncated)")
            print(f"{'='*60}")
        
        for attempt in range(self.max_retries):
            try:
                response = ollama.generate(
                    model=self.model_name, 
                    prompt=prompt,
                    options={
                        'num_predict': self.num_predict,
                        'temperature': 0.1
                    }
                )
                answer = response["response"].strip()
                
                # Afficher la réponse brute pour les 3 premiers
                if self.call_count <= 3:
                    print(f"\n🤖 RAW MODEL RESPONSE:")
                    print(answer if answer else "(empty)")
                    print(f"Length: {len(answer)} chars")

                # Extract first, then decide on length
                extracted = None
                if self.is_reasoning_model:
                    extracted = self.extract_answer_from_deepseek(answer)
                else:
                    match = re.search(r'\b[A-D]\b', answer, re.IGNORECASE)
                    if match:
                        extracted = match.group(0).upper()
                    elif answer and len(answer) > 0 and answer[0].upper() in ['A', 'B', 'C', 'D']:
                        extracted = answer[0].upper()
                
                # Valid letter found -> return immediately
                if extracted:
                    if self.call_count <= 3:
                        print(f"\n✅ EXTRACTED ANSWER: {extracted}")
                        print(f"{'='*60}\n")
                    return extracted
                
                # Otherwise, check whether the response is genuinely empty/invalid
                if not answer or len(answer) == 0:
                    if self.call_count <= 3:
                        print(f"\n⚠️ EMPTY RESPONSE")
                    # Retry with more tokens
                    if attempt < self.max_retries - 1:
                        if self.call_count <= 3:
                            print(f"Retrying with more tokens...")
                        self.num_predict = min(self.num_predict * 2, 1000)
                        time.sleep(1)
                        continue
                
                # No letter found, retrying
                if attempt < self.max_retries - 1:
                    if self.call_count <= 3:
                        print(f"\n⚠️ NO A/B/C/D LETTER FOUND, retrying...")
                    self.num_predict = min(self.num_predict * 2, 1000)
                    time.sleep(1)
                    continue
                else:
                    if self.call_count <= 3:
                        print(f"\n⚠️ NO LETTER FOUND after {self.max_retries} attempts, defaulting to 'A'")
                        print(f"{'='*60}\n")
                    return 'A'
                

            except Exception as e:
                print(f"⚠️ Error (tentative {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Failed after {self.max_retries} attempts, defaulting to 'A'")
                    if self.call_count <= 3:
                        print(f"{'='*60}\n")
                    return 'A'
        
        return 'A'


def run_mmlu_single_model(model_name):
    """Run MMLU benchmark for a single model"""

    # Create output directory
    output_dir = "./MMLU"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*60)
    print("MMLU BENCHMARK - SINGLE MODEL")
    print("="*60)
    print(f"\nTesting model: {model_name}")

    # Define tasks
    tasks = [
        MMLUTask.FORMAL_LOGIC,
        MMLUTask.GLOBAL_FACTS,
        MMLUTask.COLLEGE_COMPUTER_SCIENCE,
        MMLUTask.COLLEGE_MATHEMATICS,
        MMLUTask.MARKETING,
        MMLUTask.HIGH_SCHOOL_MACROECONOMICS
    ]

    print(f"Tasks: {len(tasks)} MMLU categories")
    for task in tasks:
        task_name = task.value if hasattr(task, 'value') else str(task)
        print(f"   - {task_name}")
    print("-"*60)

    try:
        # Initialize model
        print(f"\n🔄 Loading model {model_name}...")
        model = OllamaModel(model_name)

        benchmark = MMLU(
            tasks=tasks,
            n_shots=3
        )

        # Evaluation with progressive checkpointing
        print("\n🚀 Starting evaluation (showing the first 3 questions)...")
        
        benchmark.evaluate(model=model)

        # Store results
        task_names = [task.value if hasattr(task, 'value') else str(task) for task in tasks]

        # Calculate per-task scores from predictions
        task_scores = {}
        if hasattr(benchmark, 'predictions') and benchmark.predictions is not None:
            predictions_df = benchmark.predictions if isinstance(benchmark.predictions, pd.DataFrame) else pd.DataFrame(benchmark.predictions)

            # Display the first 3 predictions with comparison
            print(f"\n{'='*60}")
            print("📋 FIRST 3 QUESTIONS — COMPARISON")
            print(f"{'='*60}")
            for idx in range(min(3, len(predictions_df))):
                row = predictions_df.iloc[idx]
                print(f"\nQuestion #{idx + 1}:")
                print(f"  Task: {row.get('Task', 'N/A')}")
                print(f"  Expected answer: {row.get('Expected Output', 'N/A')}")
                print(f"  Model answer: {row.get('Actual Output', 'N/A')}")
                print(f"  Correct: {'✅ YES' if row.get('Correct', False) else '❌ NO'}")
                print("-" * 60)

            for task_name in task_names:
                task_preds = predictions_df[predictions_df['Task'] == task_name]
                if len(task_preds) > 0:
                    score = task_preds['Correct'].mean()
                    task_scores[task_name] = score
                    
                    # Per-task progressive checkpoint
                    checkpoint_data = {
                        'model_name': model_name,
                        'task_name': task_name,
                        'score': score,
                        'num_questions': len(task_preds),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    save_checkpoint(model_name, task_name, checkpoint_data, output_dir)

        result = {
            'model_name': model_name,
            'overall_score': benchmark.overall_score,
            'tasks': task_names,
            'task_scores': task_scores,
            'num_tasks': len(tasks),
            'n_shots': 3,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'success',
            'predictions': benchmark.predictions
        }

        # Print per-task scores
        if task_scores:
            print(f"\n📊 Per-Task Scores:")
            for task_name, score in task_scores.items():
                print(f"   {task_name:35s}: {score:.4f} ({score*100:.2f}%)")

        print(f"\n✅ Overall Score: {benchmark.overall_score:.4f} ({benchmark.overall_score*100:.2f}%)")

        # Save results
        save_results(result, output_dir, model_name)

        return result

    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        import traceback
        traceback.print_exc()
        
        tasks = [
            MMLUTask.FORMAL_LOGIC,
            MMLUTask.GLOBAL_FACTS,
            MMLUTask.COLLEGE_COMPUTER_SCIENCE,
            MMLUTask.COLLEGE_MATHEMATICS,
            MMLUTask.MARKETING,
            MMLUTask.HIGH_SCHOOL_MACROECONOMICS
        ]
        task_names = [task.value if hasattr(task, 'value') else str(task) for task in tasks]
        result = {
            'model_name': model_name,
            'overall_score': 0.0,
            'tasks': task_names,
            'task_scores': {},
            'num_tasks': len(tasks),
            'n_shots': 3,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'failed',
            'error': str(e),
            'predictions': []
        }
        save_results(result, output_dir, model_name)
        return result
    
    finally:
        # Décharger le modèle
        unload_model(model_name)


def save_checkpoint(model_name, task_name, results, output_dir):
    """Progressive checkpoint saved after each task."""
    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    clean_model_name = model_name.replace(':', '_').replace('/', '_')
    clean_task_name = task_name.replace(' ', '_')
    
    checkpoint_file = os.path.join(
        checkpoint_dir, 
        f"{clean_model_name}_{clean_task_name}_checkpoint.json"
    )
    
    with open(checkpoint_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Checkpoint saved: {clean_task_name}")





def unload_model(model_name):
    """Unload a model from memory."""
    try:
        print(f"\n🧹 Unloading model {model_name}...")
        ollama.generate(model=model_name, prompt="", keep_alive=0)
        print(f"✅ Model {model_name} unloaded from memory")
        return True
    except Exception as e:
        print(f"⚠️ Error unloading {model_name}: {e}")
        return False


def save_results(result, output_dir, model_name):
    """Save results to JSON and CSV files"""

    # Clean model name for filename (replace special characters)
    clean_model_name = model_name.replace(':', '_').replace('/', '_')

    # Create a copy without predictions (only keep scores)
    result_copy = {
        'model_name': result['model_name'],
        'overall_score': result['overall_score'],
        'tasks': result['tasks'],
        'task_scores': result.get('task_scores', {}),
        'num_tasks': result.get('num_tasks', len(result['tasks'])),
        'n_shots': result['n_shots'],
        'timestamp': result['timestamp'],
        'status': result['status']
    }

    # Include error if present
    if 'error' in result:
        result_copy['error'] = result['error']

    # Save to JSON (without detailed predictions, only scores)
    json_path = os.path.join(output_dir, f'{clean_model_name}_MMLU.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_copy, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {json_path}")

    # Prepare data for CSV (without detailed predictions)
    csv_row = {
        'model_name': result['model_name'],
        'overall_score': result['overall_score'],
        'tasks': ', '.join(result['tasks']) if isinstance(result['tasks'], list) else result['tasks'],
        'num_tasks': result.get('num_tasks', len(result['tasks']) if isinstance(result['tasks'], list) else 1),
        'n_shots': result['n_shots'],
        'timestamp': result['timestamp'],
        'status': result['status']
    }

    # Add per-task scores as separate columns
    task_scores = result.get('task_scores', {})
    for task_name, score in task_scores.items():
        csv_row[f'score_{task_name}'] = score

    if 'error' in result:
        csv_row['error'] = result['error']

    # Save to CSV
    df = pd.DataFrame([csv_row])
    csv_path = os.path.join(output_dir, f'{clean_model_name}_MMLU.csv')
    df.to_csv(csv_path, index=False)
    print(f"💾 Results saved to: {csv_path}")


def get_available_models():
    """Get all available models from Ollama"""
    try:
        models_list = ollama.list()
        # Extract model names, excluding embedding models
        model_names = [model['model'] for model in models_list['models']
                      if 'embed' not in model['model'].lower()]
        return sorted(model_names)
    except Exception as e:
        print(f"❌ Error getting model list: {e}")
        return []


def run_mmlu_for_all_models():
    """Run MMLU benchmark for all available Ollama models"""

    print("\n" + "="*60)
    print("MMLU BENCHMARK - ALL MODELS")
    print("="*60)

    # Show tasks being tested
    tasks = [
        MMLUTask.FORMAL_LOGIC,
        MMLUTask.GLOBAL_FACTS,
        MMLUTask.COLLEGE_COMPUTER_SCIENCE,
        MMLUTask.COLLEGE_MATHEMATICS,
        MMLUTask.MARKETING,
        MMLUTask.HIGH_SCHOOL_MACROECONOMICS
    ]

    print(f"\n📚 Testing {len(tasks)} MMLU task categories:")
    for task in tasks:
        task_name = task.value if hasattr(task, 'value') else str(task)
        print(f"   - {task_name}")

    # Get all available models
    models = get_available_models()

    if not models:
        print("❌ No models found in Ollama!")
        return []

    print(f"\n✅ Found {len(models)} model(s) to test:")
    for model in models:
        print(f"   - {model}")
    print()

    # Store all results for summary
    all_results = []

    # Test each model
    for idx, model_name in enumerate(models, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(models)}] Testing: {model_name}")
        print('='*60)

        result = run_mmlu_single_model(model_name)
        all_results.append(result)

        # Print immediate result
        if result['status'] == 'success':
            print(f"✅ {model_name}: Score = {result['overall_score']:.4f}")
        else:
            print(f"❌ {model_name}: Failed - {result.get('error', 'Unknown error')}")
        
        print(f"\n{'='*60}")
        print(f"Model {model_name} complete. Memory released.")
        print('='*60)

    # Print final summary
    print_summary(all_results)

    return all_results


def print_summary(results):
    """Print summary of all benchmark results"""

    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

    # Filter successful results
    successful_results = [r for r in results if r['status'] == 'success']
    failed_results = [r for r in results if r['status'] == 'failed']

    print(f"\n📊 Total models tested: {len(results)}")
    print(f"   ✅ Successful: {len(successful_results)}")
    print(f"   ❌ Failed: {len(failed_results)}")

    if successful_results:
        # Sort by score
        sorted_results = sorted(successful_results, key=lambda x: x['overall_score'], reverse=True)

        print("\n🏆 RANKINGS:")
        print("-"*60)
        for i, result in enumerate(sorted_results, 1):
            score_pct = result['overall_score'] * 100
            print(f"{i:2d}. {result['model_name']:30s} - {result['overall_score']:.4f} ({score_pct:.2f}%)")

        # Statistics
        scores = [r['overall_score'] for r in successful_results]
        print("\n📈 STATISTICS:")
        print("-"*60)
        print(f"Mean score:   {sum(scores)/len(scores):.4f}")
        print(f"Median score: {sorted(scores)[len(scores)//2]:.4f}")
        print(f"Best score:   {max(scores):.4f}")
        print(f"Worst score:  {min(scores):.4f}")

    if failed_results:
        print("\n⚠️  FAILED MODELS:")
        print("-"*60)
        for result in failed_results:
            print(f"   - {result['model_name']}: {result.get('error', 'Unknown error')}")

    print("\n" + "="*60)


if __name__ == "__main__":
    # Paper coverage: all 25 models were evaluated via run_mmlu_for_all_models().
    # The single-model call below was the last dev invocation; uncomment the
    # all-models call to reproduce the full paper dataset.
    print("Starting MMLU evaluation...")
    run_mmlu_single_model('granite4:1b-h')
    # run_mmlu_for_all_models()