#!/usr/bin/env python3
"""
Script to set up the database and import data from TSV files
"""
from database import MovieDatabase

def main():
    print("Setting up movie database...")
    db = MovieDatabase()
    
    print("Importing data from TSV files...")
    db.import_data("data")
    
    print("Database setup completed!")
    
    # Test the database
    print("\nTesting database with a sample search...")
    results = db.search_movies("Matrix", 3)
    for result in results:
        print(f"- {result[1]} ({result[2]})")

if __name__ == "__main__":
    main()