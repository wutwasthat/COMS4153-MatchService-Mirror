from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.favourite import Favourite, Favourites
from app.services.service_factory import ServiceFactory

router = APIRouter()

@router.post("/favourite", response_model=Favourite, status_code=201)
async def add_favourite(favourite: Favourite):
    try:

        res = ServiceFactory.get_service("FavouritesResource")
        record = res.add_to_favourite(favourite)

        if not record:
            raise HTTPException(status_code=500, detail="Failed to create match request in the database.")


        # Return the created match request with a Location header
        response = JSONResponse(
            content=record.dict(),
            status_code=201
        )
        print(response.headers)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favourites/{user_id}", response_model=Favourites)
async def get_favourites(user_id: str,
                         page: int = Query(1, ge=1),
                         page_size: int = Query(10, ge=1),):
    try:
        res = ServiceFactory.get_service("FavouritesResource")
        favourites = res.get_list(user_id, page, page_size)

        return favourites

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching favourites from DB.")