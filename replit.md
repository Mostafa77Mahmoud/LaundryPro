# Laundry Service Management System

## Overview

This is a Flask-based web application for managing a laundry service business. The system provides an admin dashboard for managing orders, categories, analytics, and reports. It's designed to handle multiple service categories (carpet cleaning, women's clothing, upholstery cleaning) with bilingual support (English/Arabic) and includes features for order tracking, revenue analytics, and commission management.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### July 15, 2025 - Database Migration Complete
- ✓ Migrated from in-memory data store to PostgreSQL database
- ✓ Created SQLAlchemy models (User, Category, Order, OrderItem)
- ✓ Updated all API endpoints to use database queries
- ✓ Fixed template variables to match new database structure
- ✓ Maintained commission system (15% app, 85% shop)
- ✓ Preserved bilingual support with proper RTL layout

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) with Gunicorn WSGI deployment
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Data Models**: User, Category, Order, OrderItem with proper relationships
- **API Structure**: RESTful endpoints for mobile app integration
- **CORS**: Enabled for cross-origin requests from mobile applications
- **File Handling**: Support for image uploads with size limits (16MB max)

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript Libraries**: 
  - Chart.js for analytics visualization
  - Font Awesome for icons
- **Theme Support**: Dark/light mode with localStorage persistence
- **Internationalization**: Bilingual support (English/Arabic) with RTL layout

## Key Components

### Data Models
- **DataStore**: Central in-memory storage manager
- **User**: Customer information without authentication
- **Order**: Order management with status tracking
- **Category**: Service categories with bilingual names and pricing

### Analytics Engine
- **Daily Revenue Tracking**: Today's summary with revenue, commission, and order counts
- **Chart Data Generation**: Time-series data for dashboard visualization
- **Status Analytics**: Order status breakdown and payment method analysis

### Service Categories
- **Carpet Cleaning**: Various rug sizes with different pricing
- **Women's Clothing**: Delicate clothing items
- **Upholstery Cleaning**: Furniture cleaning services
- **Bilingual Support**: All categories support English/Arabic names and descriptions

### File Management
- **Image Uploads**: Category images stored in `/static/uploads/`
- **Static Assets**: CSS, JavaScript, and default images in `/static/`
- **Security**: Filename sanitization using Werkzeug's secure_filename

## Data Flow

### Order Processing
1. Mobile app sends order data via API
2. Order created with pending status
3. Admin updates status through dashboard
4. Real-time updates available through polling

### Category Management
1. Default categories initialized on startup
2. Admin can add/edit categories through dashboard
3. Image uploads processed and stored locally
4. Categories served to mobile app via API

### Analytics Processing
1. Real-time calculation of daily metrics
2. Historical data aggregation for charts
3. Commission and revenue tracking
4. Export functionality for reports

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-CORS**: Cross-origin resource sharing
- **Werkzeug**: WSGI utilities and security

### Frontend Libraries
- **Bootstrap 5**: UI framework
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library

### File Storage
- Local filesystem for uploaded images
- Static file serving through Flask

## Deployment Strategy

### Current Setup
- **Development Server**: Flask built-in server on port 5000
- **Host Configuration**: Configured for 0.0.0.0 to accept external connections
- **Debug Mode**: Enabled for development
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxy

### Production Considerations
- No persistent database (data lost on restart)
- In-memory storage not suitable for production
- File uploads stored locally (not cloud-ready)
- Session secret should be environment variable in production

### Scalability Limitations
- Single-threaded Flask development server
- No database persistence
- No user authentication or authorization
- Limited to single-instance deployment

### Recommended Production Changes
- Implement database persistence (PostgreSQL with Drizzle ORM)
- Add proper authentication system
- Use cloud storage for file uploads
- Deploy with WSGI server (Gunicorn)
- Add Redis for session management
- Implement proper logging and monitoring