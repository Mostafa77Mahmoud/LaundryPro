import os
import csv
import io
import uuid
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Order, Category, OrderItem
from analytics import AnalyticsEngine

# Initialize analytics engine - commented out for now
# analytics = None

@app.route('/')
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
def analytics_page():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/orders')
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
def categories_page():
    """Categories management page"""
    categories = Category.query.all()
    categories_data = [category.to_dict() for category in categories]
    return render_template('categories.html', categories=categories_data)

@app.route('/reports')
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
        
        # Create order
        order = Order(
            user_id=data['user_id'],
            payment_method=data.get('payment_method', 'cash')
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
        order.app_commission = total_amount * 0.30  # 30% commission
        order.shop_revenue = total_amount * 0.70   # 70% to shop
        
        db.session.commit()
        
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
        user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        user_orders_data = [order.to_dict() for order in user_orders]
        
        return jsonify({"orders": user_orders_data}), 200
        
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
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        valid_statuses = ['pending', 'washing', 'ready', 'delivered']
        if data['status'] not in valid_statuses:
            return jsonify({"error": "Invalid status"}), 400
        
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
                "commission_rate": 0.30,
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
            "commission_rate": 0.30,
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
        if lang == 'ar':
            headers = ['رقم الطلب', 'اسم العميل', 'رقم الهاتف', 'التاريخ', 'طريقة الدفع', 
                      'المبلغ الإجمالي', 'العمولة (30%)', 'ربح المتجر (70%)', 'الحالة']
        else:
            headers = ['Order ID', 'Customer Name', 'Phone', 'Date', 'Payment Method', 
                      'Total Amount', 'Commission (30%)', 'Shop Revenue (70%)', 'Status']
        
        writer.writerow(headers)
        
        # Write order data
        for order in orders:
            writer.writerow([
                order.id,
                order.user.name if order.user else 'Unknown',
                order.user.phone if order.user else 'N/A',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.payment_method,
                order.total_amount,
                order.app_commission,
                order.shop_revenue,
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
