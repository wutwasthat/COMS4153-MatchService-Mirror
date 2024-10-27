# MySQL connection settings
# Cloud DB context
# db_context = {
#     "host": "w4153.cl9cloxvh1sk.us-east-1.rds.amazonaws.com",
#     "user": "root",
#     "password": "dbpassuser",
#     "port": 3306
# }
import requests
from fastapi import FastAPI, HTTPException, Query
from db import Database, build_and_execute_query, build_and_execute_match_request_query
from utils.igdb_helper import fetch_games_data
import os
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID
from model import GameWithLinks, GamesResponse, MatchRequest, MatchRequestResponse, MatchRequestWithLinks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime


app = FastAPI()

load_dotenv() # it loads from the .env file

# Create a context dictionary from environment variables
context = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Initialize the Database instance
db = Database(context)

# TODO: Check if game exists, then update the game instead of creating new entry
@app.on_event("startup")
# async def startup():
#     # Initialize the 'Games' database schema
#     print('Initialize the database...')
#     db.initialize('Games')  # Ensure the database and tables are created
#     print('Initialized both the tables in the database')
#     print("Fetching game data from IGDB and populating the database...")
#     games_info = fetch_games_data()
#     for game in games_info:
#         # Prepare the data object for insertion
#         data_object = {
#             "gameId": game["id"],
#             "title": game["name"],
#             "description": game["description"],
#             "image": game["image_url"]
#         }

#         # Insert the data object into the database
#         if db.data_service.insert_data_object("Games", "game_info", data_object):
#            pass
#         else:
#             print(f"Failed to insert game: {game['name']}")
#     print("Database population complete for table: games_info!")

@app.get("/health")
async def health():
    return {"message": "Service is up and running"}

# TODO: Fix genre population logic
# TODO: Add logic to filter based on genre
@app.get("/games", response_model=GamesResponse)
async def get_games(
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1),
    title: Optional[str] = None,
    gameId: Optional[str] = None):
    """
    Retrieve all games from the database.
    1) HATEOAS is implemented
    2) Proper response codes are implemented:
    - 500 for server error
    - 200 for OK
    3) Added Pagination logic
    4) Added filtering logic using query param for title
    """
    try:
        # Use the helper function to fetch filtered records
        records = build_and_execute_query(db, title, gameId, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching games from DB.")
    print("Fetched records from DB")
    try:        
        games_with_links = []
        # Convert the records to Game objects
        for row in records:
            game_with_links = GameWithLinks(
                gameId=row['gameId'],
                title=row['title'],
                description=row['description'],
                image=row['image'],
                links={
                    "self": {"href": f"/games/{row['gameId']}"},
                    "image": {"href": row['image'] or "No image available"}
                }
            )
            print(game_with_links)
            games_with_links.append(game_with_links)
        
        # Create response including pagination links
        response = GamesResponse(
            games=games_with_links,
            links={
                "self": {"href": f"/games?page={page}&page_size={page_size}"},
                "next": {"href": f"/games?page={page + 1}&page_size={page_size}"},
                "prev": {"href": f"/games?page={page - 1}&page_size={page_size}"} if page > 1 else None
            }
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing games.")

    
@app.get("/games/{game_id}", response_model=GameWithLinks)
async def get_game(game_id: str):
    record = db.data_service.get_data_object("Games", "game_info", "gameId", game_id)
    print(f"Fetched Game with game_id {game_id}: {record}")
    if not record:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        return GameWithLinks(
        gameId=record['gameId'],
        title=record['title'],
        description=record['description'],
        image=record['image'] if record['image'] else "No image available",
        links={
            "self": {"href": f"/games/{record['gameId']}"},
            "image": {"href": record['image'] or "No image available"}
        }
    )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the game.")
    

@app.post("/match-requests", response_model=MatchRequest, status_code=201)
async def create_match_request(match_request: MatchRequest):
    try:
        match_request_data = match_request.dict()
        match_request_id = str(uuid.uuid4())
        match_request_data['matchRequestId'] = match_request_id
        
        # Insert the match request into the database
        res = db.data_service.insert_data_object("Games", "match_request", match_request_data)

        # Check if successful
        if not res:
            raise HTTPException(status_code=500, detail="Failed to create match request in the database.")

        # Create the Location header
        location_header = f"/match-requests/{match_request_id}"

        # Return the created match request with a Location header
        response = JSONResponse(
            content=match_request_data,
            headers={"Location": location_header},
            status_code=201
        )
        print(response.headers)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/match-requests", response_model=MatchRequestResponse)
async def get_match_requests(
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1),
    userId: Optional[str] = None,
    gameId: Optional[str] = None):
    """
    Retrieve all match requests from the database.
    1) HATEOAS is implemented
    2) Proper response codes are implemented:
    - 500 for server error
    - 200 for OK
    3) Added Pagination logic
    4) Added filtering logic using query params for userId and gameId
    """
    try:
        # Use a helper function to fetch filtered records
        records = build_and_execute_match_request_query(db, userId, gameId, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching match requests from DB.")
    
    print("Fetched records from DB")
    try:        
        match_requests_with_links = []
        # Convert the records to MatchRequest objects
        for row in records:
            match_request_with_links = MatchRequestWithLinks(
                userId=row['userId'],
                gameId=row['gameId'],
                matchRequestId=row['matchRequestId'],
                expireDate=row['expireDate'].strftime("%Y-%m-%d"),
                isActive=row['isActive'],
                isCancelled=row['isCancelled'],
                links={
                    "self": {"href": f"/match-requests/{row['matchRequestId']}"}
                }
            )
            match_requests_with_links.append(match_request_with_links)
        # Create response including pagination links
        response = MatchRequestResponse(
            matchRequests=match_requests_with_links,
            links={
                "self": {"href": f"/match-requests?page={page}&page_size={page_size}"},
                "next": {"href": f"/match-requests?page={page + 1}&page_size={page_size}"},
                "prev": {"href": f"/match-requests?page={page - 1}&page_size={page_size}"} if page > 1 else None
            }
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing match requests.")

@app.get("/match-requests/{match_request_id}", response_model=MatchRequestWithLinks)
async def get_match_request(match_request_id: str):
    record = db.data_service.get_data_object("Games", "match_request", "matchRequestId", match_request_id)
    print(f"Fetched Match Request with match_request_id {match_request_id}: {record}")
    if not record:
        raise HTTPException(status_code=404, detail="match_request_id not found")
    try:
        return MatchRequestWithLinks(
                userId=record['userId'],
                gameId=record['gameId'],
                matchRequestId=record['matchRequestId'],
                expireDate=record['expireDate'].strftime("%Y-%m-%d"),
                isActive=record['isActive'],
                isCancelled=record['isCancelled'],
                links={
                    "self": {"href": f"/match-requests/{record['matchRequestId']}"}
                }
    )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the game.")