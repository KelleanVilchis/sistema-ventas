from django.urls import path
from . import views

app_name = 'company'
urlpatterns = [
    path('', views.ListCompanyView.as_view(), name='company_index'),
    path('create/', views.CreateCompanyView.as_view(), name='company_create'),
    path('edit/<int:pk>/', views.EditCompanyView.as_view(), name='company_edit'),
    path('delete/<int:company_id>/', views.DeleteCompanyView.as_view(), name='company_delete'),
]
