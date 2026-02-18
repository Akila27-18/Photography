from django.urls import path
from . import views

app_name = "invoices"

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/<int:project_id>/', views.create_invoice, name='create_invoice'),
    path('<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('download/<int:invoice_id>/', views.download_invoice, name='download_invoice'),
]
