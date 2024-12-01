from sqlalchemy import Column, String, Text, create_engine, text, Table, MetaData, or_, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import traceback
from typing import Optional


Base = declarative_base()
class GameInfo(Base):
    __tablename__ = 'game_info'
    __table_args__ = {'schema': 'Game'}  
    
    gameId = Column(String(36), primary_key=True)
    image = Column(String(255)) 
    title = Column(String(255))  
    description = Column(Text)  
    genre = Column(Text)       


class CloudDatabase:
    def __init__(self, context):
        self.engine = create_engine(
            f"mysql+pymysql://{context['user']}:{context['password']}@"
            f"{context['host']}:{context['port']}/{"Game"}",
            echo=True  #
        )
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def execute_raw_query(self, query, params=None):
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return result.fetchall()

    def insert_data(self, schema_name, table_name, data_object):
        metadata = MetaData(schema=schema_name)
        table = Table(
            table_name,
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
    
    def build_and_execute_query(self, title: Optional[str], gameId: Optional[str], page: int, page_size: int, genre: Optional[str]):
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
