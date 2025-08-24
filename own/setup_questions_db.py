#!/usr/bin/env python3
"""
Setup script for the Questions Database
This script will create the questions database structure and populate it with sample data.
"""

import mysql.connector
from mysql.connector import Error
from db_config import DB_CONFIG
import os

def setup_questions_database():
    """Set up the questions database with schema and sample data"""
    
    print("🚀 Setting up Questions Database...")
    
    # Read the SQL schema file
    schema_file = "questions_schema.sql"
    if not os.path.exists(schema_file):
        print(f"❌ Schema file {schema_file} not found!")
        return False
    
    try:
        with open(schema_file, 'r') as f:
            sql_commands = f.read()
        
        # Split SQL commands by semicolon
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("✅ Connected to database successfully")
        
        # Execute each SQL command
        for i, command in enumerate(commands, 1):
            if command:
                try:
                    cursor.execute(command)
                    print(f"✅ Executed command {i}/{len(commands)}")
                except Error as e:
                    print(f"⚠️ Warning executing command {i}: {e}")
                    # Continue with other commands
        
        # Commit changes
        connection.commit()
        print("✅ All database changes committed successfully")
        
        # Verify the setup
        print("\n🔍 Verifying database setup...")
        
        # Check main categories
        cursor.execute("SELECT COUNT(*) FROM main_categories")
        main_cat_count = cursor.fetchone()[0]
        print(f"📊 Main Categories: {main_cat_count}")
        
        # Check subcategories
        cursor.execute("SELECT COUNT(*) FROM subcategories")
        sub_cat_count = cursor.fetchone()[0]
        print(f"📊 Sub Categories: {sub_cat_count}")
        
        # Check questions
        cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = cursor.fetchone()[0]
        print(f"📊 Questions: {questions_count}")
        
        # Show sample data
        print("\n📋 Sample Main Categories:")
        cursor.execute("SELECT name, description FROM main_categories")
        for name, desc in cursor.fetchall():
            print(f"  • {name}: {desc}")
        
        print("\n📋 Sample Sub Categories (Data Structure):")
        cursor.execute("""
            SELECT sc.name, sc.description 
            FROM subcategories sc 
            JOIN main_categories mc ON sc.main_category_id = mc.id 
            WHERE mc.name = 'DataStructure' 
            LIMIT 5
        """)
        for name, desc in cursor.fetchall():
            print(f"  • {name}: {desc}")
        
        print("\n📋 Sample Questions:")
        cursor.execute("""
            SELECT q.title, q.difficulty, mc.name as main_cat, sc.name as sub_cat
            FROM questions q
            JOIN main_categories mc ON q.main_category_id = mc.id
            JOIN subcategories sc ON q.subcategory_id = sc.id
            LIMIT 3
        """)
        for title, difficulty, main_cat, sub_cat in cursor.fetchall():
            print(f"  • {title} ({difficulty}) - {main_cat} > {sub_cat}")
        
        print("\n✅ Questions database setup completed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    print("=" * 50)
    print("🏗️  Questions Database Setup")
    print("=" * 50)
    
    success = setup_questions_database()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("You can now run the FastAPI server and use the question selection feature.")
    else:
        print("\n💥 Setup failed! Please check the error messages above.")
    
    print("=" * 50)
