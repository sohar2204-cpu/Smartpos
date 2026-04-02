from django.urls import path
from . import views
from .saas_views import (
    register_view,
    superadmin_dashboard,
    superadmin_suspend_store,
    superadmin_activate_store,
    superadmin_login_as,
    superadmin_add_store,
)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('pin-login/', views.pin_login_view, name='pin_login'),
    path('logout/', views.logout_view, name='logout'),

    # Public registration
    path('register/', register_view, name='register'),

    # Superadmin
    path('superadmin/', superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/stores/add/', superadmin_add_store, name='superadmin_add_store'),
    path('superadmin/stores/<int:store_id>/suspend/', superadmin_suspend_store, name='superadmin_suspend_store'),
    path('superadmin/stores/<int:store_id>/activate/', superadmin_activate_store, name='superadmin_activate_store'),
    path('superadmin/stores/<int:store_id>/login-as/', superadmin_login_as, name='superadmin_login_as'),

    # Products
    path('products/', views.product_list, name='products'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/import/', views.product_csv_import, name='product_import'),

    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.category_create, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Barcode Labels
    path('barcode-labels/', views.barcode_labels, name='barcode_labels'),

    # API
    path('api/product/', views.get_product_by_barcode, name='api_product'),
    path('api/products/search/', views.search_products, name='api_search_products'),
    path('api/customer-info/', views.get_customer_info, name='api_customer_info'),

    # POS
    path('pos/', views.pos_view, name='pos'),
    path('pos/checkout/', views.checkout, name='checkout'),

    # Receipts
    path('receipt/<int:sale_id>/', views.receipt_view, name='receipt'),
    path('receipt/<int:sale_id>/pdf/', views.receipt_pdf, name='receipt_pdf'),
    path('receipt/<int:sale_id>/thermal/', views.thermal_receipt, name='thermal_receipt'),
    path('receipt/<int:sale_id>/whatsapp/', views.send_whatsapp, name='send_whatsapp'),

    # Sales
    path('sales/', views.sales_list, name='sales'),
    path('sales/<int:sale_id>/return/', views.process_return, name='process_return'),

    # Customers
    path('customers/', views.customer_list, name='customers'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:supplier_id>/payments/', views.supplier_payments, name='supplier_payments'),

    # Analytics & Reports
    path('analytics/', views.analytics, name='analytics'),
    path('profit/', views.profit_report, name='profit'),
    path('daily-summary/', views.daily_summary_view, name='daily_summary'),
    path('daily-summary/pdf/', views.daily_summary_pdf, name='daily_summary_pdf'),
    path('loyalty/', views.loyalty_report, name='loyalty_report'),

    # Expenses
    path('expenses/', views.expenses_list, name='expenses'),

    # Shift / Cash Drawer
    path('shift/', views.shift_view, name='shift'),

    # Reorder Alerts
    path('reorder/', views.reorder_alerts, name='reorder_alerts'),

    # Export
    path('export/sales/', views.export_sales_csv, name='export_sales'),
    path('export/products/', views.export_products_csv, name='export_products'),

    # Users
    path('users/', views.user_list, name='users'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/pins/', views.manage_pins, name='manage_pins'),
    path('users/reset/', views.reset_cashier, name='reset_cashier'),

    # Stores
    path('stores/', views.store_list, name='stores'),
    path('stores/add/', views.store_add, name='store_add'),

    # Settings
    path('settings/', views.store_settings, name='store_settings'),
    path('whatsapp-settings/', views.whatsapp_settings, name='whatsapp_settings'),

    # Backup & Restore
    path('backup/', views.backup_database, name='backup'),
    path('restore/', views.restore_backup, name='restore_backup'),
    path('cloud-backup/', views.cloud_backup_settings, name='cloud_backup'),

    # Purchase Invoices
    path('purchase/<int:purchase_id>/invoice/', views.purchase_invoice, name='purchase_invoice'),
    path('purchase/<int:purchase_id>/invoice/pdf/', views.purchase_invoice_pdf, name='purchase_invoice_pdf'),

    # Audit Log
    path('audit-log/', views.audit_log_view, name='audit_log'),

    # Tax Engine
    path('tax-rules/', views.tax_rules_view, name='tax_rules'),

    # Currency Settings
    path('currency/', views.currency_settings_view, name='currency_settings'),
    path('currency/live-rate/', views.fetch_live_rate, name='fetch_live_rate'),
    path('currency/save-api-key/', views.save_api_key, name='save_api_key'),
]