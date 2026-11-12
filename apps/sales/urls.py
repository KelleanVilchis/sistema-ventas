from django.urls import path
from . import views

app_name = 'sales'
urlpatterns = [
    path('combos/', views.ComboListView.as_view(), name='combo_list'),
    path('combos/create/', views.CreateComboView.as_view(), name='combo_create'),
    path('combos/edit/<int:combo_id>/', views.UpdateComboView.as_view(), name='combo_edit'),
    path('combos/delete/<int:combo_id>/', views.DeleteComboView.as_view(), name='combo_delete'),

    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.CreateOrderView.as_view(), name='order_create'),
    path('orders/edit/<int:order_id>/', views.UpdateOrderView.as_view(), name='order_edit'),
    path('orders/delete/<int:order_id>/', views.DeleteOrderView.as_view(), name='order_delete'),
    path("orders/<int:pk>/complete/", views.OrderCompleteView.as_view(), name="order_complete"),
    # apps/sales/urls.py
    path("orders/<int:pk>/sell/",views.OrderSellView.as_view(),name="order_sell",),

    path('sales/', views.SaleListView.as_view(), name='sale_list'),
    path('sales/create/', views.CreateSaleView.as_view(), name='sale_create'),
    path('sales/edit/<int:sale_id>/', views.UpdateSaleView.as_view(), name='sale_edit'),
    path('sales/delete/<int:sale_id>/', views.DeleteSaleView.as_view(), name='sale_delete'),

    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.CreateExpenseView.as_view(), name='expense_create'),
    path('expenses/edit/<int:expense_id>/', views.UpdateExpenseView.as_view(), name='expense_edit'),
    path('expenses/delete/<int:expense_id>/', views.DeleteExpenseView.as_view(), name='expense_delete'),
]
