from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currencies/create/', views.CreateCurrencyView.as_view(), name='currency_create'),
    path('currencies/edit/<int:currency_id>/', views.UpdateCurrencyView.as_view(), name='currency_edit'),
    path('currencies/delete/<int:currency_id>/', views.DeleteCurrencyView.as_view(), name='currency_delete'),

    path('categories/', views.ProductCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CreateProductCategoryView.as_view(), name='category_create'),
    path('categories/edit/<int:category_id>/', views.UpdateProductCategoryView.as_view(), name='category_edit'),
    path('categories/delete/<int:category_id>/', views.DeleteProductCategoryView.as_view(), name='category_delete'),

    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.CreateProductView.as_view(), name='product_create'),
    path('products/edit/<int:product_id>/', views.UpdateProductView.as_view(), name='product_edit'),
    path('products/delete/<int:product_id>/', views.DeleteProductView.as_view(), name='product_delete'),
]