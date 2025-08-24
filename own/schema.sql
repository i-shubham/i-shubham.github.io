-- MySQL Database Schema for Online Compiler Authentication and Questions
-- Run this script to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS online_compiler_auth;
USE online_compiler_auth;

-- Users table
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Questions Database Tables
-- Drop existing tables if they exist
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS subcategories;
DROP TABLE IF EXISTS main_categories;

-- Main Categories Table
CREATE TABLE main_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sub Categories Table
CREATE TABLE subcategories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    main_category_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (main_category_id) REFERENCES main_categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_subcategory (main_category_id, name)
);

-- Questions Table
CREATE TABLE questions (
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
);

-- Insert sample main categories
INSERT INTO main_categories (name, description) VALUES
('DataStructure', 'Data Structure problems including arrays, linked lists, trees, graphs, etc.'),
('SystemDesign', 'System Design problems including distributed systems, databases, scalability, etc.');

-- Insert sample subcategories for Data Structure
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
(1, 'Dynamic Programming', 'Dynamic programming problems');

-- Insert sample subcategories for System Design
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
(2, 'Monitoring', 'System monitoring and observability');

-- Insert sample questions for Data Structure - Array (2 questions)
INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
('Two Sum', 'Find two numbers in an array that add up to a target value', 
'# Two Sum Problem

Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

## Example 1:
<div class="example">
**Input:** nums = [2,7,11,15], target = 9  
**Output:** [0,1]  
**Explanation:** Because nums[0] + nums[1] == 9, we return [0, 1].
</div>

## Example 2:
<div class="example">
**Input:** nums = [3,2,4], target = 6  
**Output:** [1,2]
</div>

## Constraints:
<div class="constraints">
• 2 ≤ nums.length ≤ 10^4  
• -10^9 ≤ nums[i] ≤ 10^9  
• -10^9 ≤ target ≤ 10^9  
• Only one valid answer exists.
</div>', 1, 1, 'Easy', '["array", "hash-table", "two-pointers"]'),

('Maximum Subarray', 'Find the contiguous subarray with the largest sum', 
'# Maximum Subarray Problem

Given an integer array `nums`, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.

## Example 1:
<div class="example">
**Input:** nums = [-2,1,-3,4,-1,2,1,-5,4]  
**Output:** 6  
**Explanation:** The subarray [4,-1,2,1] has the largest sum 6.
</div>

## Example 2:
<div class="example">
**Input:** nums = [1]  
**Output:** 1
</div>

## Constraints:
<div class="constraints">
• 1 ≤ nums.length ≤ 3 * 10^4  
• -10^5 ≤ nums[i] ≤ 10^5
</div>', 1, 1, 'Medium', '["array", "divide-and-conquer", "dynamic-programming"]');

-- Insert sample questions for Data Structure - String (2 questions)
INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
('Valid Palindrome', 'Check if a string is a valid palindrome', 
'# Valid Palindrome Problem

Given a string `s`, return `true` if it is a palindrome, or `false` otherwise.

A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.

## Example 1:
<div class="example">
**Input:** s = "A man, a plan, a canal: Panama"  
**Output:** true  
**Explanation:** "amanaplanacanalpanama" is a palindrome.
</div>

## Example 2:
<div class="example">
**Input:** s = "race a car"  
**Output:** false  
**Explanation:** "raceacar" is not a palindrome.
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

## Example 2:
<div class="example">
**Input:** s = "bbbbb"  
**Output:** 1  
**Explanation:** The answer is "b", with the length of 1.
</div>

## Constraints:
<div class="constraints">
• 0 ≤ s.length ≤ 5 * 10^4  
• s consists of English letters, digits, symbols and spaces
</div>', 1, 2, 'Medium', '["string", "sliding-window", "hash-table"]');

-- Insert sample questions for Data Structure - Tree (2 questions)
INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
('Binary Tree Inorder Traversal', 'Perform inorder traversal of a binary tree', 
'# Binary Tree Inorder Traversal

Given the root of a binary tree, return the inorder traversal of its nodes'' values.

## Example 1:
<div class="example">
**Input:** root = [1,null,2,3]  
**Output:** [1,3,2]
</div>

## Example 2:
<div class="example">
**Input:** root = []  
**Output:** []
</div>

## Constraints:
<div class="constraints">
• The number of nodes in the tree is in the range [0, 100]  
• -100 ≤ Node.val ≤ 100
</div>', 1, 6, 'Easy', '["tree", "depth-first-search", "binary-tree"]'),

('Maximum Depth of Binary Tree', 'Find the maximum depth of a binary tree', 
'# Maximum Depth of Binary Tree

Given the root of a binary tree, return its maximum depth.

A binary tree''s maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.

## Example 1:
<div class="example">
**Input:** root = [3,9,20,null,null,15,7]  
**Output:** 3
</div>

## Example 2:
<div class="example">
**Input:** root = [1,null,2]  
**Output:** 2
</div>

## Constraints:
<div class="constraints">
• The number of nodes in the tree is in the range [0, 10^4]  
• -100 ≤ Node.val ≤ 100
</div>', 1, 6, 'Easy', '["tree", "depth-first-search", "breadth-first-search", "binary-tree"]');

-- Insert sample questions for System Design - Database Design (2 questions)
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
</div>

## Design Considerations:
<div class="example">
**Database Design:**
• URL mapping table  
• User management  
• Analytics tracking  
• Rate limiting
</div>', 2, 2, 'Medium', '["database", "system-design", "url-shortener"]'),

('Design a Social Media Feed', 'Design a social media news feed system', 
'# Design a Social Media Feed

Design a social media news feed system like Facebook, Twitter, or Instagram.

## Requirements:
<div class="example">
**Functional Requirements:**
• Display personalized posts in chronological order  
• Support different types of content (text, images, videos)  
• Like, comment, and share functionality  
• Follow/unfollow users
</div>

## Non-Functional Requirements:
<div class="constraints">
• Low latency feed generation  
• High availability  
• Scalability for millions of users  
• Real-time updates
</div>

## Design Considerations:
<div class="example">
**Database Design:**
• User relationships table  
• Content storage strategy  
• Feed generation algorithm  
• Caching strategy
</div>', 2, 2, 'Hard', '["database", "system-design", "social-media", "feed"]');

-- Insert sample questions for System Design - Caching (2 questions)
INSERT INTO questions (title, description, content, main_category_id, subcategory_id, difficulty, tags) VALUES
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
</div>

## Design Considerations:
<div class="example">
**Architecture:**
• Cache partitioning  
• Replication strategy  
• Eviction policies  
• Consistency models  
• Load balancing
</div>', 2, 3, 'Hard', '["caching", "distributed-systems", "system-design"]'),

('Design a CDN', 'Design a Content Delivery Network system', 
'# Design a Content Delivery Network

Design a Content Delivery Network (CDN) system to deliver content globally with low latency.

## Requirements:
<div class="example">
**Functional Requirements:**
• Distribute content across multiple geographic locations  
• Route users to nearest server  
• Cache static content (images, videos, CSS, JS)  
• Handle dynamic content
</div>

## Non-Functional Requirements:
<div class="constraints">
• Global coverage  
• Low latency (< 100ms)  
• High availability  
• Cost-effective  
• Scalable
</div>

## Design Considerations:
<div class="example">
**Architecture:**
• Edge server placement  
• Load balancing strategy  
• Caching policies  
• Origin server management  
• Geographic routing
</div>', 2, 3, 'Medium', '["caching", "cdn", "system-design", "distributed-systems"]');

-- Create indexes for better performance
CREATE INDEX idx_questions_main_category ON questions(main_category_id);
CREATE INDEX idx_questions_subcategory ON questions(subcategory_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_subcategories_main_category ON subcategories(main_category_id);

-- Create a view for easy question retrieval
CREATE VIEW question_details AS
SELECT 
    q.id,
    q.title,
    q.description,
    q.content,
    q.difficulty,
    q.tags,
    mc.name as main_category,
    sc.name as subcategory,
    q.created_at,
    q.updated_at
FROM questions q
JOIN main_categories mc ON q.main_category_id = mc.id
JOIN subcategories sc ON q.subcategory_id = sc.id;
