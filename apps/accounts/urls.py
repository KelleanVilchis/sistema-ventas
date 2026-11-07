from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('', views.ListUsersView.as_view(), name='list_users'),
    path('delete_user/<int:user_id>/', views.DeleteUserView.as_view(), name='delete_user'),
    path('edit_user/<int:user_id>/', views.EditUserView.as_view(), name='edit_user'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),

]
