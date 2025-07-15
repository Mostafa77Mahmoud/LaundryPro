import os
import csv
import io
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app
from models import data_store, User, Order, Category
from analytics import AnalyticsEngine

# Initialize analytics engine
analytics = AnalyticsEngine(data_store)

@app.route('/')
def dashboard():
    """Main dashboard view"""
    today_stats = analytics.get_today_summary()
    return render_template('dashboard.html', stats=today_stats)

@app.route('/analytics')
def analytics_page():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/orders')
def orders_page():
    """Orders management page"""
    orders = list(data_store.orders.values())
    # Sort by creation date, newest first
    orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Get user info for each order
    for order in orders:
        user = data_store.users.get(order.user_id)
        order.user_info = user.to_dict() if user else {"name": "Unknown", "phone": "N/A"}
    
    return render_template('orders.html', orders=orders)

@app.route('/categories')
def categories_page():
    """Categories management page"""
    categories = list(data_store.categories.values())
    return render_template('categories.html', categories=categories)

@app.route('/reports')
def reports_page():
    """Reports and export page"""
    return render_template('reports.html')

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
        
        data_store.users[user.id] = user
        
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
        categories = []
        for category in data_store.categories.values():
            categories.append({
                "id": category["id"],
                "name": category["name"],
                "description": category["description"],
                "image": category["image"],
                "items": category["items"]
            })
        
        return jsonify({"categories": categories}), 200
        
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
        if data['user_id'] not in data_store.users:
            return jsonify({"error": "User not found"}), 404
        
        # Calculate total prices for items
        processed_items = []
        for item in data['items']:
            total_price = item['quantity'] * item['unit_price']
            processed_items.append({
                "category_id": item.get('category_id'),
                "item_name": item['item_name'],
                "quantity": item['quantity'],
                "unit_price": item['unit_price'],
                "total_price": total_price
            })
        
        order = Order(
            user_id=data['user_id'],
            items=processed_items,
            payment_method=data.get('payment_method', 'cash')
        )
        
        data_store.orders[order.id] = order
        
        return jsonify({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "message": "Order created successfully"
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": "Failed to create order"}), 500

@app.route('/api/orders/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Get orders for a specific user"""
    try:
        user_orders = [order.to_dict() for order in data_store.orders.values() 
                      if order.user_id == user_id]
        
        # Sort by creation date, newest first
        user_orders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({"orders": user_orders}), 200
        
    except Exception as e:
        app.logger.error(f"Error getting user orders: {str(e)}")
        return jsonify({"error": "Failed to get orders"}), 500

@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({"error": "Status is required"}), 400
        
        if order_id not in data_store.orders:
            return jsonify({"error": "Order not found"}), 404
        
        valid_statuses = ['pending', 'washing', 'ready', 'delivered']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
        order = data_store.orders[order_id]
        order.update_status(data['status'])
        
        return jsonify({
            "message": "Order status updated successfully",
            "new_status": order.status
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error updating order status: {str(e)}")
        return jsonify({"error": "Failed to update order status"}), 500

@app.route('/api/chat', methods=['POST'])
def chatbot():
    """Simple chatbot for price inquiries and order tracking"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        user_id = data.get('user_id')
        
        response = {"message": "I'm sorry, I didn't understand that. You can ask about prices or track your orders."}
        
        # Price inquiries
        if any(word in message for word in ['price', 'cost', 'how much', 'سعر']):
            if 'carpet' in message or 'سجاد' in message:
                response = {"message": "Carpet cleaning prices: Small Rug 40 SAR, Medium Carpet 70 SAR, Large Carpet 100 SAR, Persian Rug 150 SAR"}
            elif 'clothes' in message or 'ملابس' in message:
                response = {"message": "Women's clothing prices: Dress 25 SAR, Blouse 15 SAR, Skirt 20 SAR, Formal Suit 50 SAR"}
            elif 'upholstery' in message or 'انتريه' in message:
                response = {"message": "Upholstery cleaning prices: Single Chair 30 SAR, 2-Seater Sofa 80 SAR, 3-Seater Sofa 120 SAR"}
            elif 'bedding' in message or 'بطانية' in message:
                response = {"message": "Bedding prices: Single Blanket 35 SAR, Double Blanket 50 SAR, Comforter 60 SAR, Pillow 10 SAR"}
            else:
                response = {"message": "We offer carpet cleaning, women's clothing, upholstery cleaning, and bedding services. What would you like to know about?"}
        
        # Order tracking
        elif any(word in message for word in ['order', 'track', 'where', 'status', 'طلب']):
            if user_id:
                user_orders = [order for order in data_store.orders.values() if order.user_id == user_id]
                if user_orders:
                    latest_order = max(user_orders, key=lambda x: x.created_at)
                    response = {"message": f"Your latest order (#{latest_order.id[:8]}) is currently: {latest_order.status}"}
                else:
                    response = {"message": "You don't have any orders yet. Would you like to place one?"}
            else:
                response = {"message": "Please provide your user ID to track your orders."}
        
        # New order request
        elif any(word in message for word in ['wash', 'clean', 'order', 'want', 'need', 'غسيل']):
            response = {"message": "I'd be happy to help you place an order! Please use the mobile app to select your items and quantities."}
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error in chatbot: {str(e)}")
        return jsonify({"error": "Chatbot service unavailable"}), 500

@app.route('/api/analytics/summary')
def analytics_summary():
    """Get analytics summary for dashboard"""
    try:
        summary = analytics.get_today_summary()
        return jsonify(summary), 200
    except Exception as e:
        app.logger.error(f"Error getting analytics summary: {str(e)}")
        return jsonify({"error": "Failed to get analytics"}), 500

@app.route('/api/analytics/chart-data')
def analytics_chart_data():
    """Get chart data for analytics"""
    try:
        chart_type = request.args.get('type', 'daily_revenue')
        days = int(request.args.get('days', 7))
        
        if chart_type == 'daily_revenue':
            data = analytics.get_daily_revenue_chart(days)
        elif chart_type == 'payment_methods':
            data = analytics.get_payment_methods_chart()
        elif chart_type == 'service_popularity':
            data = analytics.get_service_popularity_chart()
        elif chart_type == 'order_status':
            data = analytics.get_order_status_chart()
        else:
            return jsonify({"error": "Invalid chart type"}), 400
        
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
        for order in data_store.orders.values():
            user = data_store.users.get(order.user_id)
            writer.writerow([
                order.id,
                user.name if user else 'Unknown',
                user.phone if user else 'N/A',
                order.total_amount,
                order.payment_method,
                order.commission_amount,
                order.shop_amount,
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
        
        category_id = data.get('id') or str(uuid.uuid4())
        
        category_data = {
            "id": category_id,
            "name": data['name'],
            "description": data['description'],
            "image": data.get('image', '/static/images/default.svg'),
            "items": data['items']
        }
        
        data_store.categories[category_id] = category_data
        
        return jsonify({"message": "Category saved successfully", "id": category_id}), 200
        
    except Exception as e:
        app.logger.error(f"Error saving category: {str(e)}")
        return jsonify({"error": "Failed to save category"}), 500

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
