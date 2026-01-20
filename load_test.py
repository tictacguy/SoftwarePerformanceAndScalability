#!/usr/bin/env python3
"""
Load testing script using Locust
"""
from locust import HttpUser, task, between
import json
import random

class MovieSearchUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Load queries when user starts"""
        try:
            with open('queries.json', 'r') as f:
                self.queries = json.load(f)
        except FileNotFoundError:
            print("queries.json not found. Please run generate_queries.py first.")
            self.queries = ["Matrix", "Godfather", "Pulp Fiction"]  # Fallback
    
    @task(8)
    def search_movie(self):
        """Search for a movie (80% of requests)"""
        query = random.choice(self.queries)
        self.client.get(f"/search/{query}")
    
    @task(2)
    def get_movie_details(self):
        """Get movie details (20% of requests)"""
        # First search for a movie
        query = random.choice(self.queries)
        response = self.client.get(f"/search/{query}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                # Get details for the first result
                tconst = data['results'][0]['tconst']
                self.client.get(f"/movie/{tconst}")
    
    @task(1)
    def health_check(self):
        """Health check (10% of requests)"""
        self.client.get("/health")

# Run with: locust -f load_test.py --host=http://localhost:8000