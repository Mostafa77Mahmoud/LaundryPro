from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json

class DataStore:
    def __init__(self):
        self.users = {}
        self.orders = {}
        self.categories = {}
        self.init_default_categories()
    
    def init_default_categories(self):
        """Initialize default service categories with bilingual support"""
        default_categories = [
            {
                "id": "carpet_cleaning",
                "name": {"en": "Carpet Cleaning", "ar": "غسيل سجاد"},
                "description": {"en": "Professional carpet cleaning services", "ar": "خدمات غسيل السجاد المهنية"},
                "image": "/static/images/carpet.svg",
                "items": [
                    {"name": {"en": "Small Rug", "ar": "سجادة صغيرة"}, "price": 40},
                    {"name": {"en": "Medium Carpet", "ar": "سجادة متوسطة"}, "price": 70},
                    {"name": {"en": "Large Carpet", "ar": "سجادة كبيرة"}, "price": 100},
                    {"name": {"en": "Persian Rug", "ar": "سجادة فارسية"}, "price": 150}
                ]
            },
            {
                "id": "womens_clothing",
                "name": {"en": "Women's Clothing", "ar": "ملابس حريمي"},
                "description": {"en": "Delicate clothing care", "ar": "عناية بالملابس الحساسة"},
                "image": "/static/images/clothes.svg",
                "items": [
                    {"name": {"en": "Dress", "ar": "فستان"}, "price": 25},
                    {"name": {"en": "Blouse", "ar": "بلوزة"}, "price": 15},
                    {"name": {"en": "Skirt", "ar": "تنورة"}, "price": 20},
                    {"name": {"en": "Formal Suit", "ar": "بدلة رسمية"}, "price": 50}
                ]
            },
            {
                "id": "upholstery_cleaning",
                "name": {"en": "Upholstery Cleaning", "ar": "غسيل انتريهات"},
                "description": {"en": "Furniture and upholstery cleaning", "ar": "تنظيف الأثاث والمفروشات"},
                "image": "/static/images/upholstery.svg",
                "items": [
                    {"name": {"en": "Single Chair", "ar": "كرسي واحد"}, "price": 30},
                    {"name": {"en": "2-Seater Sofa", "ar": "كنبة مقعدين"}, "price": 80},
                    {"name": {"en": "3-Seater Sofa", "ar": "كنبة ثلاثة مقاعد"}, "price": 120},
                    {"name": {"en": "Ottoman", "ar": "مقعد صغير"}, "price": 25}
                ]
            },
            {
                "id": "bedding_blankets",
                "name": {"en": "Bedding & Blankets", "ar": "بطاطين ومفروشات"},
                "description": {"en": "Bedding and blanket cleaning", "ar": "تنظيف البطاطين والمفروشات"},
                "image": "/static/images/bedding.svg",
                "items": [
                    {"name": {"en": "Single Blanket", "ar": "بطانية فردي"}, "price": 35},
                    {"name": {"en": "Double Blanket", "ar": "بطانية دبل"}, "price": 50},
                    {"name": {"en": "Comforter", "ar": "لحاف"}, "price": 60},
                    {"name": {"en": "Pillow", "ar": "مخدة"}, "price": 10}
                ]
            }
        ]
        
        for category in default_categories:
            self.categories[category["id"]] = category

# Global data store instance
data_store = DataStore()

class User:
    def __init__(self, name: str, phone: str, latitude: float = None, longitude: float = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.latitude = latitude
        self.longitude = longitude
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat()
        }

class Order:
    def __init__(self, user_id: str, items: List[Dict], payment_method: str = "cash"):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.items = items  # List of {category_id, item_name, quantity, unit_price, total_price}
        self.total_amount = sum(item.get('total_price', 0) for item in items)
        self.payment_method = payment_method  # cash, card, mobile_payment
        self.status = "pending"  # pending, washing, ready, delivered
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.commission_rate = 0.15  # 15% commission for app owner
        self.commission_amount = self.total_amount * self.commission_rate
        self.shop_amount = self.total_amount - self.commission_amount
    
    def update_status(self, new_status: str):
        self.status = new_status
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": self.items,
            "total_amount": self.total_amount,
            "payment_method": self.payment_method,
            "status": self.status,
            "commission_rate": self.commission_rate,
            "commission_amount": self.commission_amount,
            "shop_amount": self.shop_amount,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class Category:
    def __init__(self, name: Dict[str, str], description: Dict[str, str], image: str, items: List[Dict]):
        self.id = str(uuid.uuid4())
        self.name = name  # {"en": "English Name", "ar": "Arabic Name"}
        self.description = description
        self.image = image
        self.items = items  # List of {name: {en, ar}, price}
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "items": self.items,
            "created_at": self.created_at.isoformat()
        }
