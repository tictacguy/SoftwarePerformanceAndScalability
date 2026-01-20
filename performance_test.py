#!/usr/bin/env python3
"""
Performance testing and bottleneck analysis
"""
import requests
import time
import json
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

class PerformanceTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.queries = self.load_queries()
    
    def load_queries(self):
        try:
            with open('queries.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return ["Matrix", "Godfather", "Pulp Fiction"]
    
    def single_request(self, query):
        """Make a single request and measure response time"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/search/{query}", timeout=10)
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
        except Exception as e:
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'status_code': 0,
                'success': False,
                'error': str(e)
            }
    
    def test_concurrent_users(self, num_users, duration=60):
        """Test with concurrent users for specified duration"""
        print(f"Testing with {num_users} concurrent users for {duration} seconds...")
        
        results = []
        start_time = time.time()
        
        def user_simulation():
            user_results = []
            while time.time() - start_time < duration:
                query = self.queries[len(user_results) % len(self.queries)]
                result = self.single_request(query)
                user_results.append(result)
                time.sleep(0.1)  # Small delay between requests
            return user_results
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_simulation) for _ in range(num_users)]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        return self.analyze_results(results, num_users)
    
    def analyze_results(self, results, num_users):
        """Analyze test results"""
        if not results:
            return None
        
        response_times = [r['response_time'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])
        total_requests = len(results)
        
        if not response_times:
            return {
                'num_users': num_users,
                'total_requests': total_requests,
                'successful_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'median_response_time': 0,
                'p95_response_time': 0,
                'throughput': 0
            }
        
        return {
            'num_users': num_users,
            'total_requests': total_requests,
            'successful_requests': success_count,
            'success_rate': success_count / total_requests * 100,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
            'throughput': success_count / 60  # requests per second
        }
    
    def run_scalability_test(self):
        """Run tests with increasing number of users"""
        user_counts = [1, 5, 10, 20, 50, 100, 200]
        results = []
        
        for num_users in user_counts:
            result = self.test_concurrent_users(num_users, duration=30)
            if result:
                results.append(result)
                print(f"Users: {num_users}, Success Rate: {result['success_rate']:.1f}%, "
                      f"Avg Response Time: {result['avg_response_time']:.3f}s, "
                      f"Throughput: {result['throughput']:.1f} req/s")
            
            time.sleep(5)  # Cool down between tests
        
        # Save results
        with open('performance_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\nPerformance test completed. Results saved to performance_results.json")
        return results

def main():
    tester = PerformanceTester()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code != 200:
            print("Server is not responding correctly. Please start the API server first.")
            return
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Please start the API server first with: python api.py")
        return
    
    print("Starting scalability test...")
    results = tester.run_scalability_test()
    
    # Find optimal number of users (best throughput with acceptable response time)
    if results:
        best_result = max(results, key=lambda x: x['throughput'] if x['avg_response_time'] < 1.0 else 0)
        print(f"\nOptimal configuration: {best_result['num_users']} users")
        print(f"Throughput: {best_result['throughput']:.1f} req/s")
        print(f"Average response time: {best_result['avg_response_time']:.3f}s")

if __name__ == "__main__":
    main()