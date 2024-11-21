import pymysql
from framework.services.DataAccess.MySQLDataService import MySQLDataService
from typing import Optional


class MatchRequestDataService(MySQLDataService):

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

                # Create the 'match_request' table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS match_request (
                        userId CHAR(36),
                        gameId CHAR(36),
                        matchRequestId CHAR(36) PRIMARY KEY,  -- Remove default UUID generation here
                        expireDate DATE,
                        isActive BOOL,
                        isCancelled BOOL
                    )
                """)

                # Create the `matched_requests` table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS matched_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        matchRequestId1 CHAR(36) NOT NULL,
                        matchRequestId2 CHAR(36) NOT NULL,
                        gameId CHAR(36) NOT NULL,
                        status ENUM('matched', 'completed', 'cancelled') NOT NULL DEFAULT 'matched',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (matchRequestId1) REFERENCES match_request(matchRequestId) ON DELETE CASCADE,
                        FOREIGN KEY (matchRequestId2) REFERENCES match_request(matchRequestId) ON DELETE CASCADE
                    )
                """)
                connection.commit()


    def get_match_requests_records(self, user_id: Optional[str], game_id: Optional[str], page: int, page_size: int):
        """
        Build and execute a SQL query to fetch match requests with optional filtering and pagination.

        :param self: self instance.
        :param user_id: Optional user ID to filter match requests.
        :param game_id: Optional game ID to filter match requests.
        :param page: The page number for pagination.
        :param page_size: The number of records per page.
        :return: A list of match requests.
        """
        offset = (page - 1) * page_size  # Calculate the offset for pagination

        database = self.context["database"]

        # Build the SQL query with optional filters
        base_query = "SELECT * FROM Games.match_request WHERE 1=1"

        params = []

        if user_id:
            base_query += " AND userId = %s"
            params.append(f"{user_id}")

        if game_id:
            base_query += " AND gameId = %s"
            params.append(f"{game_id}")

        base_query += " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        # Execute the query and return the results
        return self.execute_query(base_query, params)

