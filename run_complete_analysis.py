#!/usr/bin/env python3
"""
Complete analysis pipeline - runs all steps
"""
import subprocess
import sys
import time
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"STEP: {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    print("MOVIE DASHBOARD - COMPLETE PERFORMANCE ANALYSIS")
    print("This will run all 4 steps of the analysis")
    
    # Step 1: Setup database
    if not run_command("python setup_database.py", "Setting up database and importing data"):
        print("Database setup failed. Please check your data files.")
        return
    
    # Step 2: Generate queries
    if not run_command("python generate_queries.py", "Generating 10,000 queries based on rating probability"):
        print("Query generation failed.")
        return
    
    print("\n" + "="*50)
    print("STARTING API SERVER FOR TESTING")
    print("="*50)
    print("Please start the API server in another terminal:")
    print("python api.py")
    print("\nPress Enter when the server is running...")
    input()
    
    # Step 3: Performance testing
    if not run_command("python performance_test.py", "Running performance tests"):
        print("Performance testing failed. Make sure API server is running.")
        return
    
    # Step 4: JMT Analysis
    if not run_command("python jmt_analysis.py", "Running JMT theoretical analysis"):
        print("JMT analysis failed.")
        return
    
    # Generate final report
    if not run_command("python generate_report.py", "Generating comprehensive report"):
        print("Report generation failed.")
        return
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print("Generated files:")
    print("- movies.db (database)")
    print("- queries.json (10,000 test queries)")
    print("- performance_results.json (load test results)")
    print("- jmt_analysis.json (theoretical analysis)")
    print("- jmt_analysis.png (performance charts)")
    print("- performance_report.json (complete analysis)")
    print("- PERFORMANCE_REPORT.md (readable report)")
    
    print("\nTo test improved architecture:")
    print("python improved_architecture.py")

if __name__ == "__main__":
    main()