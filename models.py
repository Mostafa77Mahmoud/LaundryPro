import uuid
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with orders
    orders = relationship("Order", back_populates="user")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name_en = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=False)
    description_en = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    image = Column(String(500), nullable=True)
    items = Column(JSON, nullable=True)  # Store items as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with order items
    order_items = relationship("OrderItem", back_populates="category")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": {"en": self.name_en, "ar": self.name_ar},
            "description": {"en": self.description_en, "ar": self.description_ar},
            "image": self.image,
            "items": self.items or [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    payment_method = Column(String(50), default="cash")
    status = Column(String(50), default="pending")
    total_amount = Column(Float, default=0.0)
    app_commission = Column(Float, default=0.0)
    shop_revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def update_status(self, new_status: str):
        self.status = new_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def calculate_totals(self):
        """Calculate order totals based on items"""
        self.total_amount = sum(item.quantity * item.unit_price for item in self.items)
        self.app_commission = self.total_amount * 0.30  # 30% commission
        self.shop_revenue = self.total_amount * 0.70   # 70% to shop
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "payment_method": self.payment_method,
            "status": self.status,
            "total_amount": self.total_amount,
            "app_commission": self.app_commission,
            "shop_revenue": self.shop_revenue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey('orders.id'), nullable=False)
    category_id = Column(String(36), ForeignKey('categories.id'), nullable=True)
    item_name_en = Column(String(255), nullable=False)
    item_name_ar = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    category = relationship("Category", back_populates="order_items")
    
    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "category_id": self.category_id,
            "item_name": {"en": self.item_name_en, "ar": self.item_name_ar},
            "quantity": self.quantity,
            "unit_price": self.unit_price
        }

def init_default_categories():
    """Initialize default service categories with bilingual support"""
    default_categories = [
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
                {"name": {"en": "Bed Sheet Set", "ar": "طقم ملاءات السرير"}, "price": 30},
                {"name": {"en": "Comforter", "ar": "لحاف"}, "price": 50},
                {"name": {"en": "Blanket", "ar": "بطانية"}, "price": 40},
                {"name": {"en": "Pillow", "ar": "وسادة"}, "price": 15},
            ]
        }
    ]
    
    for cat_data in default_categories:
        category = Category(
            id=cat_data["id"],
            name_en=cat_data["name_en"],
            name_ar=cat_data["name_ar"],
            description_en=cat_data["description_en"],
            description_ar=cat_data["description_ar"],
            image=cat_data["image"],
            items=cat_data["items"]
        )
        db.session.add(category)
    
    db.session.commit()