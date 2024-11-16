import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="urban_mobility"
        )
        print('connected to sql:)')
        return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None
    
connection = create_connection()

def fetch_data(query):

    if connection is not None:

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()

            for row in result:
                print(row)

            return result
        except Error as e:
            print(f"Error: '{e}'")
            return None
        finally:
            # Close cursor and connection
            cursor.close()
            connection.close()
        

query = "SELECT * FROM Users;"  # Replace 'your_table_name' with your actual table name
fetch_data(query)


'''// This file is generated temporarily, the configuration is not actually stored here.
{
  "database": {
    "1730620235749": {
      "host": "127.0.0.1",
      "port": 3306,
      "user": "root",
      "dbType": "MySQL",
      "advance": {
        "hideSystemSchema": true,
        "groupingTables": false
      },
      "treeFeatures": [],
      "timezone": "+00:00",
      "useConnectionString": false,
      "usingSSH": false,
      "useSocksProxy": false,
      "useHTTPProxy": false,
      "athena": {},
      "bigQuery": {},
      "global": true,
      "savePassword": "Forever",
      "readonly": false,
      "sort": 11,
      "useSSL": false,
      "fs": {
        "encoding": "utf8",
        "showHidden": true
      },
      "dm": {
        "usingServiceName": false
      },
      "httpAuth": {
        "authType": "none"
      },
      "key": "1730620235749",
      "connectionKey": "database.connections",
      "isJdbc": false,
      "requiredAuth": true
    }
  },
  "nosql": null,
  "$schema": "http://127.0.0.1:8828/schema.json"
}'''