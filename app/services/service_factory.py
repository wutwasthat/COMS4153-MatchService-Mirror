import os
from framework.services.service_factory import BaseServiceFactory
import app.resources.games_resource as games_resource
import app.resources.match_requests_resource as match_requests_resource
from app.services.DataAccess.GamesDataService import GamesDataService
from app.services.DataAccess.MatchRequestDataService import MatchRequestDataService


class ServiceFactory(BaseServiceFactory):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_service(cls, service_name):
        #
        # TODO -- The terrible, hardcoding and hacking continues.
        #
        context = {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

        if service_name == 'GamesResource':
            result = games_resource.GamesResource(config=None)
        elif service_name == 'MatchRequestsResource':
            result = match_requests_resource.MatchRequestsResource(config=None)

        elif service_name == 'GamesResourceDataService':
            data_service = GamesDataService(context=context)
            result = data_service
        elif service_name == 'MatchResourceDataService':
            data_service = MatchRequestDataService(context=context)
            result = data_service

        else:
            result = None

        return result