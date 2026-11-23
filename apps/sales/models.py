import uuid
from django.db import models
from django.db.models import Sum
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

    def save(self, *args, **kwargs):
        if not self.folio_number:
            self.folio_number = self._generate_folio()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_folio():
        fecha = timezone.now().strftime("%Y%m%d")
        aleatorio = uuid.uuid4().hex[:6].upper()
        return f"ORD-{fecha}-{aleatorio}"

    def __str__(self):
        return f"{self.folio_number} — {self.customer}"


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

    @property
    def returned_quantity(self):
        return self.return_items.aggregate(t=Sum('quantity'))['t'] or 0

    @property
    def available_quantity(self):
        return self.quantity - self.returned_quantity

    @property
    def is_fully_returned(self):
        return self.available_quantity <= 0


class Sale(models.Model):
    STATUS_CHOICES = [
        ('SOLD', 'VENDIDO'),
        ('RETURNED', 'DEVUELTO'),
        ('CANCELLED', 'CANCELADO'),
        ('PENDING', 'EN ESPERA')
    ]
    PAYMENT_CHOICES = [
        ('CASH_MXN', 'Efectivo MXN'),
        ('CASH_USD', 'Efectivo USD'),
        ('MIXED', 'Mixto (MXN + USD)'),
        ('TRANSFER', 'Transferencia'),
    ]

    folio_number = models.CharField("folio", max_length=40, unique=True, blank=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="SOLD", db_index=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="sales", null=True)
    date_sale = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_sales')

    # ─── PAGO ───
    payment_method = models.CharField(
        max_length=15, choices=PAYMENT_CHOICES, default='CASH_MXN'
    )
    paid_mxn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        help_text="TC USD→MXN usado en esta venta"
    )

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
    TYPE_CHOICES = [
        ('INVESTMENT', 'Inversión'),
        ('OPERATIVE', 'Gasto operativo'),
        ('EMERGENCY', 'Emergencia'),
        ('MAINTENANCE', 'Mantenimiento'),
        ('TAXES', 'Impuestos'),
        ('SALARIES', 'Salarios'),
        ('UNNECESSARY', 'Innecesario'),
        ('OTHER', 'Otro'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'En espera'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
    ]
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, related_name='expenses')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='APPROVED')
    expense_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='OPERATIVE', db_index=True)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='expenses')
    date_expense = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_expenses')

    class Meta:
        ordering = ['-date_expense']

    @property
    def is_investment(self):
        return self.expense_type == 'INVESTMENT'

    def __str__(self):
        return f"{self.get_expense_type_display()} - ${self.amount}"


# ═══════════════════════════════════════════════════════════════════
# DEVOLUCIONES (solo registro financiero, sin inventario)
# ═══════════════════════════════════════════════════════════════════


class SaleReturn(models.Model):
    """
    Cabecera de una devolución asociada a una venta.
    Solo registra el reembolso financiero (no toca stock).
    """
    STATUS_CHOICES = [
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]

    folio_number = models.CharField("folio", max_length=40, unique=True, blank=True, editable=False)
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
    Solo guarda cantidades y montos; no hay destino RESTOCK/DAMAGED.
    """
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, related_name='return_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='return_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.product} (${self.subtotal})"




class Shift(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Abierto'),
        ('CLOSED', 'Cerrado'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shifts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', db_index=True)

    # TC congelado al abrir el turno (referencia; cada venta guarda el suyo)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=17.50)

    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    opened_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name='shifts_opened'
    )
    closed_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name='shifts_closed'
    )

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f"Turno {self.id} — {self.opened_at.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_open(self):
        return self.status == 'OPEN'




class ExchangeRateLog(models.Model):
    """
    Historial de cambios del tipo de cambio USD→MXN por empresa.
    Permite auditar quién cambió el TC, cuándo y de qué a qué.
    """
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='exchange_rate_logs'
    )
    old_rate = models.DecimalField(max_digits=10, decimal_places=4)
    new_rate = models.DecimalField(max_digits=10, decimal_places=4)
    changed_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, null=True, related_name='exchange_rate_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.company.name}: {self.old_rate} → {self.new_rate}"