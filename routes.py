import os
import defusedcsv as csv
import io
import uuid
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app, db, admin_required
from models import User, Order, Category, OrderItem
from analytics import AnalyticsEngine
import config

# Initialize analytics engine - commented out for now
# analytics = None

@app.route('/')
@admin_required
def dashboard():
    """Main dashboard view"""
    # Simple stats for now - using all orders to avoid date filtering issues
    all_orders = Order.query.all()
    
    total_revenue = sum(order.total_amount or 0 for order in all_orders)
    app_commission = sum(order.app_commission or 0 for order in all_orders)
    shop_revenue = sum(order.shop_revenue or 0 for order in all_orders)
    
    today_stats = {
        'today_orders': len(all_orders),
        'today_revenue': total_revenue,
        'today_commission': app_commission,
        'today_shop_revenue': shop_revenue
    }
    
    return render_template('dashboard.html', stats=today_stats)

@app.route('/analytics')
@admin_required
def analytics_page():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/orders')
@admin_required
def orders_page():
    """Orders management page"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Convert to dict format for template
    orders_data = []
    for order in orders:
        order_dict = order.to_dict()
        order_dict['user_info'] = order.user.to_dict() if order.user else {"name": "Unknown", "phone": "N/A"}
        orders_data.append(order_dict)
    
    return render_template('orders.html', orders=orders_data)

@app.route('/categories')
@admin_required
def categories_page():
    """Categories management page"""
    categories = Category.query.all()
    categories_data = [category.to_dict() for category in categories]
    return render_template('categories.html', categories=categories_data)

@app.route('/reports')
@admin_required
def reports_page():
    """Reports and export page"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Convert to dict format for template
    orders_data = []
    for order in orders:
        order_dict = order.to_dict()
        order_dict['user_info'] = order.user.to_dict() if order.user else {"name": "Unknown", "phone": "N/A"}
        orders_data.append(order_dict)
    
    return render_template('reports.html', orders=orders_data)

# API Endpoints

@app.route('/api/users', methods=['POST'])
def create_user():
    """Register new user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('phone'):
            return jsonify({"error": "Name and phone are required"}), 400
        
        user = User(
            name=data['name'],
            phone=data['phone'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "user_id": user.id,
            "message": "User registered successfully"
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": "Failed to create user"}), 500

@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Get all service categories and prices"""
    try:
        categories = Category.query.all()
        categories_data = [category.to_dict() for category in categories]
        
        return jsonify({"categories": categories_data}), 200
        
    except Exception as e:
        app.logger.error(f"Error getting prices: {str(e)}")
        return jsonify({"error": "Failed to get prices"}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new laundry order"""
    try:
        data = request.get_json()
        
        if not data or not data.get('user_id') or not data.get('items'):
            return jsonify({"error": "User ID and items are required"}), 400
        
        # Validate user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Validate payment method
        payment_method = data.get('payment_method', config.DEFAULT_PAYMENT_METHOD)
        if payment_method not in config.SUPPORTED_PAYMENT_METHODS:
            return jsonify({"error": f"Unsupported payment method. Supported: {config.SUPPORTED_PAYMENT_METHODS}"}), 400
        
        # Create order
        order = Order(
            user_id=data['user_id'],
            payment_method=payment_method
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID before adding items
        
        # Add order items
        total_amount = 0
        for item in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                category_id=item.get('category_id'),
                item_name_en=item['item_name'].get('en', item['item_name']),
                item_name_ar=item['item_name'].get('ar', '') if isinstance(item['item_name'], dict) else '',
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )
            db.session.add(order_item)
            total_amount += item['quantity'] * item['unit_price']
        
        # Calculate commission and shop revenue
        order.total_amount = total_amount
        order.app_commission = total_amount * config.COMMISSION_RATE
        order.shop_revenue = total_amount * config.SHOP_RATE
        
        db.session.commit()
        
        return jsonify({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "message": "Order created successfully"
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": "Failed to create order"}), 500

@app.route('/api/users/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Get orders for a specific user"""
    try:
        user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        user_orders_data = [order.to_dict() for order in user_orders]
        
        return jsonify({"orders": user_orders_data}), 200
        
    except Exception as e:
        app.logger.error(f"Error getting user orders: {str(e)}")
        return jsonify({"error": "Failed to get orders"}), 500

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({"error": "Status is required"}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        valid_statuses = ['pending', 'washing', 'ready', 'delivered']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
        order.update_status(data['status'])
        db.session.commit()
        
        return jsonify({
            "message": "Order status updated successfully",
            "new_status": order.status
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error updating order status: {str(e)}")
        return jsonify({"error": "Failed to update order status"}), 500

import re

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Enhanced intelligent chatbot for price inquiries, calculations, and order assistance"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        message = data['message'].lower().strip()
        user_id = data.get('user_id')
        
        # Enhanced chatbot response logic
        response_data = process_chatbot_message(message, user_id)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        app.logger.error(f"Error in chatbot: {str(e)}")
        return jsonify({"error": "Failed to process message"}), 500

def process_chatbot_message(message, user_id=None):
    """Process chatbot message with enhanced capabilities"""
    
    # Price calculation patterns
    calc_patterns = [
        r'calculate|calc|compute|total|sum|مجموع|حساب|احسب',
        r'how much|كم|سعر|تكلفة',
        r'(\d+)\s*(carpet|rug|سجاد|سجادة)',
        r'(\d+)\s*(shirt|dress|قميص|فستان|ملابس)',
        r'(\d+)\s*(sofa|chair|كنب|كرسي|أثاث)'
    ]
    
    # Check for calculation requests
    if any(re.search(pattern, message) for pattern in calc_patterns):
        return handle_price_calculation(message)
    
    # Order tracking with ID extraction
    order_id_match = re.search(r'([a-f0-9-]{36})|order\s+(\w+)', message)
    if ('track' in message or 'طلب' in message or 'order' in message) and order_id_match:
        order_id = order_id_match.group(1) or order_id_match.group(2)
        return handle_order_tracking(order_id, user_id)
    
    # Phone number extraction for order lookup
    phone_match = re.search(r'(\+?\d{10,15})', message)
    if ('track' in message or 'order' in message) and phone_match:
        phone = phone_match.group(1)
        return handle_phone_order_lookup(phone)
    
    # Service recommendations
    if 'recommend' in message or 'suggest' in message or 'اقترح' in message or 'أنصح' in message:
        return handle_service_recommendations(message)
    
    # Price inquiries
    if 'price' in message or 'cost' in message or 'سعر' in message or 'تكلفة' in message:
        return handle_price_inquiry(message)
    
    # Payment information
    if 'payment' in message or 'pay' in message or 'دفع' in message:
        return handle_payment_info()
    
    # Operating hours
    if 'hour' in message or 'time' in message or 'open' in message or 'ساعات' in message or 'مواعيد' in message:
        return handle_operating_hours()
    
    # Location/delivery info
    if 'location' in message or 'delivery' in message or 'address' in message or 'موقع' in message or 'توصيل' in message:
        return handle_location_info()
    
    # Help or general greeting
    if any(word in message for word in ['help', 'hello', 'hi', 'مرحبا', 'مساعدة', 'السلام']):
        return handle_general_help()
    
    # Default response with smart suggestions
    return handle_default_response(message)

def handle_price_calculation(message):
    """Handle price calculation requests"""
    categories = Category.query.all()
    total_cost = 0
    calculation_details = []
    
    # Extract quantities and service types
    for category in categories:
        if not category.items:
            continue
            
        for item in category.items:
            # Check for item mentions with quantities
            item_patterns = [
                item['name']['en'].lower(),
                item['name'].get('ar', '').lower()
            ]
            
            for pattern in item_patterns:
                if pattern and pattern in message:
                    # Look for quantity numbers near the item name
                    qty_match = re.search(rf'(\d+)\s*{re.escape(pattern)}|{re.escape(pattern)}\s*(\d+)', message)
                    if qty_match:
                        qty = int(qty_match.group(1) or qty_match.group(2))
                        item_total = qty * item['price']
                        total_cost += item_total
                        calculation_details.append({
                            'item': item['name']['en'],
                            'quantity': qty,
                            'unit_price': item['price'],
                            'total': item_total
                        })
    
    if calculation_details:
        response = "📊 **Cost Calculation:**\n\n"
        for detail in calculation_details:
            response += f"• {detail['item']}: {detail['quantity']} × {detail['unit_price']} = {detail['total']} {config.CURRENCY_SYMBOL}\n"
        
        # Add commission calculation
        app_commission = total_cost * config.COMMISSION_RATE
        shop_revenue = total_cost * config.SHOP_RATE
        
        response += f"\n**Total Cost:** {total_cost} {config.CURRENCY_SYMBOL}\n"
        response += f"**Commission ({int(config.COMMISSION_RATE * 100)}%):** {app_commission:.2f} {config.CURRENCY_SYMBOL}\n"
        response += f"**Shop Revenue ({int(config.SHOP_RATE * 100)}%):** {shop_revenue:.2f} {config.CURRENCY_SYMBOL}\n"
        
        return {
            "response": response,
            "type": "calculation",
            "calculation": {
                "items": calculation_details,
                "total": total_cost,
                "commission": app_commission,
                "shop_revenue": shop_revenue
            }
        }
    else:
        return {
            "response": "I can help you calculate costs! Please specify items and quantities like:\n• '3 carpets'\n• '2 shirts and 1 dress'\n• 'Calculate 5 small rugs'",
            "type": "calculation_help"
        }

def handle_order_tracking(order_id, user_id):
    """Handle order tracking by ID"""
    order = Order.query.get(order_id)
    
    if not order:
        return {
            "response": "Order not found. Please check your order ID and try again.",
            "type": "order_not_found"
        }
    
    # Calculate time since order
    time_diff = datetime.now() - order.created_at
    time_ago = f"{time_diff.days} days" if time_diff.days > 0 else f"{time_diff.seconds // 3600} hours"
    
    response = f"📋 **Order Status Update**\n\n"
    response += f"**Order ID:** {order.id}\n"
    response += f"**Status:** {order.status.title()}\n"
    response += f"**Total Amount:** {order.total_amount} {config.CURRENCY_SYMBOL}\n"
    response += f"**Placed:** {time_ago} ago\n"
    response += f"**Payment:** {order.payment_method.title()}\n\n"
    
    # Status-specific messages
    status_messages = {
        'pending': 'Your order is being processed and will be picked up soon.',
        'washing': 'Your items are currently being cleaned with care.',
        'ready': 'Great news! Your order is ready for pickup or delivery.',
        'delivered': 'Your order has been completed. Thank you for choosing our service!'
    }
    
    response += status_messages.get(order.status, 'Order is being processed.')
    
    return {
        "response": response,
        "type": "order_status",
        "order": order.to_dict()
    }

def handle_phone_order_lookup(phone):
    """Handle order lookup by phone number"""
    user = User.query.filter_by(phone=phone).first()
    
    if not user:
        return {
            "response": f"No orders found for phone number {phone}. Please check the number or create a new order.",
            "type": "no_orders"
        }
    
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).limit(5).all()
    
    if not orders:
        return {
            "response": f"No orders found for {user.name}. Ready to place your first order?",
            "type": "no_orders"
        }
    
    response = f"📱 **Orders for {user.name}:**\n\n"
    for order in orders:
        response += f"• **{order.id}** - {order.status.title()} - {order.total_amount} {config.CURRENCY_SYMBOL}\n"
    
    response += f"\nTo track a specific order, send me the order ID."
    
    return {
        "response": response,
        "type": "phone_orders",
        "orders": [order.to_dict() for order in orders]
    }

def handle_service_recommendations(message):
    """Provide service recommendations based on user needs"""
    categories = Category.query.all()
    
    # Recommendation logic based on keywords
    recommendations = []
    
    if any(word in message for word in ['carpet', 'rug', 'floor', 'سجاد', 'أرضية']):
        carpet_cat = next((cat for cat in categories if 'carpet' in cat.name_en.lower()), None)
        if carpet_cat:
            recommendations.append(carpet_cat)
    
    if any(word in message for word in ['clothes', 'shirt', 'dress', 'ملابس', 'قميص', 'فستان']):
        clothing_cat = next((cat for cat in categories if 'women' in cat.name_en.lower() or 'cloth' in cat.name_en.lower()), None)
        if clothing_cat:
            recommendations.append(clothing_cat)
    
    if any(word in message for word in ['furniture', 'sofa', 'chair', 'أثاث', 'كنب', 'كرسي']):
        furniture_cat = next((cat for cat in categories if 'upholstery' in cat.name_en.lower()), None)
        if furniture_cat:
            recommendations.append(furniture_cat)
    
    if recommendations:
        response = "🎯 **Recommended Services:**\n\n"
        for cat in recommendations:
            response += f"**{cat.name_en}** ({cat.name_ar})\n"
            response += f"{cat.description_en}\n\n"
            if cat.items:
                response += "Services include:\n"
                for item in cat.items[:3]:  # Show top 3 items
                    response += f"• {item['name']['en']}: {item['price']} {config.CURRENCY_SYMBOL}\n"
                response += "\n"
    else:
        response = "I'd be happy to recommend services! Could you tell me what type of cleaning you need?\n\n"
        response += "We offer:\n• Carpet & Rug Cleaning\n• Women's Clothing Care\n• Upholstery Cleaning"
    
    return {
        "response": response,
        "type": "recommendations"
    }

def handle_price_inquiry(message):
    """Handle general price inquiries"""
    categories = Category.query.all()
    response = "💰 **Our Service Prices:**\n\n"
    
    for category in categories:
        response += f"**{category.name_en}** ({category.name_ar})\n"
        if category.items:
            for item in category.items:
                response += f"• {item['name']['en']}: {item['price']} {config.CURRENCY_SYMBOL}\n"
        response += "\n"
    
    response += f"💡 **Tip:** Send me quantities like '3 carpets + 2 shirts' and I'll calculate the total cost!"
    
    return {
        "response": response,
        "type": "price_list"
    }

def handle_payment_info():
    """Handle payment method inquiries"""
    response = f"💳 **Payment Methods:**\n\n"
    response += f"We accept: {', '.join(config.SUPPORTED_PAYMENT_METHODS)}\n\n"
    response += f"💰 **Commission Structure:**\n"
    response += f"• App Commission: {int(config.COMMISSION_RATE * 100)}%\n"
    response += f"• Shop Revenue: {int(config.SHOP_RATE * 100)}%\n\n"
    response += f"All prices are in {config.CURRENCY_SYMBOL}."
    
    return {
        "response": response,
        "type": "payment_info"
    }

def handle_operating_hours():
    """Handle operating hours inquiries"""
    response = "🕒 **Operating Hours:**\n\n"
    response += "• Monday - Saturday: 8:00 AM - 8:00 PM\n"
    response += "• Sunday: 10:00 AM - 6:00 PM\n\n"
    response += "📞 **Contact:** Available during business hours\n"
    response += "💬 **Chat Support:** 24/7 (like now!)"
    
    return {
        "response": response,
        "type": "hours"
    }

def handle_location_info():
    """Handle location and delivery inquiries"""
    response = "📍 **Service Area & Delivery:**\n\n"
    response += "• **Pickup Service:** Free within city limits\n"
    response += "• **Delivery:** Same-day or next-day delivery\n"
    response += "• **Coverage Area:** All major neighborhoods\n\n"
    response += "📱 **GPS Tracking:** We'll locate you when you place an order\n"
    response += "🚚 **Delivery Fee:** Calculated based on distance"
    
    return {
        "response": response,
        "type": "location"
    }

def handle_general_help():
    """Handle general help and greetings"""
    response = "👋 **Welcome! I'm your laundry assistant.**\n\n"
    response += "I can help you with:\n"
    response += "💰 **Price Calculations** - 'Calculate 3 carpets + 2 shirts'\n"
    response += "📋 **Order Tracking** - Send your order ID or phone number\n"
    response += "🎯 **Service Recommendations** - Tell me what you need cleaned\n"
    response += "💳 **Payment Info** - Payment methods and pricing\n"
    response += "📍 **Location & Hours** - Service area and operating times\n\n"
    response += "Just type your question naturally - I'll understand! 😊"
    
    return {
        "response": response,
        "type": "help"
    }

def handle_default_response(message):
    """Handle unrecognized messages with smart suggestions"""
    # Try to extract intent from unknown messages
    suggestions = []
    
    if any(char in message for char in '0123456789'):
        suggestions.append("💡 Try: 'Calculate 3 carpets' for price estimation")
    
    if len(message) > 10:
        suggestions.append("💡 Try: 'Track my order' or send your order ID")
    
    response = "🤔 I'm not sure I understood that completely.\n\n"
    
    if suggestions:
        response += "Here are some suggestions:\n"
        for suggestion in suggestions:
            response += f"{suggestion}\n"
    else:
        response += "You can ask me about:\n"
        response += "• Service prices and calculations\n"
        response += "• Order tracking and status\n"
        response += "• Recommendations and help\n"
    
    response += "\n💬 **Tip:** Type 'help' for all available commands!"
    
    return {
        "response": response,
        "type": "unclear"
    }

@app.route('/api/analytics/summary')
def analytics_summary():
    """Get analytics summary for dashboard"""
    try:
        # Using all orders for now to avoid date filtering issues
        all_orders = Order.query.all()
        
        summary = {
            'today_orders': len(all_orders),
            'today_revenue': sum(order.total_amount or 0 for order in all_orders),
            'today_commission': sum(order.app_commission or 0 for order in all_orders),
            'today_shop_revenue': sum(order.shop_revenue or 0 for order in all_orders)
        }
        
        return jsonify(summary), 200
    except Exception as e:
        app.logger.error(f"Error getting analytics summary: {str(e)}")
        return jsonify({"error": "Failed to get analytics"}), 500

@app.route('/api/analytics/chart-data')
def analytics_chart_data():
    """Get chart data for analytics"""
    try:
        chart_type = request.args.get('type', 'daily_revenue')
        
        # Simple chart data from database
        if chart_type == 'order_status':
            orders = Order.query.all()
            status_counts = {}
            for order in orders:
                status_counts[order.status] = status_counts.get(order.status, 0) + 1
            
            data = {
                'labels': list(status_counts.keys()),
                'data': list(status_counts.values())
            }
        elif chart_type == 'payment_methods':
            orders = Order.query.all()
            payment_counts = {}
            for order in orders:
                payment_counts[order.payment_method] = payment_counts.get(order.payment_method, 0) + 1
            
            data = {
                'labels': list(payment_counts.keys()),
                'data': list(payment_counts.values())
            }
        else:
            # Return empty data for other chart types for now
            data = {'labels': [], 'data': []}
        
        return jsonify(data), 200
    except Exception as e:
        app.logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({"error": "Failed to get chart data"}), 500

@app.route('/api/export/orders')
def export_orders():
    """Export orders to CSV"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Order ID', 'User Name', 'Phone', 'Total Amount', 'Payment Method', 
                        'Commission', 'Shop Amount', 'Status', 'Created At'])
        
        # Write data
        orders = Order.query.all()
        for order in orders:
            writer.writerow([
                order.id,
                order.user.name if order.user else 'Unknown',
                order.user.phone if order.user else 'N/A',
                order.total_amount,
                order.payment_method,
                order.app_commission,
                order.shop_revenue,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'orders_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        app.logger.error(f"Error exporting orders: {str(e)}")
        return jsonify({"error": "Failed to export orders"}), 500

@app.route('/api/categories', methods=['POST'])
def create_category():
    """Create or update a category"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({"error": "Category name is required"}), 400
        
        category_id = data.get('id') or str(uuid.uuid4())
        
        # Create or update category in database
        category = Category.query.get(category_id)
        if category:
            # Update existing category
            category.name_en = data['name']['en']
            category.name_ar = data['name'].get('ar', data['name']['en'])
            category.description_en = data.get('description', {}).get('en', '')
            category.description_ar = data.get('description', {}).get('ar', '')
            category.image = data.get('image', '/static/images/default.svg')
            category.items = data.get('items', [])
        else:
            # Create new category
            category = Category(
                id=category_id,
                name_en=data['name']['en'],
                name_ar=data['name'].get('ar', data['name']['en']),
                description_en=data.get('description', {}).get('en', ''),
                description_ar=data.get('description', {}).get('ar', ''),
                image=data.get('image', '/static/images/default.svg'),
                items=data.get('items', [])
            )
            db.session.add(category)
        
        db.session.commit()
        
        return jsonify({
            "message": "Category saved successfully",
            "category": category.to_dict()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error creating/updating category: {str(e)}")
        return jsonify({"error": "Failed to save category"}), 500

@app.route('/api/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({"message": "Category deleted successfully"}), 200
        
    except Exception as e:
        app.logger.error(f"Error deleting category: {str(e)}")
        return jsonify({"error": "Failed to delete category"}), 500

@app.route('/api/categories/<category_id>/items', methods=['POST'])
def add_category_item(category_id):
    """Add item to category"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({"error": "Item name is required"}), 400
        
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404
        
        # Add new item to category items
        if not category.items:
            category.items = []
        
        new_item = {
            "id": str(uuid.uuid4()),
            "name": data['name'],
            "price": data.get('price', 0)
        }
        
        category.items.append(new_item)
        db.session.commit()
        
        return jsonify({
            "message": "Item added successfully",
            "item": new_item
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error adding item to category: {str(e)}")
        return jsonify({"error": "Failed to add item"}), 500

@app.route('/api/categories/<category_id>/items/<item_id>', methods=['DELETE'])
def delete_category_item(category_id, item_id):
    """Delete item from category"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404
        
        if not category.items:
            return jsonify({"error": "Item not found"}), 404
        
        # Remove item from category
        category.items = [item for item in category.items if item.get('id') != item_id]
        db.session.commit()
        
        return jsonify({"message": "Item deleted successfully"}), 200
        
    except Exception as e:
        app.logger.error(f"Error deleting item from category: {str(e)}")
        return jsonify({"error": "Failed to delete item"}), 500

# Reports API endpoints
@app.route('/api/reports/orders')
def get_orders_report():
    """Get detailed orders report with filtering"""
    try:
        # Get date filters from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Order.query
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Add 1 day to include the end date
            end_date = end_date + timedelta(days=1)
            query = query.filter(Order.created_at < end_date)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        # Format detailed report data
        report_data = []
        for order in orders:
            order_data = {
                "id": order.id,
                "customer_name": order.user.name if order.user else "Unknown",
                "customer_phone": order.user.phone if order.user else "N/A",
                "date": order.created_at.isoformat(),
                "gps_location": {
                    "latitude": order.user.latitude if order.user else None,
                    "longitude": order.user.longitude if order.user else None
                },
                "payment_method": order.payment_method,
                "status": order.status,
                "items": [
                    {
                        "name_en": item.item_name_en,
                        "name_ar": item.item_name_ar,
                        "unit_price": item.unit_price,
                        "quantity": item.quantity,
                        "total": item.unit_price * item.quantity
                    }
                    for item in order.items
                ],
                "subtotal": order.total_amount,
                "commission_rate": config.COMMISSION_RATE,
                "commission_amount": order.app_commission,
                "shop_revenue": order.shop_revenue
            }
            report_data.append(order_data)
        
        return jsonify({
            "orders": report_data,
            "total_orders": len(report_data),
            "total_revenue": sum(order.total_amount or 0 for order in orders),
            "total_commission": sum(order.app_commission or 0 for order in orders),
            "total_shop_revenue": sum(order.shop_revenue or 0 for order in orders)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting orders report: {str(e)}")
        return jsonify({"error": "Failed to get orders report"}), 500

@app.route('/api/reports/orders/<order_id>')
def get_order_details(order_id):
    """Get detailed information for a specific order"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        order_details = {
            "id": order.id,
            "customer_name": order.user.name if order.user else "Unknown",
            "customer_phone": order.user.phone if order.user else "N/A",
            "date": order.created_at.isoformat(),
            "gps_location": {
                "latitude": order.user.latitude if order.user else None,
                "longitude": order.user.longitude if order.user else None
            },
            "payment_method": order.payment_method,
            "status": order.status,
            "items": [
                {
                    "name_en": item.item_name_en,
                    "name_ar": item.item_name_ar,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "total": item.unit_price * item.quantity,
                    "category": item.category.name_en if item.category else "Unknown"
                }
                for item in order.items
            ],
            "subtotal": order.total_amount,
            "commission_rate": config.COMMISSION_RATE,
            "commission_amount": order.app_commission,
            "app_profit": order.app_commission,
            "shop_revenue": order.shop_revenue
        }
        
        return jsonify(order_details), 200
        
    except Exception as e:
        app.logger.error(f"Error getting order details: {str(e)}")
        return jsonify({"error": "Failed to get order details"}), 500

@app.route('/api/reports/export')
def export_detailed_report():
    """Export detailed report as CSV"""
    try:
        # Get date filters from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        lang = request.args.get('lang', 'en')
        
        query = Order.query
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)
            query = query.filter(Order.created_at < end_date)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers based on language
        commission_percent = int(config.COMMISSION_RATE * 100)
        shop_percent = int(config.SHOP_RATE * 100)
        
        if lang == 'ar':
            headers = ['رقم الطلب', 'اسم العميل', 'رقم الهاتف', 'التاريخ', 'طريقة الدفع', 
                      'المبلغ الإجمالي', f'العمولة ({commission_percent}%)', f'ربح المتجر ({shop_percent}%)', 'الحالة']
        else:
            headers = ['Order ID', 'Customer Name', 'Phone', 'Date', 'Payment Method', 
                      'Total Amount', f'Commission ({commission_percent}%)', f'Shop Revenue ({shop_percent}%)', 'Status']
        
        writer.writerow(headers)
        
        # Write order data
        for order in orders:
            writer.writerow([
                order.id,
                order.user.name if order.user else 'Unknown',
                order.user.phone if order.user else 'N/A',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.payment_method,
                f"{order.total_amount:.2f} LE",
                f"{order.app_commission:.2f} LE",
                f"{order.shop_revenue:.2f} LE",
                order.status
            ])
        
        output.seek(0)
        
        filename = f'orders_report_{datetime.now().strftime("%Y%m%d")}.csv'
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        app.logger.error(f"Error exporting detailed report: {str(e)}")
        return jsonify({"error": "Failed to export report"}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload category image"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create upload directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file.save(filepath)
            
            return jsonify({
                "message": "File uploaded successfully",
                "url": f"/static/uploads/{filename}"
            }), 200
        else:
            return jsonify({"error": "Invalid file type"}), 400
            
    except Exception as e:
        app.logger.error(f"Error uploading image: {str(e)}")
        return jsonify({"error": "Failed to upload image"}), 500

# Enhanced Financial Reporting Endpoints
@app.route('/api/reports/financial-summary')
def financial_summary():
    """Get comprehensive financial summary with detailed breakdowns"""
    try:
        # Get date filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period = request.args.get('period', 'all')  # daily, weekly, monthly, all
        
        query = Order.query
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)
            query = query.filter(Order.created_at < end_date)
        
        orders = query.all()
        
        # Calculate totals
        total_orders = len(orders)
        total_revenue = sum(order.total_amount or 0 for order in orders)
        total_commission = sum(order.app_commission or 0 for order in orders)
        total_shop_revenue = sum(order.shop_revenue or 0 for order in orders)
        
        # Payment method breakdown
        payment_methods = {}
        for order in orders:
            method = order.payment_method
            if method not in payment_methods:
                payment_methods[method] = {
                    'count': 0,
                    'revenue': 0,
                    'commission': 0,
                    'shop_revenue': 0
                }
            payment_methods[method]['count'] += 1
            payment_methods[method]['revenue'] += order.total_amount or 0
            payment_methods[method]['commission'] += order.app_commission or 0
            payment_methods[method]['shop_revenue'] += order.shop_revenue or 0
        
        # Category/Service breakdown
        service_breakdown = {}
        for order in orders:
            for item in order.items:
                service_name = item.item_name_en
                if service_name not in service_breakdown:
                    service_breakdown[service_name] = {
                        'count': 0,
                        'quantity': 0,
                        'revenue': 0,
                        'average_price': 0
                    }
                service_breakdown[service_name]['count'] += 1
                service_breakdown[service_name]['quantity'] += item.quantity
                service_breakdown[service_name]['revenue'] += item.quantity * item.unit_price
                service_breakdown[service_name]['average_price'] = service_breakdown[service_name]['revenue'] / service_breakdown[service_name]['quantity']
        
        # Order status breakdown
        status_breakdown = {}
        for order in orders:
            status = order.status
            if status not in status_breakdown:
                status_breakdown[status] = {
                    'count': 0,
                    'revenue': 0
                }
            status_breakdown[status]['count'] += 1
            status_breakdown[status]['revenue'] += order.total_amount or 0
        
        # Period analysis
        period_analysis = {}
        if period == 'daily':
            for order in orders:
                date_key = order.created_at.date().isoformat()
                if date_key not in period_analysis:
                    period_analysis[date_key] = {
                        'orders': 0,
                        'revenue': 0,
                        'commission': 0,
                        'shop_revenue': 0
                    }
                period_analysis[date_key]['orders'] += 1
                period_analysis[date_key]['revenue'] += order.total_amount or 0
                period_analysis[date_key]['commission'] += order.app_commission or 0
                period_analysis[date_key]['shop_revenue'] += order.shop_revenue or 0
        
        return jsonify({
            'summary': {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'total_commission': round(total_commission, 2),
                'total_shop_revenue': round(total_shop_revenue, 2),
                'commission_rate': config.COMMISSION_RATE,
                'shop_rate': config.SHOP_RATE,
                'currency': config.CURRENCY_SYMBOL,
                'supported_payment_methods': config.SUPPORTED_PAYMENT_METHODS
            },
            'payment_methods': payment_methods,
            'service_breakdown': service_breakdown,
            'status_breakdown': status_breakdown,
            'period_analysis': period_analysis
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error getting financial summary: {str(e)}")
        return jsonify({"error": "Failed to get financial summary"}), 500

@app.route('/api/reports/config')
def get_system_config():
    """Get system configuration for reports"""
    try:
        return jsonify({
            'commission_rate': config.COMMISSION_RATE,
            'shop_rate': config.SHOP_RATE,
            'currency_symbol': config.CURRENCY_SYMBOL,
            'currency_code': config.CURRENCY_CODE,
            'supported_payment_methods': config.SUPPORTED_PAYMENT_METHODS,
            'default_payment_method': config.DEFAULT_PAYMENT_METHOD,
            'system_name': config.SYSTEM_NAME,
            'system_name_en': config.SYSTEM_NAME_EN,
            'order_statuses': config.ORDER_STATUSES
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting system config: {str(e)}")
        return jsonify({"error": "Failed to get system config"}), 500
