#!/bin/bash

echo "=========================================="
echo "TTS Backend - Email Auth Setup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Database Setup"
echo "=========================================="
echo ""

# Check if database exists
if [ -f "dev.db" ]; then
    echo "Database already exists. Backing up..."
    cp dev.db dev.db.backup.$(date +%Y%m%d_%H%M%S)
fi

echo "Creating/updating database tables..."
python3 << EOF
from app.db import Base, engine
from app.models import User, VerificationCode, Voice, Job, Chunk

# Create all tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created successfully")
EOF

echo ""
echo "=========================================="
echo "Environment Configuration"
echo "=========================================="
echo ""

# Check if .env has JWT secret
if grep -q "JWT_SECRET_KEY=change-this" .env 2>/dev/null || ! grep -q "JWT_SECRET_KEY=" .env 2>/dev/null; then
    echo "Generating JWT secret key..."
    SECRET=$(openssl rand -hex 32)
    if grep -q "JWT_SECRET_KEY=" .env 2>/dev/null; then
        # Update existing key
        sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$SECRET/" .env
    else
        # Add new key
        echo "" >> .env
        echo "JWT_SECRET_KEY=$SECRET" >> .env
    fi
    echo "✓ JWT secret key generated"
else
    echo "✓ JWT secret key already configured"
fi

echo ""
echo "=========================================="
echo "Verify Configuration"
echo "=========================================="
echo ""

# Check required environment variables
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = {
    "JWT_SECRET_KEY": "JWT authentication",
    "RESEND_API_KEY": "Email service",
    "CLOUDINARY_CLOUD_NAME": "File storage",
    "CLOUDINARY_API_KEY": "File storage",
    "CLOUDINARY_API_SECRET": "File storage",
}

missing = []
for var, purpose in required_vars.items():
    value = os.getenv(var)
    if not value or value.startswith("change-this") or value.startswith("your-"):
        missing.append(f"  - {var} ({purpose})")
        print(f"✗ {var}: NOT SET")
    else:
        print(f"✓ {var}: Configured")

if missing:
    print("\n⚠️  Missing or incomplete configuration:")
    for m in missing:
        print(m)
    print("\nPlease update your .env file with valid credentials.")
else:
    print("\n✓ All required environment variables are configured!")
EOF

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env with your Resend and Cloudinary credentials"
echo "2. Run the server: uvicorn app.main:app --reload"
echo "3. Test the API at: http://localhost:8000/docs"
echo ""
echo "See MIGRATION_GUIDE.md for more information."
echo ""
