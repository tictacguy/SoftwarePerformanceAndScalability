import numpy as np
import json
from database import MovieDatabase

def generate_query_set():
    db = MovieDatabase()
    
    print("Fetching movies and their vote counts...")
    movies_votes = db.get_movies_by_votes()
    
    if not movies_votes:
        print("No movies found in database. Please run setup_database.py first.")
        return
    
    titles = [movie[0] for movie in movies_votes]
    votes = np.array([movie[1] for movie in movies_votes])
    
    probabilities = votes / votes.sum()
    
    print(f"Generating 10,000 queries from {len(titles)} movies...")
    
    query_indices = np.random.choice(len(titles), size=10000, p=probabilities)
    queries = [titles[i] for i in query_indices]
    
    with open('queries.json', 'w') as f:
        json.dump(queries, f, indent=2)
    
    print("Queries saved to queries.json")
    
    unique_queries = len(set(queries))
    print(f"Generated {len(queries)} queries ({unique_queries} unique)")
    
    from collections import Counter
    counter = Counter(queries)
    print("\nTop 10 most frequent queries:")
    for query, count in counter.most_common(10):
        print(f"  {query}: {count} times")

if __name__ == "__main__":
    generate_query_set()