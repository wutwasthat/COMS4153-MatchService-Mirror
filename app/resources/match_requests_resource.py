import asyncio
import uuid
from framework.resources.base_resource import BaseResource
from app.models.match_making_status import MatchMakingStatus
from app.models.match_request_initiate import MatchRequestInitiate
from app.models.match_request import MatchRequest, MatchRequests, MatchRequestWithLinks

from app.resources.favourites_resource import FavouritesResource

from framework.exceptions.match_exceptions import MatchNotFoundException,MatchNotValidException
from app.services.service_factory import ServiceFactory


class MatchRequestsResource(BaseResource):

    def __init__(self, config):
        super().__init__(config)

        # TODO -- Replace with dependency injection.
        #
        self.data_service = ServiceFactory.get_service("MatchResourceDataService")

        self.database = "Game"
        self.match_request_table = "match_request"
        self.matched_request_table = "matched_requests"
        self.key_field = "matchRequestId"

        self.data_service.initialize(self.database)

    def get_item(self, key: str) -> MatchRequestWithLinks:
        d_service = self.data_service

        record = d_service.get_data_object(
            self.database, self.match_request_table, key_field=self.key_field, key_value=key
        )
        result = self.populate_match_request_model(record)

        return result

    def get_list(self, userid: str, game_id: str, page: int, page_size: int) -> MatchRequests:
        d_service = self.data_service

        records = d_service.get_match_requests_records(userid, game_id, page, page_size)

        match_requests_result = self.populate_match_requests_response_model(records, page, page_size)

        return match_requests_result

    def create_match_request(self, match_request: MatchRequest) -> MatchRequest:

        match_request_id = str(uuid.uuid4())
        match_request.matchRequestId = match_request_id

        d_service = self.data_service
        is_successful = d_service.insert_data_object(self.database, self.match_request_table, match_request.dict())

        return match_request if is_successful else None

    def initiate_match_process(self, match_request_initiate: MatchRequestInitiate):

        try:
            match_request_id = match_request_initiate.MatchRequestId

            d_service = self.data_service
            # Fetch the match request from the DB
            match_request = d_service.get_data_object(self.database, self.match_request_table, self.key_field, match_request_id)

            if not match_request:
                raise MatchNotFoundException("Match request not found.")
            if match_request.get("isActive"):
                raise MatchNotValidException("Match request is already active.")

            # Update the match request to set it as active
            match_request["isActive"] = True

            # Use the new update_data_object method
            update_successful = d_service.update_data_object(self.database, self.match_request_table, self.key_field, match_request_id, match_request)

            if not update_successful:
                raise Exception("Failed to update match request.")

            return match_request["matchRequestId"]

        except Exception as e:
            raise Exception(e)

    def get_match_status(self, match_request_id) -> MatchMakingStatus:
        d_service = self.data_service
        match_request = d_service.get_data_object(self.database, self.match_request_table, self.key_field, match_request_id)

        if not match_request:
            return MatchMakingStatus(
                matchRequestId=match_request_id,
                status="not_found"
            )

        if match_request.get("isActive"):
            return MatchMakingStatus(
                matchRequestId=match_request_id,
                status="matching"
            )

        # Check if there is a matched request in the matched_requests table
        matched_request = d_service.get_data_object(self.database, self.matched_request_table, "matchRequestId1", match_request_id)

        if matched_request:
            return MatchMakingStatus(
                matchRequestId=match_request_id,
                status="matched",
                partnerRequestId=matched_request["matchRequestId2"]
            )

        # If no match is found, return the appropriate status
        return MatchMakingStatus(
            matchRequestId=match_request_id,
            status="not_found"
        )


    @staticmethod
    def populate_match_request_model(record):
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

    @staticmethod
    def populate_match_requests_response_model(records, page, page_size):
        match_request_models = []
        # Convert the records to MatchRequest objects
        for row in records:
            match_request_model = MatchRequestWithLinks(
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
            match_request_models.append(match_request_model)
        # Create response including pagination links
        response = MatchRequests(
            matchRequests=match_request_models,
            links={
                "self": {"href": f"/match-requests?page={page}&page_size={page_size}"},
                "next": {"href": f"/match-requests?page={page + 1}&page_size={page_size}"},
                "prev": {"href": f"/match-requests?page={page - 1}&page_size={page_size}"} if page > 1 else None
            }
        )
        return response

    # TODO: Fix race condition, when there are two valid matches
    # TODO: Move this to different file as helper
    async def process_matchmaking(self, match_request_id):
        """
        Process matchmaking for the given match request ID.
        This function will look for other active match requests for the same game
        and pair them together if a match is found.
        """
        try:
            d_service = self.data_service

            # Fetch the match request from the DB to get the game information
            match_request = d_service.get_data_object(self.database, self.match_request_table, self.key_field, match_request_id)

            if not match_request or not match_request.get("isActive"):
                print(f"No active match request found for ID: {match_request_id}. Exiting matchmaking process.")
                return

            game_id = match_request["gameId"]
            user_id = match_request["userId"]

            while True:
                await asyncio.sleep(5)  # Check for matches every 5 seconds

                # Fetch all active match requests for the same game
                active_matches = d_service.get_all_data_objects(self.database, self.match_request_table, 0, 100)  # Adjust limit as needed
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
                    partner_request_id = partner_request["matchRequestId"]

                    # Create a new entry in the matched database
                    matched_data = {
                        "matchRequestId1": match_request_id,
                        "matchRequestId2": partner_request_id,
                        "gameId": game_id,
                        "status": "matched"
                    }
                    print(matched_data)

                    # Insert the matched data into the database
                    res = d_service.insert_data_object(self.database, self.matched_request_table, matched_data)

                    if res:
                        print(f"Match found! {match_request_id} matched with {partner_request_id}")

                        # Update both match requests to set them as not active
                        match_request["isActive"] = False
                        partner_request["isActive"] = False
                        d_service.update_data_object(self.database, self.match_request_table, self.key_field, match_request_id, match_request)
                        d_service.update_data_object(self.database, self.match_request_table, self.key_field, partner_request_id, partner_request)

                        break  # Exit the while loop after a successful match
                else:
                    print(f"No match found for {match_request_id}. Continuing to search...")

        except Exception as e:
            print(f"Error during matchmaking process for {match_request_id}: {str(e)}")



