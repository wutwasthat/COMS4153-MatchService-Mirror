from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.models.game import Game, Games, FavGameRequest
from app.services.service_factory import ServiceFactory

router = APIRouter()

@router.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    try:
        res = ServiceFactory.get_service("GamesResource")
        record = res.get_item(game_id)

        if not record:
            raise HTTPException(status_code=404, detail="Game not found")

        print(f"Fetched Game with game_id {game_id}: {record}")
        return record

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the game.")

# TODO: Fix genre population logic
# TODO: Add logic to filter based on genre

@router.get("/games", response_model=Games)
async def get_games(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        title: Optional[str] = None,
        game_id: Optional[str] = None,
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

        res = ServiceFactory.get_service("GamesResource")
        records = res.get_list(title, game_id, page, page_size, genre)
        return records

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching games from DB.")

@router.get("/games/{game_name}", response_model=Games)
async def get_games_by_name(game_name: str):
    return get_games(title=game_name)

#TODO: This belongs to user profile service need to move it later to users service repo
@router.put("/games/{user_id}/{game_id}")
async def update_fav_game(user_id: str, game_id: str):
    data_object = FavGameRequest(user_id=user_id, game_id=game_id).to_db()
    res = ServiceFactory.get_service("GamesResource")
    try:
        if not res.data_service.insert_data_object("UserProfile", "user_favored_games", data_object):
            raise HTTPException(status_code=500, detail="Failed to update game in the database.")
        return {"message": "Game updated successfully."}
    except Exception as e:
        print(f"Error updating fav game: {str(e)}")


