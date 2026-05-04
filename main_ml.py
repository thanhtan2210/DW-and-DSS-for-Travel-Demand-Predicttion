import sys
from src.models.train_model import run_automated_training

def main():
    """Orchestrates the automated machine learning training pipeline."""
    print("============================================================")
    print("NYC TAXI - AUTOMATED ML PIPELINE (MLOps)")
    print("============================================================")
    print("Initializing data extraction, model training, and artifact storage...\n")
    
    try:
        run_automated_training()
        print("\n[SUCCESS] Machine Learning Pipeline executed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
