# 🚀 Questions Database Setup Guide

This guide will help you set up the new questions feature for the Online Compiler.

## 📋 What's New

- **Moved Sample Question and Clear Question buttons** from header to question panel
- **Added question selection popup** with categories and subcategories
- **Database-driven questions** instead of hardcoded sample questions
- **Categorized questions** for Data Structure and System Design

## 🗄️ Database Structure

The new database includes:

### Main Categories
- **DataStructure**: Array, String, Linked List, Stack, Queue, Tree, Graph, Hash Table, Heap, Dynamic Programming
- **SystemDesign**: Distributed Systems, Database Design, Caching, Load Balancing, Microservices, Scalability, Security, API Design, Message Queues, Monitoring

### Questions Table
- Title, description, content (HTML/markdown)
- Difficulty levels (Easy, Medium, Hard)
- Tags for categorization
- Foreign key relationships to categories

## 🛠️ Setup Instructions

### Step 1: Run the Database Setup Script

```bash
cd own
python setup_database.py
```

This script will:
- Create the new database tables
- Insert sample categories and subcategories
- Add sample questions for each category
- Verify the setup was successful

**Alternative**: You can also run the SQL directly:
```bash
mysql -u your_username -p online_compiler_auth < schema.sql
```

### Step 2: Start the FastAPI Server

```bash
cd own
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Access the Application

- **Authentication**: `http://localhost:8000/auth`
- **Compiler**: `http://localhost:8000/compiler_index.html`

## 🎯 How to Use

### For Users:
1. **Click "📚 Sample Question"** in the question panel
2. **Select Main Category**: Data Structure or System Design
3. **Select Sub Category**: e.g., Array, Tree, Database Design, Caching
4. **Choose a Question** from the list
5. **Question appears** in the question panel with full content

### For Developers:
- **Add new questions**: Insert into the `questions` table
- **Add new categories**: Insert into `main_categories` and `subcategories` tables
- **Modify question content**: Update the `content` field (supports HTML/markdown)

## 📁 Files Modified/Created

### Modified Files:
- `compilar_index.html` - Added question modal, moved buttons to question panel
- `main.py` - Added new API endpoints for questions

### New Files:
- `schema.sql` - Complete database schema with users, categories, and questions
- `setup_database.py` - Database setup script
- `README_QUESTIONS.md` - This documentation

## 🔌 API Endpoints

### New Question Endpoints:
- `GET /api/questions/subcategories?main_category={category}` - Get subcategories
- `GET /api/questions?main_category={category}&sub_category={subcategory}` - Get questions list
- `GET /api/questions/{question_id}` - Get specific question content

## 🎨 UI Features

### Question Panel:
- **Header**: Shows "Question" with Sample Question and Clear Question buttons
- **Content**: Displays selected question with rich formatting
- **Responsive**: Adapts to different question content lengths

### Question Modal:
- **Category Selection**: Dropdown for main and sub categories
- **Question List**: Shows available questions with difficulty indicators
- **Rich Content**: Questions support HTML formatting, examples, and constraints

## 🐛 Troubleshooting

### Common Issues:

1. **"Database connection failed"**
   - Check your MySQL connection in `db_config.py`
   - Ensure MySQL service is running

2. **"Schema file not found"**
   - Make sure `questions_schema.sql` is in the same directory as `setup_questions_db.py`

3. **Questions not loading**
   - Verify the database setup was successful
   - Check browser console for API errors
   - Ensure you're accessing via `http://localhost:8000` not `file://`

4. **Modal not showing**
   - Check if JavaScript errors in browser console
   - Ensure all CSS and JavaScript files are loaded

## 🔮 Future Enhancements

- **Question difficulty filtering**
- **Search functionality**
- **User question history**
- **Question ratings and reviews**
- **Custom question creation**
- **Question templates**

## 📞 Support

If you encounter any issues:
1. Check the browser console for JavaScript errors
2. Verify database connection and tables
3. Ensure all files are in the correct locations
4. Check the FastAPI server logs for backend errors

---

**Happy Coding! 🎉**
