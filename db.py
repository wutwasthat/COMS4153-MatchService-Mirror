import os
import pymysql
from utils.db_helper import MySQLDataService
from typing import Optional

class Database:
    def __init__(self, context):
        """
        Initialize the database connection using the provided context.
        """
        self.context = context
        self.data_service = MySQLDataService(self.context)

    def initialize(self, database_name):
        """
        Creates the database and tables if they do not exist.
        """
        # Connect to MySQL server (without specifying a database)
        with self.data_service._get_connection() as connection:
            with connection.cursor() as cursor:
                # Create the database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")

        # Ensure connection to the specific database for table creation
        self.context["database"] = database_name  # Update context with database name
        
        # Create tables in the specified database
        with self.data_service._get_connection() as connection:
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
    
# Helper functions for using query params
def build_and_execute_query(db, title: Optional[str], gameId: Optional[str], page: int, page_size: int):
    """Builds the SQL query based on filters and executes it, returning the results."""
    # Calculate offset for pagination
    offset = (page - 1) * page_size
    
    # Build the SQL query with optional filters
    base_query = "SELECT * FROM Games.game_info WHERE 1=1"
    params = []
    
    if title:
        base_query += " AND title LIKE %s"
        params.append(f"%{title}%")
    
    if gameId:
        base_query += " AND gameId = %s"
        params.append(f"%{gameId}%")
    
    base_query += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    # Execute the query and return the results
    return db.data_service.execute_query(base_query, params)

def build_and_execute_match_request_query(db, userId: Optional[str], gameId: Optional[str], page: int, page_size: int):
    """
    Build and execute a SQL query to fetch match requests with optional filtering and pagination.
    
    :param db: The database instance.
    :param userId: Optional user ID to filter match requests.
    :param gameId: Optional game ID to filter match requests.
    :param page: The page number for pagination.
    :param page_size: The number of records per page.
    :return: A list of match requests.
    """
    offset = (page - 1) * page_size  # Calculate the offset for pagination

    # Build the SQL query with optional filters
    base_query = "SELECT * FROM Games.match_request WHERE 1=1"

    params = []

    if userId:
        base_query += " AND userId = %s"
        params.append(f"%{userId}%")
    
    if gameId:
        base_query += " AND gameId = %s"
        params.append(f"%{gameId}%")
    
    
    base_query += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    # Execute the query and return the results
    return db.data_service.execute_query(base_query, params)

    
  
        