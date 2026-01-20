import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

class MovieDatabase:
    def __init__(self, db_path="movies.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create normalized database tables"""
        cursor = self.conn.cursor()
        
        # Movies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                tconst TEXT PRIMARY KEY,
                title_type TEXT,
                primary_title TEXT,
                original_title TEXT,
                is_adult INTEGER,
                start_year INTEGER,
                end_year INTEGER,
                runtime_minutes INTEGER,
                genres TEXT
            )
        """)
        
        # People table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                nconst TEXT PRIMARY KEY,
                primary_name TEXT,
                birth_year INTEGER,
                death_year INTEGER,
                primary_profession TEXT
            )
        """)
        
        # Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                tconst TEXT PRIMARY KEY,
                average_rating REAL,
                num_votes INTEGER,
                FOREIGN KEY (tconst) REFERENCES movies (tconst)
            )
        """)
        
        # Directors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors (
                tconst TEXT,
                nconst TEXT,
                PRIMARY KEY (tconst, nconst),
                FOREIGN KEY (tconst) REFERENCES movies (tconst),
                FOREIGN KEY (nconst) REFERENCES people (nconst)
            )
        """)
        
        # Actors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actors (
                tconst TEXT,
                nconst TEXT,
                ordering INTEGER,
                category TEXT,
                characters TEXT,
                PRIMARY KEY (tconst, nconst),
                FOREIGN KEY (tconst) REFERENCES movies (tconst),
                FOREIGN KEY (nconst) REFERENCES people (nconst)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_title ON movies (primary_title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_votes ON ratings (num_votes)")
        
        self.conn.commit()
    
    def import_data(self, data_dir="data"):
        """Import data from TSV files"""
        # Clear existing data from tables before importing
        cursor = self.conn.cursor()
        tables = ['actors', 'directors', 'ratings', 'movies', 'people']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()

        data_path = Path(data_dir)
        
        # Import movies
        print("Importing movies...")
        movies_df = pd.read_csv(data_path / "title.basics.tsv", sep='\t', na_values='\\N')
        movies_df = movies_df.rename(columns={
            'titleType': 'title_type',
            'primaryTitle': 'primary_title',
            'originalTitle': 'original_title',
            'isAdult': 'is_adult',
            'startYear': 'start_year',
            'endYear': 'end_year',
            'runtimeMinutes': 'runtime_minutes'
        })
        movies_df = movies_df[movies_df['title_type'].isin(['movie', 'tvMovie'])]  # Only movies
        movies_df.to_sql('movies', self.conn, if_exists='append', index=False)
        
        # Import people
        print("Importing people...")
        people_df = pd.read_csv(data_path / "name.basics.tsv", sep='\t', na_values='\\N')
        people_df = people_df.rename(columns={
            'primaryName': 'primary_name',
            'birthYear': 'birth_year',
            'deathYear': 'death_year',
            'primaryProfession': 'primary_profession'
        })
        # Select only the columns that exist in the 'people' table
        people_cols = ['nconst', 'primary_name', 'birth_year', 'death_year', 'primary_profession']
        people_df[people_cols].to_sql('people', self.conn, if_exists='append', index=False)
        
        # Import ratings
        print("Importing ratings...")
        ratings_df = pd.read_csv(data_path / "title.ratings.tsv", sep='\t', na_values='\\N')
        ratings_df = ratings_df.rename(columns={
            'averageRating': 'average_rating',
            'numVotes': 'num_votes'
        })
        ratings_df.to_sql('ratings', self.conn, if_exists='append', index=False)
        
        # Import directors
        print("Importing directors...")
        crew_df = pd.read_csv(data_path / "title.crew.tsv", sep='\t', na_values='\\N')
        crew_df = crew_df.dropna(subset=['directors'])
        # Explode the directors string into multiple rows
        directors_df = (crew_df[['tconst', 'directors']]
                        .assign(nconst=crew_df['directors'].str.split(','))
                        .explode('nconst')
                        .drop(columns=['directors']))
        
        if not directors_df.empty:
            directors_df.to_sql('directors', self.conn, if_exists='append', index=False)
        
        # Import actors
        print("Importing actors...")
        principals_df = pd.read_csv(data_path / "title.principals.tsv", sep='\t', na_values='\\N')
        actors_df = principals_df[principals_df['category'].isin(['actor', 'actress'])]
        # Sort by ordering and remove duplicates to handle actors playing multiple roles
        actors_df = actors_df.sort_values('ordering').drop_duplicates(subset=['tconst', 'nconst'], keep='first')
        # Rename columns to match the database schema
        actors_df = actors_df.rename(columns={
            'ordering': 'ordering',
            'category': 'category',
            'characters': 'characters'
        })
        actor_cols = ['tconst', 'nconst', 'ordering', 'category', 'characters']
        actors_df[actor_cols].to_sql('actors', self.conn, if_exists='append', index=False)
        
        self.conn.commit()
        print("Data import completed!")
    
    def search_movies(self, query, limit=10):
        """Search movies by title"""
        cursor = self.conn.cursor()
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
        return cursor.fetchall()
    
    def get_movie_details(self, tconst):
        """Get detailed movie information"""
        cursor = self.conn.cursor()
        
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
        
        return {
            'tconst': movie[0],
            'title': movie[2],
            'year': movie[5],
            'runtime': movie[7],
            'genres': movie[8],
            'rating': movie[9],
            'votes': movie[10],
            'directors': directors,
            'actors': [{'name': actor[0], 'character': actor[1]} for actor in actors]
        }
    
    def get_movies_by_votes(self):
        """Get all movies with their vote counts for query generation"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.primary_title, r.num_votes
            FROM movies m
            JOIN ratings r ON m.tconst = r.tconst
            WHERE r.num_votes > 0
        """)
        return cursor.fetchall()