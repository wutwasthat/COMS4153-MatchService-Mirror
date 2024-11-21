import pymysql
from framework.services.DataAccess.MySQLDataService import MySQLDataService
from typing import Optional


class GamesDataService(MySQLDataService):

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

                # Create the `game_info` table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS game_info (
                        gameId CHAR(36) PRIMARY KEY,  -- Remove default UUID generation here
                        image VARCHAR(255),
                        title VARCHAR(255),
                        description TEXT,
                        genre TEXT
                    )
                """)
                connection.commit()

    def get_game_records(self, title: Optional[str], game_id: Optional[str], page: int, page_size: int):
        """Builds the SQL query based on filters and executes it, returning the results."""
        # Calculate offset for pagination
        offset = (page - 1) * page_size

        database = self.context["database"]

        # Build the SQL query with optional filters
        base_query = "SELECT * FROM Games.game_info WHERE 1=1"
        params = []

        if title:
            base_query += " AND title LIKE %s"
            params.append(f"%{title}%")

        if game_id:
            base_query += " AND gameId = %s"
            params.append(f"%{game_id}%")

        base_query += " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        # Execute the query and return the results
        return self.execute_query(base_query, params)