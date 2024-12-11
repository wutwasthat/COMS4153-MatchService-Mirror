from typing import Any

from framework.resources.base_resource import BaseResource
import uuid
from app.models.game import Game
from app.models.favourite import Favourite, Favourites

from app.services.service_factory import ServiceFactory


class FavouritesResource(BaseResource):

    def __init__(self, config):
        super().__init__(config)

        # TODO -- Replace with dependency injection.
        #
        self.data_service = ServiceFactory.get_service("FavouriteResourceDataService")

        self.database = "Game"
        self.table = "favourites"
        self.key_field = "favouriteId"

        self.data_service.initialize(self.database)

    def get_item(self, key: str) -> Favourite:
        d_service = self.data_service

        record = d_service.get_data_object(
            self.database, self.table, key_field=self.key_field, key_value=key
        )
        result = self.populate_favourite_model(record)

        return result


    def get_list(self, user_id: str, page:int, page_size:int) -> Favourites:
        d_service = self.data_service

        game_ids = d_service.get_favourites(user_id, page, page_size)

        favourite_games = []
        game_table = 'game_info'
        game_key = 'gameId'

        for game_id in game_ids:
            game = d_service.get_data_object(self.database, game_table, key_field=game_key, key_value=game_id['gameId'])
            game_model = self.populate_game_model(game)
            favourite_games.append(game_model)

        favourites = Favourites(games = favourite_games)

        return favourites

    def add_to_favourite(self, favourite: Favourite) -> Favourite:
        favourite_id = str(uuid.uuid4())
        favourite.favouriteId = favourite_id

        d_service = self.data_service
        is_successful = d_service.insert_data_object(self.database, self.table, favourite.dict())

        return favourite if is_successful else None

    @staticmethod
    def populate_favourite_model(record):
        return Favourite(
            favourite_id=record['favouriteId'],
            user_id=record['userId'],
            game_id=record['gameId']
        )

    @staticmethod
    def populate_game_model(record):
        return Game(
            gameId=record['gameId'],
            title=record['title'],
            description=record['description'],
            image=record['image'] if record['image'] else "No image available",
            links={
                "self": {"href": f"/games/{record['gameId']}"},
                "image": {"href": record['image'] or "No image available"}
            }
        )

