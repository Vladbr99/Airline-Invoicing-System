from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='home'),
    path('login/', views.login_view, name='login'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/add-item/', views.add_invoice_item, name='add_invoice_item'),
    path('invoices/<int:invoice_id>/update-status/', views.update_invoice_status, name='update_invoice_status'),
    path('reports/customer/', views.customer_report, name='customer_report'),
]
