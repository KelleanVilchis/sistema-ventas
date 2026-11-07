from django.db import models
from apps.accounts.models import AppUser
# Create your models here.

class Currency(models.Model): 
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    created_by = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_categories')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
                                        
    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, related_name='products', null=True)
    purchase_price= models.DecimalField(max_digits=10, decimal_places=2)
    sale_price= models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, null=True,on_delete=models.SET_NULL, related_name='products')
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_products')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name