from fastapi import FastAPI, HTTPException
from database import MovieDatabase
import uvicorn

app = FastAPI(title="Movie Dashboard API")
db = MovieDatabase()

@app.get("/")
def root():
    return {"message": "Movie Dashboard API"}

@app.get("/search/{query}")
def search_movies(query: str, limit: int = 10):
    """Search movies by title"""
    try:
        results = db.search_movies(query, limit)
        movies = []
        for row in results:
            movies.append({
                "tconst": row[0],
                "title": row[1],
                "year": row[2],
                "runtime": row[3],
                "genres": row[4],
                "rating": row[5],
                "votes": row[6]
            })
        return {"query": query, "results": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/movie/{tconst}")
def get_movie(tconst: str):
    """Get detailed movie information"""
    try:
        movie = db.get_movie_details(tconst)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint for load testing"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)