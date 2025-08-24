#!/usr/bin/env python3
"""
Robust Database Setup Script
This script will set up the database step by step, handling missing tables gracefully.
"""

import mysql.connector
from mysql.connector import Error
from db_config import DB_CONFIG
import os

def setup_database_robust():
    """Set up the database step by step"""
    
    print("🚀 Setting up Online Compiler Database (Robust Mode)...")
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("✅ Connected to database successfully")
        
        # Step 1: Create users table
        print("\n📋 Step 1: Creating users table...")
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            cursor.execute(create_users_table)
            print("✅ Users table created/verified")
        except Error as e:
            print(f"⚠️  Users table warning: {e}")
        
        # Step 2: Create main_categories table
        print("\n📋 Step 2: Creating main_categories table...")
        create_main_categories = """
        CREATE TABLE IF NOT EXISTS main_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        try:
            cursor.execute(create_main_categories)
            print("✅ Main categories table created/verified")
        except Error as e:
            print(f"⚠️  Main categories table warning: {e}")
        
        # Step 3: Create subcategories table
        print("\n📋 Step 3: Creating subcategories table...")
        create_subcategories = """
        CREATE TABLE IF NOT EXISTS subcategories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            main_category_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (main_category_id) REFERENCES main_categories(id) ON DELETE CASCADE,
            UNIQUE KEY unique_subcategory (main_category_id, name)
        )
        """
        
        try:
            cursor.execute(create_subcategories)
            print("✅ Subcategories table created/verified")
        except Error as e:
            print(f"⚠️  Subcategories table warning: {e}")
        
        # Step 4: Create questions table
        print("\n📋 Step 4: Creating questions table...")
        create_questions = """
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            content LONGTEXT NOT NULL,
            main_category_id INT NOT NULL,
            subcategory_id INT NOT NULL,
            difficulty ENUM('Easy', 'Medium', 'Hard') DEFAULT 'Medium',
            tags JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (main_category_id) REFERENCES main_categories(id) ON DELETE CASCADE,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE CASCADE,
            INDEX idx_category (main_category_id, subcategory_id),
            INDEX idx_difficulty (difficulty)
        )
        """
        
        try:
            cursor.execute(create_questions)
            print("✅ Questions table created/verified")
        except Error as e:
            print(f"⚠️  Questions table warning: {e}")
        
        # Step 5: Insert main categories
        print("\n📋 Step 5: Inserting main categories...")
        try:
            cursor.execute("SELECT COUNT(*) FROM main_categories")
            if cursor.fetchone()[0] == 0:
                insert_main_categories = """
                INSERT INTO main_categories (name, description) VALUES
                ('DataStructure', 'Data Structure problems including arrays, linked lists, trees, graphs, etc.'),
                ('SystemDesign', 'System Design problems including distributed systems, databases, scalability, etc.')
                """
                cursor.execute(insert_main_categories)
                print("✅ Main categories inserted")
            else:
                print("✅ Main categories already exist")
        except Error as e:
            print(f"⚠️  Main categories insertion warning: {e}")
        
        # Step 6: Insert subcategories
        print("\n📋 Step 6: Inserting subcategories...")
        try:
            cursor.execute("SELECT COUNT(*) FROM subcategories")
            if cursor.fetchone()[0] == 0:
                # Data Structure subcategories
                insert_ds_subcategories = """
                INSERT INTO subcategories (main_category_id, name, description) VALUES
                (1, 'Array', 'Array-based problems and algorithms'),
                (1, 'String', 'String manipulation and algorithms'),
                (1, 'Linked List', 'Linked list data structure problems'),
                (1, 'Stack', 'Stack data structure and applications'),
                (1, 'Queue', 'Queue data structure and applications'),
                (1, 'Tree', 'Tree data structure problems'),
                (1, 'Graph', 'Graph algorithms and problems'),
                (1, 'Hash Table', 'Hash table and hash map problems'),
                (1, 'Heap', 'Heap data structure and priority queue'),
                (1, 'Dynamic Programming', 'Dynamic programming problems')
                """
                cursor.execute(insert_ds_subcategories)
                
                # System Design subcategories
                insert_sd_subcategories = """
                INSERT INTO subcategories (main_category_id, name, description) VALUES
                (2, 'Distributed Systems', 'Distributed system design problems'),
                (2, 'Database Design', 'Database schema and query optimization'),
                (2, 'Caching', 'Caching strategies and implementations'),
                (2, 'Load Balancing', 'Load balancing algorithms and strategies'),
                (2, 'Microservices', 'Microservices architecture design'),
                (2, 'Scalability', 'System scalability and performance'),
                (2, 'Security', 'System security and authentication'),
                (2, 'API Design', 'REST API and GraphQL design'),
                (2, 'Message Queues', 'Message queue and event streaming'),
                (2, 'Monitoring', 'System monitoring and observability')
                """
                cursor.execute(insert_sd_subcategories)
                print("✅ Subcategories inserted")
            else:
                print("✅ Subcategories already exist")
        except Error as e:
            print(f"⚠️  Subcategories insertion warning: {e}")
        
        # Step 7: Insert sample questions
        print("\n📋 Step 7: Inserting sample questions...")
        try:
            cursor.execute("SELECT COUNT(*) FROM questions")
            if cursor.fetchone()[0] == 0:
                # Insert sample questions for Array
                insert_array_questions = """
                INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
                ('Two Sum', 'Find two numbers in an array that add up to a target value', 
                '# Two Sum Problem

Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

## Example 1:
<div class="example">
**Input:** nums = [2,7,11,15], target = 9  
**Output:** [0,1]  
**Explanation:** Because nums[0] + nums[1] == 9, we return [0, 1].
</div>

## Constraints:
<div class="constraints">
• 2 ≤ nums.length ≤ 10^4  
• -10^9 ≤ nums[i] ≤ 10^9  
• Only one valid answer exists.
</div>', 1, 1, 'Easy', '["array", "hash-table", "two-pointers"]'),

                ('Maximum Subarray', 'Find the contiguous subarray with the largest sum', 
                '# Maximum Subarray Problem

Given an integer array `nums`, find the contiguous subarray with the largest sum.

## Example 1:
<div class="example">
**Input:** nums = [-2,1,-3,4,-1,2,1,-5,4]  
**Output:** 6  
**Explanation:** The subarray [4,-1,2,1] has the largest sum 6.
</div>

## Constraints:
<div class="constraints">
• 1 ≤ nums.length ≤ 3 * 10^4  
• -10^5 ≤ nums[i] ≤ 10^5
</div>', 1, 1, 'Medium', '["array", "divide-and-conquer", "dynamic-programming"]')
                """
                cursor.execute(insert_array_questions)
                
                # Insert sample questions for String
                insert_string_questions = """
                INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
                ('Valid Palindrome', 'Check if a string is a valid palindrome', 
                '# Valid Palindrome Problem

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

## Example 1:
<div class="example">
**Input:** s = "A man, a plan, a canal: Panama"  
**Output:** true  
**Explanation:** "amanaplanacanalpanama" is a palindrome.
</div>

## Constraints:
<div class="constraints">
• 1 ≤ s.length ≤ 2 * 10^5  
• s consists only of printable ASCII characters
</div>', 1, 2, 'Easy', '["string", "two-pointers"]'),

                ('Longest Substring Without Repeating Characters', 'Find the longest substring without repeating characters', 
                '# Longest Substring Without Repeating Characters

Given a string `s`, find the length of the longest substring without repeating characters.

## Example 1:
<div class="example">
**Input:** s = "abcabcbb"  
**Output:** 3  
**Explanation:** The answer is "abc", with the length of 3.
</div>

## Constraints:
<div class="constraints">
• 0 ≤ s.length ≤ 5 * 10^4  
• s consists of English letters, digits, symbols and spaces
</div>', 1, 2, 'Medium', '["string", "sliding-window", "hash-table"]')
                """
                cursor.execute(insert_string_questions)
                
                # Insert sample questions for Tree
                insert_tree_questions = """
                INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
                ('Binary Tree Inorder Traversal', 'Perform inorder traversal of a binary tree', 
                '# Binary Tree Inorder Traversal

Given the root of a binary tree, return the inorder traversal of its nodes'' values.

## Example 1:
<div class="example">
**Input:** root = [1,null,2,3]  
**Output:** [1,3,2]
</div>

## Constraints:
<div class="constraints">
• The number of nodes in the tree is in the range [0, 100]  
• -100 ≤ Node.val ≤ 100
</div>', 1, 6, 'Easy', '["tree", "depth-first-search", "binary-tree"]'),

                ('Maximum Depth of Binary Tree', 'Find the maximum depth of a binary tree', 
                '# Maximum Depth of Binary Tree

Given the root of a binary tree, return its maximum depth.

## Example 1:
<div class="example">
**Input:** root = [3,9,20,null,null,15,7]  
**Output:** 3
</div>

## Constraints:
<div class="constraints">
• The number of nodes in the tree is in the range [0, 10^4]  
• -100 ≤ Node.val ≤ 100
</div>', 1, 6, 'Easy', '["tree", "depth-first-search", "breadth-first-search", "binary-tree"]')
                """
                cursor.execute(insert_tree_questions)
                
                # Insert sample questions for System Design
                insert_sd_questions = """
                INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
                ('Design a URL Shortener', 'Design a system to shorten long URLs', 
                '# Design a URL Shortener

Design a URL shortening service like TinyURL or Bitly.

## Requirements:
<div class="example">
**Functional Requirements:**
• Shorten a long URL to a short URL  
• Redirect short URL to original URL  
• Custom short URLs (optional)  
• Analytics on URL clicks
</div>

## Non-Functional Requirements:
<div class="constraints">
• High availability  
• Low latency  
• URL redirection should be fast  
• Short URLs should be unique  
• System should be scalable
</div>', 2, 2, 'Medium', '["database", "system-design", "url-shortener"]'),

                ('Design a Distributed Cache', 'Design a distributed caching system like Redis', 
                '# Design a Distributed Cache

Design a distributed caching system that can handle high throughput and provide low latency access to frequently used data.

## Requirements:
<div class="example">
**Functional Requirements:**
• Store key-value pairs  
• Retrieve values by key  
• Set expiration time  
• Support different data types
</div>

## Non-Functional Requirements:
<div class="constraints">
• High availability (99.9%+)  
• Low latency (< 10ms)  
• High throughput  
• Fault tolerance  
• Scalability
</div>', 2, 3, 'Hard', '["caching", "distributed-systems", "system-design"]')
                """
                cursor.execute(insert_sd_questions)
                
                print("✅ Sample questions inserted")
            else:
                print("✅ Questions already exist")
        except Error as e:
            print(f"⚠️  Questions insertion warning: {e}")
        
        # Step 8: Create indexes
        print("\n📋 Step 8: Creating indexes...")
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_questions_main_category ON questions(main_category_id)",
                "CREATE INDEX IF NOT EXISTS idx_questions_subcategory ON questions(subcategory_id)",
                "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)",
                "CREATE INDEX IF NOT EXISTS idx_subcategories_main_category ON subcategories(main_category_id)"
            ]
            
            for index in indexes:
                try:
                    cursor.execute(index)
                except Error as e:
                    if "already exists" not in str(e).lower():
                        print(f"⚠️  Index creation warning: {e}")
            
            print("✅ Indexes created/verified")
        except Error as e:
            print(f"⚠️  Index creation warning: {e}")
        
        # Commit all changes
        connection.commit()
        print("\n✅ All database changes committed successfully")
        
        # Verify the setup
        print("\n🔍 Verifying database setup...")
        
        # Check all tables
        tables = ['users', 'main_categories', 'subcategories', 'questions']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📊 {table}: {count} records")
            except Error as e:
                print(f"❌ Error checking {table}: {e}")
        
        # Show sample data
        print("\n📋 Sample Main Categories:")
        try:
            cursor.execute("SELECT name, description FROM main_categories")
            for name, desc in cursor.fetchall():
                print(f"  • {name}: {desc}")
        except Error as e:
            print(f"⚠️  Could not fetch main categories: {e}")
        
        print("\n📋 Sample Questions:")
        try:
            cursor.execute("""
                SELECT q.title, q.difficulty, mc.name as main_cat, sc.name as sub_cat
                FROM questions q
                JOIN main_categories mc ON q.main_category_id = mc.id
                JOIN subcategories sc ON q.subcategory_id = sc.id
                LIMIT 3
            """)
            for title, difficulty, main_cat, sub_cat in cursor.fetchall():
                print(f"  • {title} ({difficulty}) - {main_cat} > {sub_cat}")
        except Error as e:
            print(f"⚠️  Could not fetch questions: {e}")
        
        print("\n✅ Database setup completed successfully!")
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
    print("=" * 60)
    print("🏗️  Online Compiler Database Setup (Robust Mode)")
    print("=" * 60)
    
    success = setup_database_robust()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Start the FastAPI server: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Access the application: http://localhost:8000/auth")
        print("3. Try the question selection feature in the compiler!")
    else:
        print("\n💥 Setup failed! Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("• Make sure MySQL is running")
        print("• Check your database credentials in db_config.py")
        print("• Ensure you're in the 'own' directory")
    
    print("=" * 60)
