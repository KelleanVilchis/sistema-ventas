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

]
