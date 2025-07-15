from database import create_app, db, User, Order, Category, OrderItem

app = create_app()

# Import routes after app is created
import routes