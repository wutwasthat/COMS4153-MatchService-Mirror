
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.resources.games_resource import GamesResource


from app.routers import games, match_requests, favourites

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# it loads from the .env file
load_dotenv()

app.include_router(games.router)
app.include_router(match_requests.router)
app.include_router(favourites.router)

@app.get("/health")
async def health():
    return {"message": "Service is up and running"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)



# # TODO: Check if game exists, then update the game instead of creating new entry
# @app.on_event("startup")
# async def startup():
#     # Initialize the 'Games' database schema
#     print('Initialize the database...')
#     db.initialize('Games')  # Ensure the database and tables are created
#     print('Initialized all the tables in the database')
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
#
#         # Insert the data object into the database
#         if db.data_service.insert_data_object("Games", "game_info", data_object):
#            pass
#         else:
#             print(f"Failed to insert game: {game['name']}")
#     print("Database population complete for table: games_info!")

