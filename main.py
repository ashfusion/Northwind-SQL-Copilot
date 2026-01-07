import sys
import argparse
import time
from src.pipeline import TextToSQLPipeline
from src.cache import CacheManager
from src.config import CACHE_FILE

def main():
    parser = argparse.ArgumentParser(description="Northwind SQL Copilot")
    parser.add_argument("question", nargs="?", default="Which customer has placed the least orders?", help="User question")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for this run")
    parser.add_argument("--clear-cache", action="store_true", help="Clear existing cache")
    args = parser.parse_args()

    # Handle Cache Clearing
    if args.clear_cache:
        CacheManager(file_path=CACHE_FILE).clear()
        print("Cache cleared.")

    # Welcome Message
    print("\n" + "="*50)
    print("Welcome to Northwind-SQL-Copilot")
    print("="*50 + "\n")

    try:
        # Determine if cache should be enabled
        use_cache = not args.no_cache
        pipeline = TextToSQLPipeline(use_cache=use_cache)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize pipeline.\nError: {e}")
        sys.exit(1)

    print(f"\nProcessing Question: {args.question}...")
    
    # Run Pipeline
    response = pipeline.run(args.question)

    # Display Step-by-Step Output (Simulating the components requested)
    print(f"\nSQL Generated in {response.execution_time:.2f}s (Approx)") # Note: Accessing internal timings would require changing return type, approximating with total for now or we rely on the log messages printed during execution for the steps.
    
    # The pipeline.py logs "SQL Generated in Xs" to console.
    # We display the final block here.

    print("-" * 40)
    print("\n" + "="*60)
    print(f"QUESTION : {response.question}")
    print(f"SQL QUERY: {response.sql_query}")
    print(f"ANSWER   : {response.answer}")
    if response.from_cache:
        print(f"TIME     : 0.00s (Cached)")
    else:
        print(f"TIME     : {response.execution_time}s")
    print("="*60)
    print("\nCheck logs/ for detailed execution records.\n")

if __name__ == "__main__":
    main()