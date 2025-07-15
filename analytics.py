from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

class AnalyticsEngine:
    def __init__(self, data_store):
        self.data_store = data_store
    
    def get_today_summary(self) -> Dict[str, Any]:
        """Get today's key metrics summary"""
        today = datetime.now().date()
        today_orders = [order for order in self.data_store.orders.values() 
                       if order.created_at.date() == today]
        
        total_orders = len(today_orders)
        total_revenue = sum(order.total_amount for order in today_orders)
        total_commission = sum(order.commission_amount for order in today_orders)
        shop_revenue = sum(order.shop_amount for order in today_orders)
        
        # Status breakdown
        status_counts = defaultdict(int)
        for order in today_orders:
            status_counts[order.status] += 1
        
        # Payment method breakdown
        payment_counts = defaultdict(int)
        for order in today_orders:
            payment_counts[order.payment_method] += 1
        
        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2),
            "shop_revenue": round(shop_revenue, 2),
            "status_breakdown": dict(status_counts),
            "payment_breakdown": dict(payment_counts),
            "date": today.isoformat()
        }
    
    def get_daily_revenue_chart(self, days: int = 7) -> Dict[str, Any]:
        """Get daily revenue data for chart"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        daily_data = defaultdict(lambda: {"revenue": 0, "commission": 0, "shop_amount": 0, "orders": 0})
        
        for order in self.data_store.orders.values():
            order_date = order.created_at.date()
            if start_date <= order_date <= end_date:
                daily_data[order_date]["revenue"] += order.total_amount
                daily_data[order_date]["commission"] += order.commission_amount
                daily_data[order_date]["shop_amount"] += order.shop_amount
                daily_data[order_date]["orders"] += 1
        
        # Format for Chart.js
        labels = []
        revenue_data = []
        commission_data = []
        shop_data = []
        order_counts = []
        
        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.strftime('%m/%d'))
            day_data = daily_data[current_date]
            revenue_data.append(round(day_data["revenue"], 2))
            commission_data.append(round(day_data["commission"], 2))
            shop_data.append(round(day_data["shop_amount"], 2))
            order_counts.append(day_data["orders"])
            current_date += timedelta(days=1)
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Total Revenue",
                    "data": revenue_data,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 2
                },
                {
                    "label": "Commission",
                    "data": commission_data,
                    "backgroundColor": "rgba(255, 99, 132, 0.5)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 2
                },
                {
                    "label": "Shop Revenue",
                    "data": shop_data,
                    "backgroundColor": "rgba(75, 192, 192, 0.5)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 2
                }
            ]
        }
    
    def get_payment_methods_chart(self) -> Dict[str, Any]:
        """Get payment methods distribution for pie chart"""
        payment_counts = defaultdict(int)
        payment_revenue = defaultdict(float)
        
        for order in self.data_store.orders.values():
            payment_counts[order.payment_method] += 1
            payment_revenue[order.payment_method] += order.total_amount
        
        labels = list(payment_counts.keys())
        data = list(payment_counts.values())
        revenue_data = [round(payment_revenue[label], 2) for label in labels]
        
        colors = [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)'
        ]
        
        return {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": colors[:len(labels)],
                "borderWidth": 2
            }],
            "revenue_data": revenue_data
        }
    
    def get_service_popularity_chart(self) -> Dict[str, Any]:
        """Get service popularity data"""
        service_counts = defaultdict(int)
        service_revenue = defaultdict(float)
        
        for order in self.data_store.orders.values():
            for item in order.items:
                service_name = item.get('item_name', 'Unknown')
                service_counts[service_name] += item.get('quantity', 1)
                service_revenue[service_name] += item.get('total_price', 0)
        
        # Get top 10 services
        top_services = sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        labels = [service[0] for service in top_services]
        data = [service[1] for service in top_services]
        revenue_data = [round(service_revenue[service[0]], 2) for service in top_services]
        
        return {
            "labels": labels,
            "datasets": [{
                "label": "Quantity Ordered",
                "data": data,
                "backgroundColor": "rgba(153, 102, 255, 0.6)",
                "borderColor": "rgba(153, 102, 255, 1)",
                "borderWidth": 2
            }],
            "revenue_data": revenue_data
        }
    
    def get_order_status_chart(self) -> Dict[str, Any]:
        """Get order status distribution"""
        status_counts = defaultdict(int)
        
        for order in self.data_store.orders.values():
            status_counts[order.status] += 1
        
        labels = list(status_counts.keys())
        data = list(status_counts.values())
        
        colors = {
            'pending': 'rgba(255, 205, 86, 0.8)',
            'washing': 'rgba(54, 162, 235, 0.8)',
            'ready': 'rgba(255, 159, 64, 0.8)',
            'delivered': 'rgba(75, 192, 192, 0.8)'
        }
        
        background_colors = [colors.get(label, 'rgba(201, 203, 207, 0.8)') for label in labels]
        
        return {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": background_colors,
                "borderWidth": 2
            }]
        }
