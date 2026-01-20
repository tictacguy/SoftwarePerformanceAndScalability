#!/usr/bin/env python3
"""
Test improved architecture performance
"""
from performance_test import PerformanceTester
import json

def main():
    # Test improved architecture on port 8001
    tester = PerformanceTester("http://localhost:8001")
    
    print("Testing improved architecture...")
    results = tester.run_scalability_test()
    
    # Save improved results
    with open('improved_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Compare with original
    try:
        with open('performance_results.json', 'r') as f:
            original = json.load(f)
        
        print("\n=== COMPARISON ===")
        for orig, impr in zip(original, results):
            if orig['num_users'] == impr['num_users']:
                print(f"Users {orig['num_users']}:")
                print(f"  Original: {orig['success_rate']:.1f}% success, {orig['throughput']:.1f} req/s")
                print(f"  Improved: {impr['success_rate']:.1f}% success, {impr['throughput']:.1f} req/s")
                improvement = (impr['throughput'] / orig['throughput'] - 1) * 100
                print(f"  Improvement: {improvement:+.1f}%\n")
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    main()