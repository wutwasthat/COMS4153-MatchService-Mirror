from framework.resources.base_resource import BaseResource
from app.models.game import Game, Games
from app.resources.match_requests_resource import MatchRequestsResource
from app.services.service_factory import ServiceFactory


class GamesResource(BaseResource):

    def __init__(self, config):
        super().__init__(config)

        # TODO -- Replace with dependency injection.
        #
        self.data_service = ServiceFactory.get_service("GamesResourceDataService")
        self.data_service.initialize()


    def get_item(self, key: str) -> Game:
        d_service = self.data_service

        record = d_service.get_data_object(
            self.database, self.collection, key_field=self.key_field, key_value=key
        )
        result = self.populate_game_model(record)

        return result

    def get_list(self, title:str, game_id:str, page:int, page_size:int, genre: str = None) -> Games:
        d_service = self.data_service

        records, has_next_page = d_service.get_game_records(title, game_id, page, page_size, genre)

        games_result = self.populate_games_response_model(records, page, page_size, has_next_page)

        return games_result

    @staticmethod
    def populate_game_model(record):
        return Game(
                    gameId=record.gameId,
                    title=record.title,
                    description=record.description,
                    image=record.image if record.image else "No image available",
                    links={
                        "self": {"href": f"/games/{record.gameId}"},
                        "image": {"href": record.image or "No image available"}
                    }
        )

    @staticmethod
    def populate_games_response_model(records, page, page_size, has_next_page):

        game_models = []

        # Convert the records to Game objects
        for row in records:
            game_model = Game(
                gameId=row.gameId,
                title=row.title,
                description=row.description,
                image=row.image,
                links={
                    "self": {"href": f"/games/{row.gameId}"},
                    "image": {"href": row.image or "No image available"}
                }
            )
            game_models.append(game_model)

        # Create response including pagination links
        response = Games(
            games=game_models,
            links={
                "self": {"href": f"/games?page={page}&page_size={page_size}"},
                "next": {"href": f"/games?page={page + 1}&page_size={page_size}"} if has_next_page else None,
                "prev": {"href": f"/games?page={page - 1}&page_size={page_size}"} if page > 1 else None
            }
        )

        return response

