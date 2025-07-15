import os

# Admin Authentication Configuration
ADMIN_SECRET = "sasa_ot123"  # Change this password to secure your admin panel

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

# File Upload Configuration
UPLOAD_FOLDER = "static/uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Session Configuration
SESSION_SECRET = os.environ.get("SESSION_SECRET",
                                "your-session-secret-key-here")

# Commission Rate Configuration
COMMISSION_RATE = 0.30  # 30% commission rate for the app
SHOP_RATE = 0.70  # 70% revenue for the shop
