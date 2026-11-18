#!/bin/bash
set -e

echo "🚀 Ah Liki Investment Corporation - Setup Script"
echo "=================================================="
echo ""

# This script is for LOCAL development only. On Azure App Service the startup
# command is `bash startup.sh`, and deployments are done by the GitHub Actions
# workflow, which ships code only — never the database.
if [ -n "$WEBSITE_HOSTNAME" ]; then
    echo "❌ This is the local setup script. On Azure, use: bash startup.sh"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python --version)
echo "✅ Using $PYTHON_VERSION"
echo ""

# Install requirements
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🗄️  Running migrations (existing data is kept)..."
python manage.py migrate

echo ""
echo "🌱 Seeding initial data..."
python manage.py seed_data

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Demo Credentials:"
echo "   Admin:    admin@example.com / AdminPass123!"
echo "   Finance:  finance@example.com / FinancePass123!"
echo "   Customer: customer@example.com / CustomerPass123!"
echo ""
echo "🚀 To start development server:"
echo "   python manage.py runserver"
echo ""
echo "🌐 Then visit: http://localhost:8000"
