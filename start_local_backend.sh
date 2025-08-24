#!/bin/bash

echo "🚀 Starting Online Compiler Backend in Local Mode (No Docker)..."

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found. Please run this script from the 'own' directory."
    exit 1
fi

# Navigate to backend
cd backend

# Check if local startup script exists
if [ ! -f "start_local.sh" ]; then
    echo "❌ start_local.sh not found in backend directory."
    exit 1
fi

# Make scripts executable
chmod +x start_local.sh
chmod +x setup_mysql.sh

echo "✅ Scripts made executable"
echo ""

# Check if MySQL setup is needed
echo "🔍 Checking if MySQL setup is needed..."
if ! mysql -u root -p'Admin@40123' -h localhost -e "USE compiler_db;" > /dev/null 2>&1; then
    echo "⚠️  MySQL database 'compiler_db' not found or not accessible."
    echo "💡 Running MySQL setup script..."
    ./setup_mysql.sh
    
    if [ $? -ne 0 ]; then
        echo "❌ MySQL setup failed. Please check the errors above."
        echo "💡 You can try running the setup manually:"
        echo "   cd backend"
        echo "   ./setup_mysql.sh"
        exit 1
    fi
else
    echo "✅ MySQL database 'compiler_db' is accessible"
fi

echo ""
echo "🎯 Starting FastAPI backend with uvicorn..."
echo ""

# Start the backend
./start_local.sh
