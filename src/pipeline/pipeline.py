import subprocess
import time
import sys


def run_step(step_name, command):
    """
    Executes a shell command, tracking its execution time and handling errors.
    """
    print(f"\n{'='*60}")
    print(f"🚀 STARTING: {step_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # check=True ensures that if a script fails, it throws an error immediately
        subprocess.run(command, check=True, text=True)
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ SUCCESS: {step_name} completed in {elapsed_time:.1f} seconds.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FATAL ERROR: {step_name} failed. Pipeline halted.")
        # Stop the entire pipeline so we don't train models on broken data
        sys.exit(1) 

def run_pipeline():
    """
    The master orchestrator that runs the entire Kano GeoAI framework in sequence.
    """
    print("🌍 KANO GEO-AI: MASTER PIPELINE INITIALIZED 🌍")
    total_start_time = time.time()

    # Define the exact execution order of your system
    pipeline_steps = [
        #("1. Data Ingestion: Market Prices (FEWS NET)", ["python", "-m", "src.data.fetch_prices"]),
        #("2. Data Ingestion: Satellite Data (GEE)", ["python", "-m", "src.data.fetch_satellite"]),
        ("3. Data Engineering: ETL Pipeline", ["python", "-m", "src.data.etl_pipeline"]),
        ("4. Features: Build Features", ["python", "-m", "src.features.build_features"]),
        ("5. Machine Learning: Train Price Models", ["python", "-m", "src.models.train_price_models"]),
        ("6. Machine Learning: Train Stress Model", ["python", "-m", "src.models.train_stress_model"]),
        
        # Optional: You can uncomment the evaluation script if you want a report printed every time
        ("7. Model Evaluation: Generate Metrics", ["python", "-m", "src.models.evaluate_models"])
    ]

    # Execute each step one by one
    for name, cmd in pipeline_steps:
        run_step(name, cmd)

    # Final Report
    total_elapsed = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉")
    print(f"⏱️  Total Execution Time: {total_elapsed / 60:.2f} minutes.")
    print(f"{'='*60}")
    print("👉 Your database and models are now fully up to date.")
    print("👉 To view the results, run: streamlit run src/app/dashboard.py")

if __name__ == "__main__":
    run_pipeline()