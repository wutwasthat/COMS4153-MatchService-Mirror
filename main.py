# MySQL connection settings
# Cloud DB context
# db_context = {
#     "host": "w4153.cl9cloxvh1sk.us-east-1.rds.amazonaws.com",
#     "user": "root",
#     "password": "dbpassuser",
#     "port": 3306
# }
import requests
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from db import CloudDatabase
from utils.igdb_helper import fetch_games_data
import os
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID
from model import GameWithLinks, GamesResponse, MatchRequest, MatchRequestResponse, MatchRequestWithLinks, MatchRequestInitiate, MatchmakingStatus
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv() # it loads from the .env file

# Create a context dictionary from environment variables
context = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Initialize the Database instance
db = CloudDatabase(context)

# TODO: Check if game exists, then update the game instead of creating new entry
@asynccontextmanager
async def lifespan(app: FastAPI):
    # # Startup logic
    # print('Initialize the database...')
    # print('Initialized all the tables in the database')
    # print("Fetching game data from IGDB and populating the database...")
    # games_info = fetch_games_data()
    # for game in games_info:
    #     data_object = {
    #         "gameId": str(game["id"]),
    #         "title": game["name"],
    #         "description": game["description"],
    #         "image": game["image_url"],
    #         "genre": ",".join(game["genres"])
    #     }
    #     if not db.insert_data("Game", "game_info", data_object):
    #         print(f"Failed to insert game: {game['name']}")
    # print("Database population complete for table: games_info!")

    yield

app.router.lifespan_context = lifespan

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
    gameId: Optional[str] = None,
    genre: Optional[str] = None):
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
        records, has_next_page = db.build_and_execute_query(title, gameId, page, page_size, genre)
    except Exception as e:
        print(f"Error fetching records: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching games from DB.")
    print("Fetched records from DB")
    try:       
        games_with_links = []
        # Convert the records to Game objects
        for row in records:
            game_with_links = GameWithLinks(
                gameId=row.gameId,
                title=row.title,
                description=row.description,
                image=row.image if row.image else "No image available",
                genre=row.genre,
                links={
                    "self": {"href": f"/games/{row.gameId}"},
                    "image": {"href": row.image or "No image available"}
                }
            )
            # print(game_with_links)
            games_with_links.append(game_with_links)
        
        # Create response including pagination links
        response = GamesResponse(
            games=games_with_links,
            links={
                "self": {"href": f"/games?page={page}&page_size={page_size}"},
                "next": {"href": f"/games?page={page + 1}&page_size={page_size}"} if has_next_page else None,
                "prev": {"href": f"/games?page={page - 1}&page_size={page_size}"} if page > 1 else None
            }
        )
        
        return response
    except Exception as e:
        print(f"Error processing records: {str(e)}")
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
    
# TODO: Add validation if that match exists
# TODO: Add validation if that game is valid - Can be done by the composite service
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
    
@app.post("/match-requests/match", status_code=202)
async def initiate_match(
    match_request_initiate: MatchRequestInitiate,
    background_tasks: BackgroundTasks
):
    match_request_id = match_request_initiate.MatchRequestId
    try:
        # Fetch the match request from the DB
        match_request = db.data_service.get_data_object("Games", "match_request", "matchRequestId", match_request_id)

        if not match_request:
            raise HTTPException(status_code=404, detail="Match request not found.")
        if match_request.get("isActive"):
            raise HTTPException(status_code=400, detail="Match request is already active.")

        # Update the match request to set it as active
        match_request["isActive"] = True

        # Use the new update_data_object method
        update_successful = db.data_service.update_data_object("Games", "match_request", "matchRequestId", match_request_id, match_request)

        if not update_successful:
            raise HTTPException(status_code=500, detail="Failed to update match request.")

        # Initiate the asynchronous matchmaking process
        background_tasks.add_task(process_matchmaking, match_request_id)

        # Return a 202 response with a polling URL
        polling_url = f"/match-requests/status/{match_request_id}"
        return JSONResponse(
            content={
                "message": "Matchmaking request accepted. Poll status at the specified URL.",
                "matchRequestId": match_request_id,
                "polling_url": polling_url
            },
            status_code=202
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/match/status/{match_request_id}", response_model=MatchmakingStatus)
async def get_matchmaking_status(match_request_id: str):
    try:
        # Fetch the match request from the database to check its status
        match_request = db.data_service.get_data_object("Games", "match_request", "matchRequestId", match_request_id)

        if not match_request:
            return MatchmakingStatus(
                matchRequestId=match_request_id,
                status="not_found"
            )

        if match_request.get("isActive"):
            return MatchmakingStatus(
                matchRequestId=match_request_id,
                status="matching"
            )

        # Check if there is a matched request in the matched_requests table
        matched_request = db.data_service.get_data_object("Games", "matched_requests", "matchRequestId1", match_request_id)

        if matched_request:
            return MatchmakingStatus(
                matchRequestId=match_request_id,
                status="matched",
                partnerRequestId=matched_request["matchRequestId2"]
            )

        # If no match is found, return the appropriate status
        return MatchmakingStatus(
            matchRequestId=match_request_id,
            status="not_found"
        )

    except Exception as e:
        print(f"Error fetching matchmaking status for {match_request_id}: {str(e)}")
        return MatchmakingStatus(
            matchRequestId=match_request_id,
            status="error"
        )


# TODO: Fix race condition, when there are two valid matches
# TODO: Move this to different file as helper
async def process_matchmaking(match_request_id):
    """
    Process matchmaking for the given match request ID.
    This function will look for other active match requests for the same game
    and pair them together if a match is found.
    """
    try:
        # Fetch the match request from the DB to get the game information
        match_request = db.data_service.get_data_object("Games", "match_request", "matchRequestId", match_request_id)

        if not match_request or not match_request.get("isActive"):
            print(f"No active match request found for ID: {match_request_id}. Exiting matchmaking process.")
            return

        game_id = match_request["gameId"] 
        user_id = match_request["userId"]

        while True:
            await asyncio.sleep(5)  # Check for matches every 5 seconds

            # Fetch all active match requests for the same game
            active_matches = db.data_service.get_all_data_objects("Games", "match_request", 0, 100)  # Adjust limit as needed
            print(active_matches)
            matched_requests = [
                req for req in active_matches 
                if (req["gameId"] == game_id and 
                    req["matchRequestId"] != match_request_id and 
                    req.get("isActive") and 
                    req["userId"] != user_id)  # Ensure user IDs are not the same
            ]
            print(matched_requests)

            if matched_requests:
                # Pair the current match request with the first matching request found
                partner_request = matched_requests[0]

                # Create a new entry in the matched database
                matched_data = {
                    "matchRequestId1": match_request_id,
                    "matchRequestId2": partner_request["matchRequestId"],
                    "gameId": game_id,
                    "status": "matched"
                }
                print(matched_data)
                
                # Insert the matched data into the database
                res = db.data_service.insert_data_object("Games", "matched_requests", matched_data)

                if res:
                    print(f"Match found! {match_request_id} matched with {partner_request['matchRequestId']}")
                    
                    # Update both match requests to set them as not active
                    match_request["isActive"] = False
                    partner_request["isActive"] = False
                    db.data_service.update_data_object("Games", "match_request", "matchRequestId", match_request_id, match_request)
                    db.data_service.update_data_object("Games", "match_request", "matchRequestId", partner_request["matchRequestId"], partner_request)

                    break  # Exit the while loop after a successful match
            else:
                print(f"No match found for {match_request_id}. Continuing to search...")

    except Exception as e:
        print(f"Error during matchmaking process for {match_request_id}: {str(e)}")
