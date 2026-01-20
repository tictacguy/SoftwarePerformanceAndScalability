#!/usr/bin/env python3
"""
JMT (Java Modelling Tools) analysis simulation for response time modeling
"""
import numpy as np
import matplotlib.pyplot as plt
import json
from scipy.optimize import minimize_scalar

class QueueingModel:
    def __init__(self, service_rate, db_service_rate=None):
        """
        Initialize queueing model
        service_rate: requests per second the server can handle
        db_service_rate: database requests per second (bottleneck)
        """
        self.service_rate = service_rate
        self.db_service_rate = db_service_rate or service_rate * 0.8  # DB is typically slower
    
    def mm1_response_time(self, arrival_rate, service_rate):
        """M/M/1 queue response time formula"""
        if arrival_rate >= service_rate:
            return float('inf')  # System unstable
        utilization = arrival_rate / service_rate
        return 1 / (service_rate - arrival_rate)
    
    def analyze_system(self, max_users=200):
        """Analyze system performance with increasing users"""
        users = np.arange(1, max_users + 1)
        
        # Assume each user makes 1 request per 2 seconds on average
        arrival_rates = users / 2.0
        
        # Calculate response times for different components
        web_response_times = [self.mm1_response_time(rate, self.service_rate) for rate in arrival_rates]
        db_response_times = [self.mm1_response_time(rate, self.db_service_rate) for rate in arrival_rates]
        
        # Total response time (web + database)
        total_response_times = [web + db if web != float('inf') and db != float('inf') 
                               else float('inf') for web, db in zip(web_response_times, db_response_times)]
        
        return users, arrival_rates, total_response_times, web_response_times, db_response_times
    
    def find_optimal_users(self, max_response_time=1.0):
        """Find optimal number of users with acceptable response time"""
        users, arrival_rates, response_times, _, _ = self.analyze_system()
        
        # Find maximum users with response time under threshold
        optimal_users = 0
        for i, (user_count, response_time) in enumerate(zip(users, response_times)):
            if response_time <= max_response_time:
                optimal_users = user_count
            else:
                break
        
        return optimal_users

def run_jmt_analysis():
    """Run JMT-style analysis"""
    print("Running JMT-style queueing analysis...")
    
    # Load performance results if available
    try:
        with open('performance_results.json', 'r') as f:
            perf_results = json.load(f)
        
        # Estimate service rate from performance results
        if perf_results:
            # Find the highest throughput achieved
            max_throughput = max(result['throughput'] for result in perf_results)
            service_rate = max_throughput * 1.2  # Theoretical maximum
        else:
            service_rate = 50  # Default estimate
    except FileNotFoundError:
        service_rate = 50  # Default estimate (50 req/s)
    
    print(f"Estimated service rate: {service_rate:.1f} req/s")
    
    # Create queueing model
    model = QueueingModel(service_rate=service_rate, db_service_rate=service_rate * 0.6)
    
    # Analyze system
    users, arrival_rates, response_times, web_times, db_times = model.analyze_system()
    
    # Find optimal configuration
    optimal_users = model.find_optimal_users(max_response_time=1.0)
    
    # Create analysis results
    analysis = {
        'service_rate': service_rate,
        'db_service_rate': service_rate * 0.6,
        'optimal_users': optimal_users,
        'analysis_points': []
    }
    
    for i in range(0, len(users), 5):  # Sample every 5th point
        if response_times[i] != float('inf'):
            analysis['analysis_points'].append({
                'users': int(users[i]),
                'arrival_rate': arrival_rates[i],
                'response_time': response_times[i],
                'web_response_time': web_times[i],
                'db_response_time': db_times[i]
            })
    
    # Save analysis
    with open('jmt_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Generate plot
    plt.figure(figsize=(12, 8))
    
    # Filter out infinite values for plotting
    finite_indices = [i for i, rt in enumerate(response_times) if rt != float('inf')]
    if finite_indices:
        plot_users = [users[i] for i in finite_indices]
        plot_response_times = [response_times[i] for i in finite_indices]
        plot_web_times = [web_times[i] for i in finite_indices]
        plot_db_times = [db_times[i] for i in finite_indices]
        
        plt.subplot(2, 1, 1)
        plt.plot(plot_users, plot_response_times, 'b-', label='Total Response Time', linewidth=2)
        plt.plot(plot_users, plot_web_times, 'g--', label='Web Server Response Time')
        plt.plot(plot_users, plot_db_times, 'r--', label='Database Response Time')
        plt.axhline(y=1.0, color='orange', linestyle=':', label='1s Threshold')
        plt.axvline(x=optimal_users, color='red', linestyle=':', label=f'Optimal Users ({optimal_users})')
        plt.xlabel('Number of Users')
        plt.ylabel('Response Time (seconds)')
        plt.title('JMT Analysis: Response Time vs Number of Users')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Throughput plot
        plt.subplot(2, 1, 2)
        throughput = [rate for rate in arrival_rates[:len(plot_users)]]
        plt.plot(plot_users, throughput, 'purple', linewidth=2)
        plt.axvline(x=optimal_users, color='red', linestyle=':', label=f'Optimal Users ({optimal_users})')
        plt.xlabel('Number of Users')
        plt.ylabel('Throughput (req/s)')
        plt.title('System Throughput vs Number of Users')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('jmt_analysis.png', dpi=300, bbox_inches='tight')
        print("JMT analysis plot saved as jmt_analysis.png")
    
    print(f"\nJMT Analysis Results:")
    print(f"Estimated service rate: {service_rate:.1f} req/s")
    print(f"Database service rate: {service_rate * 0.6:.1f} req/s")
    print(f"Optimal number of users: {optimal_users}")
    print(f"Analysis saved to jmt_analysis.json")
    
    return analysis

if __name__ == "__main__":
    run_jmt_analysis()