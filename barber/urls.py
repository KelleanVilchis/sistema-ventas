"""
URL configuration for barber project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from . import views

# Nota: Se eliminó 'app_name = 'barber'' de aquí porque el archivo raíz no lo requiere.

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('company/', include('apps.company.urls', namespace='company')),
    path('catalog/', include('apps.catalog.urls', namespace='catalog')),
    path('sales/', include('apps.sales.urls', namespace='sales')),
]