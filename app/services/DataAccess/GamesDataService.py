from framework.services.DataAccess.MySQLDataService import MySQLDataService
from typing import Optional
from sqlalchemy import create_engine, or_, MetaData, Table
from sqlalchemy.orm import sessionmaker
from typing import Optional
from app.models.game import GameInfo
import traceback


class GamesDataService(MySQLDataService):
    def __init__(self, context):
        super().__init__(context)

    def initialize(self):
        """
        Creates the database and tables if they do not exist.
        """
        self.engine = create_engine(
            f"mysql+pymysql://{self.context['user']}:{self.context['password']}@"
            f"{self.context['host']}:{self.context['port']}/{"Game"}",
            echo=True  #
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()

    def get_game_records(self, title: Optional[str], gameId: Optional[str], page: int, page_size: int, genre: Optional[str]):
        offset = (page - 1) * page_size
        session = self.get_session()
        query = session.query(GameInfo)

        if title:
            query = query.filter(GameInfo.title.like(f"%{title}%"))

        if gameId:
            query = query.filter(GameInfo.gameId == gameId)

        genres_list = ["arcade", "shooter", "platform", "adventure", "fighting", "puzzle"]
        if genre and genre.lower() != "other":
            query = query.filter(GameInfo.genre.ilike(f"%{genre}%"))
        elif genre and genre.lower() == "other":
            exclude_conditions = [GameInfo.genre.ilike(f"%{g}%") for g in genres_list]
            query = query.filter(~or_(*exclude_conditions))

        results = query.limit(page_size + 1).offset(offset).all()
        has_next_page = len(results) > page_size
        results = results[:page_size]
        return results, has_next_page
    
    def insert_data_object(self, database_name, collection_name, data_object):
        metadata = MetaData(schema=database_name)
        print(f"Inserting data into table: {collection_name}")
        print(self.engine)
        print("!!!!!")
        table = Table(
            collection_name,
            metadata,
            autoload_with=self.engine 
        )
        try:
            with self.engine.connect() as connection:
                insert_stmt = table.insert().values(**data_object) 
                connection.execute(insert_stmt)
                connection.commit()
            return True
        except Exception as e:
            print(f"Failed to insert data: {e}")
            traceback.print_exc() 
            return False