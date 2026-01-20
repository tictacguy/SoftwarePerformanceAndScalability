#!/usr/bin/env python3
"""
Improved architecture with caching and connection pooling
"""
from fastapi import FastAPI, HTTPException
import asyncio
import aiofiles
import json
import time
from functools import lru_cache
import sqlite3
from threading import Lock
import uvicorn

class ConnectionPool:
    def __init__(self, db_path, pool_size=10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self.lock = Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.connections.append(conn)
    
    def get_connection(self):
        with self.lock:
            if self.connections:
                return self.connections.pop()
            else:
                # Create new connection if pool is empty
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                return conn
    
    def return_connection(self, conn):
        with self.lock:
            if len(self.connections) < self.pool_size:
                self.connections.append(conn)
            else:
                conn.close()

class ImprovedMovieDatabase:
    def __init__(self, db_path="movies.db"):
        self.pool = ConnectionPool(db_path)
        self._cache = {}
        self._cache_ttl = {}
        self.cache_duration = 300  # 5 minutes
    
    def _get_from_cache(self, key):
        if key in self._cache:
            if time.time() - self._cache_ttl[key] < self.cache_duration:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_ttl[key]
        return None
    
    def _set_cache(self, key, value):
        self._cache[key] = value
        self._cache_ttl[key] = time.time()
    
    def search_movies(self, query, limit=10):
        cache_key = f"search_{query}_{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT m.tconst, m.primary_title, m.start_year, m.runtime_minutes, 
                       m.genres, r.average_rating, r.num_votes
                FROM movies m
                LEFT JOIN ratings r ON m.tconst = r.tconst
                WHERE m.primary_title LIKE ?
                ORDER BY r.num_votes DESC
                LIMIT ?
            """
            cursor.execute(sql, (f"%{query}%", limit))
            result = cursor.fetchall()
            
            # Convert to list of dicts for JSON serialization
            result_list = [dict(row) for row in result]
            self._set_cache(cache_key, result_list)
            return result_list
        finally:
            self.pool.return_connection(conn)
    
    def get_movie_details(self, tconst):
        cache_key = f"movie_{tconst}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # Movie info
            cursor.execute("""
                SELECT m.*, r.average_rating, r.num_votes
                FROM movies m
                LEFT JOIN ratings r ON m.tconst = r.tconst
                WHERE m.tconst = ?
            """, (tconst,))
            movie = cursor.fetchone()
            
            if not movie:
                return None
            
            # Directors
            cursor.execute("""
                SELECT p.primary_name
                FROM directors d
                JOIN people p ON d.nconst = p.nconst
                WHERE d.tconst = ?
            """, (tconst,))
            directors = [row[0] for row in cursor.fetchall()]
            
            # Main actors
            cursor.execute("""
                SELECT p.primary_name, a.characters
                FROM actors a
                JOIN people p ON a.nconst = p.nconst
                WHERE a.tconst = ?
                ORDER BY a.ordering
                LIMIT 5
            """, (tconst,))
            actors = cursor.fetchall()
            
            result = {
                'tconst': movie['tconst'],
                'title': movie['primary_title'],
                'year': movie['start_year'],
                'runtime': movie['runtime_minutes'],
                'genres': movie['genres'],
                'rating': movie['average_rating'],
                'votes': movie['num_votes'],
                'directors': directors,
                'actors': [{'name': actor[0], 'character': actor[1]} for actor in actors]
            }
            
            self._set_cache(cache_key, result)
            return result
        finally:
            self.pool.return_connection(conn)

# Improved API with caching
app = FastAPI(title="Improved Movie Dashboard API")
db = ImprovedMovieDatabase()

@app.get("/")
def root():
    return {"message": "Improved Movie Dashboard API with Caching"}

@app.get("/search/{query}")
def search_movies(query: str, limit: int = 10):
    try:
        results = db.search_movies(query, limit)
        movies = []
        for row in results:
            movies.append({
                "tconst": row["tconst"] if isinstance(row, dict) else row[0],
                "title": row["primary_title"] if isinstance(row, dict) else row[1],
                "year": row["start_year"] if isinstance(row, dict) else row[2],
                "runtime": row["runtime_minutes"] if isinstance(row, dict) else row[3],
                "genres": row["genres"] if isinstance(row, dict) else row[4],
                "rating": row["average_rating"] if isinstance(row, dict) else row[5],
                "votes": row["num_votes"] if isinstance(row, dict) else row[6]
            })
        return {"query": query, "results": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/movie/{tconst}")
def get_movie(tconst: str):
    try:
        movie = db.get_movie_details(tconst)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "cache_size": len(db._cache)}

@app.get("/cache/stats")
def cache_stats():
    return {
        "cache_size": len(db._cache),
        "cache_keys": list(db._cache.keys())[:10]  # Show first 10 keys
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port