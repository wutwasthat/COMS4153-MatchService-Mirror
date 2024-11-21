import uuid
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.match_request import MatchRequest, MatchRequests, MatchRequestWithLinks
from app.models.match_request_initiate import MatchRequestInitiate
from app.models.match_making_status import MatchMakingStatus
from app.services.service_factory import ServiceFactory
from framework.exceptions.match_exceptions import MatchNotValidException, MatchNotFoundException

router = APIRouter()

@router.get("/match-requests/{match_request_id}", response_model=MatchRequestWithLinks)
async def get_match_request(match_request_id: str):
    try:
        res = ServiceFactory.get_service("MatchRequestsResource")
        record = res.get_item(match_request_id)

        if not record:
            raise HTTPException(status_code=404, detail="match_request_id not found")

        print(f"Fetched Match Request with match_request_id {match_request_id}: {record}")

        return record

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching the game.")


@router.get("/match-requests", response_model=MatchRequests)
async def get_match_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    user_id: Optional[str] = None,
    game_id: Optional[str] = None):
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

        res = ServiceFactory.get_service("MatchRequestsResource")
        records = res.get_list(user_id, game_id, page, page_size)

        return records

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching games from DB.")


# TODO: Add validation if that match exists
# TODO: Add validation if that game is valid - Can be done by the composite service
@router.post("/match-requests", response_model=MatchRequest, status_code=201)
async def create_match_request(match_request: MatchRequest):
    try:

        res = ServiceFactory.get_service("MatchRequestsResource")
        record = res.create_match_request(match_request)

        if not record:
            raise HTTPException(status_code=500, detail="Failed to create match request in the database.")

        # Create the Location header
        location_header = f"/match-requests/{record.matchRequestId}"

        # Return the created match request with a Location header
        response = JSONResponse(
            content=record.dict(),
            headers={"Location": location_header},
            status_code=201
        )
        print(response.headers)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-requests/match", status_code=202)
async def initiate_match(
    match_request_initiate: MatchRequestInitiate,
    background_tasks: BackgroundTasks ):
    try:

        res = ServiceFactory.get_service("MatchRequestsResource")
        match_request_id = res.initiate_match_process(match_request_initiate)

        background_tasks.add_task(res.process_matchmaking, match_request_id)
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
    except MatchNotFoundException:
        raise HTTPException(status_code=404, detail="Match request not found.")

    except MatchNotValidException:
        raise HTTPException(status_code=400, detail="Match request is already active.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/match/status/{match_request_id}", response_model=MatchMakingStatus)
async def get_matchmaking_status(match_request_id: str):
    try:
        # Fetch the match request from the database to check its status
        res = ServiceFactory.get_service("MatchRequestsResource")
        response = res.get_match_status(match_request_id)

        return response

    except Exception as e:
        print(f"Error fetching matchmaking status for {match_request_id}: {str(e)}")
        return MatchMakingStatus(
            matchRequestId=match_request_id,
            status="error"
        )