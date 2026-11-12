import uuid
from django.db import models, transaction
from django.utils import timezone
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
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default="SOLD",db_index=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="sales", null=True)
    date_sale = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_sales')

    def __str__(self):
        return f"Sale {self.id} - Order {self.order.id}"

    def save(self, *args, **kwargs):
        if not self.folio_number:
            self.folio_number = self._generate_folio()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_folio():
        fecha = timezone.now().strftime("%Y%m%d")
        aleatorio = uuid.uuid4().hex[:6].upper()
        return f"SAL-{fecha}-{aleatorio}"

    def __str__(self):
        return f"{self.folio_number} — Pedido {self.order_id}"


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


# ═══════════════════════════════════════════════════════════════════
# NUEVOS MODELOS — Devoluciones y Mermas
# ═══════════════════════════════════════════════════════════════════


class SaleReturn(models.Model):
    """
    Cabecera de una devolución asociada a una venta.
    Agrupa todos los productos devueltos en una sola operación.
    """
    STATUS_CHOICES = [
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]

    folio_number = models.CharField(
        "folio", max_length=40, unique=True, blank=True, editable=False
    )
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='returns')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='returns')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='returns')
    total_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='COMPLETED')
    created_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name='created_returns'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.folio_number:
            fecha = timezone.now().strftime("%Y%m%d")
            aleatorio = uuid.uuid4().hex[:6].upper()
            self.folio_number = f"RET-{fecha}-{aleatorio}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio_number} — Venta {self.sale.folio_number}"


class SaleReturnItem(models.Model):
    """
    Detalle de cada producto devuelto dentro de una SaleReturn.
    `destination` define si el producto regresa al inventario o no.
    """
    DESTINATIONS = [
        ('RESTOCK', 'Reingresa a inventario'),
        ('DAMAGED', 'Producto dañado (no reingresa)'),
    ]

    sale_return = models.ForeignKey(
        SaleReturn, on_delete=models.CASCADE, related_name='items'
    )
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.SET_NULL, null=True, related_name='return_items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='return_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    destination = models.CharField(
        max_length=10, choices=DESTINATIONS, default='RESTOCK'
    )

    def __str__(self):
        return f"{self.quantity} × {self.product} ({self.get_destination_display()})"


class InventoryWriteOff(models.Model):
    """
    Registro de productos que salen del inventario sin venta:
    dañados, caducados, perdidos, robados, etc.
    
    Si `affects_inventory=True` (default), descuenta del stock actual
    creando un InventoryMovement(OUT) automáticamente.
    
    Si se crea desde una devolución DAMAGED (el producto nunca volvió
    al stock), usar `affects_inventory=False` para que solo quede el
    registro de trazabilidad sin tocar el inventario.
    """
    REASONS = [
        ('DAMAGED', 'Dañado'),
        ('EXPIRED', 'Caducado'),
        ('LOST', 'Perdido'),
        ('THEFT', 'Robo'),
        ('OTHER', 'Otro'),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='write_offs'
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='write_offs'
    )
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=REASONS)
    affects_inventory = models.BooleanField(
        default=True,
        help_text="Si es True, descuenta del stock actual automáticamente.",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name='created_write_offs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new and self.affects_inventory:
                concept = f"Merma: {self.get_reason_display()}"
                if self.notes:
                    concept += f" — {self.notes[:50]}"
                InventoryMovement.objects.create(
                    product=self.product,
                    movement_type=InventoryMovementType.OUT,
                    quantity=self.quantity,
                    company=self.company,
                    concept=concept,
                    created_by=self.created_by,
                )

    def __str__(self):
        return f"{self.get_reason_display()} — {self.product} ({self.quantity})"