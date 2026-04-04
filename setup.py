#!/usr/bin/env python
"""
SmartPOS Cloud Setup Script
Runs automatically on every Render deploy (via Procfile release command).
Safe to run multiple times — all operations are idempotent.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartpos.settings')

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from pos.models import Store, UserProfile, Category, Supplier, Product

print("=" * 50)
print("  SmartPOS — Initial Setup")
print("=" * 50)

# Run migrations
print("\n[1/5] Running migrations...")
call_command('migrate', verbosity=0)
print("      ✓ Database tables created")

# Create default store
print("\n[2/5] Creating default store...")
store, created = Store.objects.get_or_create(
    name="Main Store",
    defaults={'address': '123 Main Street', 'phone': '+1234567890', 'tax_rate': 8.00}
)
if created:
    print("      ✓ Main Store created")
else:
    print("      ✓ Main Store already exists")

# Create admin user
print("\n[3/5] Creating admin user...")
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@smartpos.com', 'admin123')
    admin.first_name = 'System'
    admin.last_name = 'Admin'
    admin.save()
    UserProfile.objects.create(user=admin, role='admin', store=store)
    print("      ✓ Admin user created (username: admin / password: admin123)")
else:
    print("      ✓ Admin user already exists")

# Create sample cashier
if not User.objects.filter(username='cashier').exists():
    cashier = User.objects.create_user('cashier', 'cashier@smartpos.com', 'cashier123')
    cashier.first_name = 'John'
    cashier.last_name = 'Doe'
    cashier.save()
    UserProfile.objects.create(user=cashier, role='cashier', store=store, pin='1234')
    print("      ✓ Sample cashier created (username: cashier / password: cashier123 / PIN: 1234)")

# Create default categories
print("\n[4/5] Creating sample categories...")
categories = ['Dairy', 'Bakery', 'Beverages', 'Snacks', 'Produce', 'Frozen', 'Household', 'Personal Care']
for cat_name in categories:
    Category.objects.get_or_create(name=cat_name, store=store)
print(f"      ✓ {len(categories)} categories created")

# Create sample supplier
print("\n[5/5] Creating sample data...")
supplier, _ = Supplier.objects.get_or_create(
    name="Default Supplier",
    defaults={'phone': '+1234567890', 'email': 'supplier@example.com', 'store': store}
)

# Create sample products
sample_products = [
    {'name': 'Whole Milk 1L', 'barcode': '8901001001001', 'category': 'Dairy', 'price': 2.50, 'stock': 50},
    {'name': 'White Bread', 'barcode': '8901002002002', 'category': 'Bakery', 'price': 1.80, 'stock': 30},
    {'name': 'Orange Juice 1L', 'barcode': '8901003003003', 'category': 'Beverages', 'price': 3.20, 'stock': 25},
    {'name': 'Potato Chips 100g', 'barcode': '8901004004004', 'category': 'Snacks', 'price': 1.50, 'stock': 40},
    {'name': 'Banana 1kg', 'barcode': '8901005005005', 'category': 'Produce', 'price': 0.90, 'stock': 8},
    {'name': 'Butter 250g', 'barcode': '8901006006006', 'category': 'Dairy', 'price': 2.20, 'stock': 5},
    {'name': 'Mineral Water 500ml', 'barcode': '8901007007007', 'category': 'Beverages', 'price': 0.75, 'stock': 100},
    {'name': 'Chocolate Bar 50g', 'barcode': '8901008008008', 'category': 'Snacks', 'price': 1.20, 'stock': 0},
]

created_count = 0
for p_data in sample_products:
    if not Product.objects.filter(barcode=p_data['barcode']).exists():
        cat = Category.objects.filter(name=p_data['category'], store=store).first()
        Product.objects.create(
            name=p_data['name'],
            barcode=p_data['barcode'],
            price=p_data['price'],
            cost_price=round(p_data['price'] * 0.6, 2),
            stock_quantity=p_data['stock'],
            low_stock_threshold=10,
            category=cat,
            supplier=supplier,
            store=store,
        )
        created_count += 1

print(f"      ✓ {created_count} sample products created")

# Collect static files
print("\nCollecting static files...")
call_command('collectstatic', verbosity=0, interactive=False)
print("      ✓ Static files collected")

print("\n" + "=" * 50)
print("  ✓ Setup complete!")
print("=" * 50)
print("\n  Start server:  python manage.py runserver")
print("  Or production: gunicorn smartpos.wsgi:application")
print("\n  Login credentials:")
print("  → Admin:   admin / admin123")
print("  → Cashier: cashier / cashier123")
print("\n  ⚠ Change passwords before deploying to production!")
print("=" * 50)