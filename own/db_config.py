# Database Configuration for Online Compiler
# Update these values according to your MySQL setup

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': 'Admin@123',  # Change this to your MySQL password
    'database': 'online_compiler_auth',
    'charset': 'utf8mb4',
    'autocommit': True,
    'port': 3306  # Default MySQL port
}

# Test database connection
def test_connection():
    try:
        import mysql.connector
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Database connection successful!")
            print(f"📊 Connected to MySQL Server version: {connection.get_server_info()}")
            print(f"🗄️ Database: {DB_CONFIG['database']}")
            connection.close()
            return True
        else:
            print("❌ Failed to connect to database")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
