import pymysql
from framework.services.DataAccess.MySQLDataService import MySQLDataService
from typing import Optional


class FavouritesDataService(MySQLDataService):

    def __init__(self, context):
        super().__init__(context)

    def initialize(self, database_name):
        """
        Creates the database and tables if they do not exist.
        """
        # Connect to MySQL server (without specifying a database)
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                # Create the database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")

        # Ensure connection to the specific database for table creation
        self.context["database"] = database_name  # Update context with database name

        # Create tables in the specified database
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"USE {database_name}")

                # Create the `favourites` table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS favourites (
                        favouriteId CHAR(36) PRIMARY KEY,
                        userId VARCHAR(255) NOT NULL,
                        gameId VARCHAR(255) NOT NULL
                    )
                """)
                connection.commit()

    def get_favourites(self, user_id: str, page: int, page_size: int):
        """Builds the SQL query based on filters and executes it, returning the results."""
        offset = (page - 1) * page_size
        params = []

        database = self.context["database"]

        base_query = f"SELECT gameId FROM {database}.favourites "
        base_query += "WHERE userId = %s"
        params.append(f"{user_id}")

        base_query += " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        return self.execute_query(base_query,params)