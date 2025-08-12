import mysql.connector
from mysql.connector import errorcode

# --- Configuration ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'SuperDB',
        'USER': 'sa',
        'PASSWORD': 'Welcome@123',
        'HOST': '192.168.48.201',
        'PORT': '3306',
    }
}

def check_mysql_connection():
    """
    Connects to the MySQL Server, fetches a few student records, and prints the status.
    """
    print("--- MySQL Connection Test ---")
    db_config = DATABASES['default']
    
    try:
        # 1. Attempt to connect to the database
        print(f"Attempting to connect to {db_config['HOST']}...")
        conn = mysql.connector.connect(
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            database=db_config['NAME'],
            port=db_config['PORT'],
            connection_timeout=5
        )
        print("✅ Connection Successful!")
        
        # 2. Attempt to fetch data
        print("\nFetching a few student records...")
        cursor = conn.cursor(dictionary=True)
        
        # Execute a query to get the top 5 valid student records
        cursor.execute("""
            SELECT ID, First_Name, Last_Name 
            FROM tbl_Student 
            WHERE ID IS NOT NULL AND First_Name IS NOT NULL AND Last_Name IS NOT NULL
            LIMIT 5
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("⚠️  Warning: Connection successful, but no student records were found.")
        else:
            print(f"✅ Data Fetched Successfully! Found {len(records)} records.")
            for row in records:
                print(f"  - ID: {row['ID']}, Name: {row['First_Name']} {row['Last_Name']}")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ DATABASE ERROR: Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"❌ DATABASE ERROR: Database '{db_config['NAME']}' does not exist")
        else:
            print(f"❌ DATABASE ERROR: {err}")
    except Exception as e:
        print(f"❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nConnection closed.")
        print("--- Test Complete ---")

if __name__ == "__main__":
    check_mysql_connection()
