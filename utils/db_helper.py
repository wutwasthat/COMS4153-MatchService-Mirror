import pymysql

class MySQLDataService:
    """
    MySQL data service to interact with MySQL databases.
    """

    def __init__(self, context):
        self.context = context

    # General operations
    def _get_connection(self):
        return pymysql.connect(
            host=self.context["host"],
            port=self.context["port"],
            user=self.context["user"],
            password=self.context["password"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def get_data_object(self, database_name, collection_name, key_field, key_value):
        """Fetch a single record based on a unique key field."""
        sql_statement = f"SELECT * FROM {database_name}.{collection_name} WHERE {key_field} = %s"
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_statement, (key_value,))
                return cursor.fetchone()
            
    def get_all_data_objects(self, database_name, collection_name, offset, limit):
        """Fetch all records from a specified table with pagination."""
        sql_statement = f"SELECT * FROM {database_name}.{collection_name} LIMIT %s OFFSET %s"
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_statement, (limit, offset))
                return cursor.fetchall()
    
    def execute_query(self, query, params):
        """Execute a given SQL query with parameters and return the results."""
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()



    def insert_data_object(self, database_name, collection_name, data_object):
        """Insert a new record into a specified table."""
        columns = ', '.join(data_object.keys())
        placeholders = ', '.join(['%s'] * len(data_object))
        sql_statement = f"INSERT INTO {database_name}.{collection_name} ({columns}) VALUES ({placeholders})"
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_statement, tuple(data_object.values()))
                connection.commit()
                return cursor.rowcount > 0  # Returns True if the insertion was successful

    def update_data_object(self, database_name, collection_name, key_field, key_value, updated_data):
        """Update an existing record in a specified table based on a unique key field."""
        set_clause = ', '.join([f"{key} = %s" for key in updated_data.keys()])
        sql_statement = f"UPDATE {database_name}.{collection_name} SET {set_clause} WHERE {key_field} = %s"
        
        # Prepare the parameters for the query
        params = tuple(updated_data.values()) + (key_value,)
        
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_statement, params)
                connection.commit()
                return cursor.rowcount > 0  # Returns True if the update was successful
