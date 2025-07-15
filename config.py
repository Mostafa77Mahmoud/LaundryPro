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

# Financial Configuration
COMMISSION_RATE = 0.30  # 30% commission rate for the app
SHOP_RATE = 0.70  # 70% revenue for the shop

# Currency Configuration
CURRENCY_SYMBOL = "LE"  # Egyptian Pound symbol
CURRENCY_CODE = "EGP"   # Currency code for display

# Payment Methods Configuration
SUPPORTED_PAYMENT_METHODS = ["cash", "mobile"]  # Only Cash and Mobile payments
DEFAULT_PAYMENT_METHOD = "cash"

# System Configuration
SYSTEM_NAME = "الحسيني كلين"  # System name in Arabic
SYSTEM_NAME_EN = "Husseini Clean"  # System name in English

# Order Status Configuration
ORDER_STATUSES = {
    "pending": {"en": "Pending", "ar": "في الانتظار"},
    "washing": {"en": "Washing", "ar": "قيد الغسيل"},
    "ready": {"en": "Ready", "ar": "جاهز"},
    "delivered": {"en": "Delivered", "ar": "تم التسليم"}
}

# Default Categories Configuration
DEFAULT_CATEGORIES = [
    {
        "id": "carpet-cleaning",
        "name_en": "Carpet Cleaning",
        "name_ar": "تنظيف السجاد",
        "description_en": "Professional carpet and rug cleaning services",
        "description_ar": "خدمات تنظيف السجاد والبسط الاحترافية",
        "image": "/static/images/carpet.jpg",
        "items": [
            {"name": {"en": "Small Rug (2x3)", "ar": "سجادة صغيرة (2×3)"}, "price": 50},
            {"name": {"en": "Medium Rug (3x5)", "ar": "سجادة متوسطة (3×5)"}, "price": 80},
            {"name": {"en": "Large Rug (5x8)", "ar": "سجادة كبيرة (5×8)"}, "price": 120},
            {"name": {"en": "Persian Carpet", "ar": "سجادة فارسية"}, "price": 200},
        ]
    },
    {
        "id": "womens-clothing",
        "name_en": "Women's Clothing",
        "name_ar": "ملابس نسائية",
        "description_en": "Delicate clothing care and cleaning",
        "description_ar": "العناية بالملابس الحساسة والتنظيف",
        "image": "/static/images/womens-clothing.jpg",
        "items": [
            {"name": {"en": "Dress", "ar": "فستان"}, "price": 25},
            {"name": {"en": "Blouse", "ar": "بلوزة"}, "price": 15},
            {"name": {"en": "Skirt", "ar": "تنورة"}, "price": 20},
            {"name": {"en": "Evening Gown", "ar": "فستان سهرة"}, "price": 40},
        ]
    },
    {
        "id": "upholstery-cleaning",
        "name_en": "Upholstery Cleaning",
        "name_ar": "تنظيف المفروشات",
        "description_en": "Furniture and upholstery deep cleaning",
        "description_ar": "تنظيف عميق للأثاث والمفروشات",
        "image": "/static/images/upholstery.jpg",
        "items": [
            {"name": {"en": "Single Chair", "ar": "كرسي مفرد"}, "price": 60},
            {"name": {"en": "2-Seater Sofa", "ar": "أريكة مقعدين"}, "price": 120},
            {"name": {"en": "3-Seater Sofa", "ar": "أريكة ثلاثة مقاعد"}, "price": 180},
            {"name": {"en": "Ottoman", "ar": "مقعد عثماني"}, "price": 40},
        ]
    },
    {
        "id": "bedding-blankets",
        "name_en": "Bedding & Blankets",
        "name_ar": "أغطية السرير والبطانيات",
        "description_en": "Bedding, comforters, and blanket cleaning",
        "description_ar": "تنظيف أغطية السرير والبطانيات",
        "image": "/static/images/bedding.jpg",
        "items": [
            {"name": {"en": "Single Blanket", "ar": "بطانية مفردة"}, "price": 35},
            {"name": {"en": "Double Blanket", "ar": "بطانية مزدوجة"}, "price": 50},
            {"name": {"en": "Comforter", "ar": "لحاف"}, "price": 60},
            {"name": {"en": "Pillow", "ar": "وسادة"}, "price": 10},
        ]
    }
]
