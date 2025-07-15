# Laundry Service Management System

## Overview

This is a Flask-based web application for managing a laundry service business. The system provides an admin dashboard for managing orders, categories, analytics, and reports. It's designed to handle multiple service categories (carpet cleaning, women's clothing, upholstery cleaning) with bilingual support (English/Arabic) and includes features for order tracking, revenue analytics, and commission management.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### July 15, 2025 - Major System Enhancements Complete
- ✓ Migrated from in-memory data store to PostgreSQL database  
- ✓ Updated commission system to 30% app, 70% shop (from 15%/85%)
- ✓ Enhanced bilingual support with RTL layout and language toggle
- ✓ Added full CRUD operations for categories and items
- ✓ Implemented image upload functionality for categories
- ✓ Created comprehensive financial reporting system
- ✓ Added date filtering for analytics and reports
- ✓ Built detailed order tracking with GPS location support
- ✓ Enhanced export functionality (CSV with Arabic support)
- ✓ Added dark/light theme toggle with localStorage persistence
- ✓ Improved dashboard with real-time PostgreSQL data integration
- ✓ Implemented secure admin login system with session management
- ✓ Added comprehensive Arabic translations for all UI elements
- ✓ Enabled RTL layout support for Arabic language

### July 15, 2025 - Replit Migration Complete
- ✓ Migrated from Replit Agent to standard Replit environment
- ✓ Updated Flask configuration to use environment variables
- ✓ Fixed session secret key configuration for secure login
- ✓ Enhanced dark mode CSS for better text visibility
- ✓ Created comprehensive Arabic documentation (manual_ar.md)
- ✓ Application now runs successfully on Replit with PostgreSQL

### July 15, 2025 - Configuration System Complete
- ✓ Centralized all system configuration in config.py
- ✓ Made commission rates fully configurable (30% app, 70% shop)
- ✓ Implemented strict payment method validation (Cash and Mobile only)
- ✓ Added comprehensive financial reporting with detailed breakdowns
- ✓ Enhanced API endpoints with configuration integration
- ✓ Added bilingual chatbot with dynamic pricing from config
- ✓ Completed comprehensive API testing - all endpoints working
- ✓ Fixed missing API routes and improved error handling
- ✓ Validated all financial calculations use config values

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

### Admin Authentication Setup
- **Admin Password**: Default password is `laundry_admin_2025`
- **Configuration**: Change admin password in `config.py` file
- **Location**: Update `ADMIN_SECRET` variable in `config.py`
- **Security**: Password is hardcoded and must be changed in source code
- **Session Management**: Uses Flask sessions with secure cookies

### Recommended Production Changes
- Change default admin password in `config.py`
- Use environment variables for admin password
- Implement proper user role management
- Add password complexity requirements
- Deploy with WSGI server (Gunicorn) - ✓ Already implemented
- Add Redis for session management
- Implement proper logging and monitoring