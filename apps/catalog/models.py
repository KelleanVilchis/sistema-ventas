from django.db import models
from apps.accounts.models import AppUser
from apps.company.models import Company
# Create your models here.

class Currency(models.Model): 
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, related_name='currencies')
    created_by = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='categories', null=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_categories')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
                                        
    def __str__(self):
        return self.name

class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        INACTIVE = "INACTIVE", "Inactivo"

    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        related_name="products",
        null=True,
    )
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(
        Currency, null=True, on_delete=models.SET_NULL, related_name="products"
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, related_name="products", null=True
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name="created_products"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def deactivate(self):
        self.status = self.Status.INACTIVE
        self.save(update_fields=["status", "date_updated"])

    def activate(self):
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status", "date_updated"])