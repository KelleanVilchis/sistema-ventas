from django.db import models
from apps.accounts.models import AppUser
from apps.catalog.models import Product, Currency
from apps.company.models import Company


class Combo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='combos')
    date_start = models.DateTimeField(auto_now_add=True)
    date_end = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_combos')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


    def purchase_price(self):
        return sum(
            item.product.purchase_price * item.quantity
            for item in self.items.all()
            if item.product_id is not None
        )

    def sale_price(self):
        return sum(
            item.product.sale_price * item.quantity
            for item in self.items.all()
            if item.product_id is not None
        )

    def __str__(self):
        return self.name


class ComboItem(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.SET_NULL, null=True, related_name='combo_items')
    quantity = models.PositiveIntegerField()
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_combo_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Item {self.id} - Combo {self.combo.id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('ACCEPTED', 'Aceptado'),
        ('PENDING', 'En espera'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
    ]
    folio_number = models.CharField("folio", max_length=40, unique=True, blank=True, editable=False)    
    customer = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_orders')

    def __str__(self):
        return f"Order {self.id} - {self.status}"
# Create your models here.

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    combo = models.ForeignKey(Combo, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product = models.ForeignKey('catalog.Product', on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Item {self.id} - Order {self.order.id}"





class Sale(models.Model):
    STATUS_CHOICES = [
        ('SOLD', 'VENDIDO'),
        ('RETURNED', 'DEVUELTO'),
        ('CANCELLED', 'CANCELADO'),
        ('PENDING', 'EN ESPERA')
    ]
    folio_number = models.CharField("folio", max_length=40, unique=True, blank=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="sales", null=True)
    date_sale = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_sales')

    def __str__(self):
        return f"Sale {self.id} - Order {self.order.id}"




class Expense(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En espera'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
    ]
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='expenses')
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='expenses')
    date_expense = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_expenses')

    def __str__(self):
        return f"Expense {self.id} - {self.status}"



class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)        
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product} - {self.quantity}"
    

class InventoryMovementType(models.IntegerChoices):
    IN = 1,"Entrada"
    OUT = 2,"Salida"


class InventoryMovement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.SmallIntegerField(choices=InventoryMovementType.choices, default=InventoryMovementType.IN)
    quantity = models.PositiveIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='inventory_movements')
    concept = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        inventory = Inventory.objects.get(product=self.product)

        if self.movement_type == InventoryMovementType.IN:
            inventory.quantity += self.quantity
        elif self.movement_type == InventoryMovementType.OUT:
            if self.quantity > inventory.quantity:
                raise ValueError("No hay suficiente inventario para esta salida.")
            inventory.quantity -= self.quantity

        inventory.save()