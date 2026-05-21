from django.db import models


class MenuItem(models.Model):
    name = models.CharField(max_length=200, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class CafeCategory(models.TextChoices):
    BEVERAGES = 'beverages', 'Beverages'
    INGREDIENTS = 'ingredients', 'Ingredients'
    SNACKS = 'snacks', 'Snacks'
    SUPPLIES = 'supplies', 'Supplies'
    EQUIPMENT = 'equipment', 'Equipment'


class CafeInventoryItem(models.Model):
    """Inventory model for cafe supplies and equipment."""
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=CafeCategory.choices,
        default=CafeCategory.SUPPLIES,
    )
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=[
            ('good', 'Good / In Stock'),
            ('maintenance', 'Needs Maintenance'),
            ('out_of_stock', 'Out of Stock'),
            ('low_stock', 'Low Stock'),
        ],
        default='good',
    )
    unit = models.CharField(
        max_length=20,
        default='pcs',
        help_text='Unit (e.g., kg, L, pcs, packets)'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def category_label(self):
        return self.get_category_display()


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',          'Pending'),
        ('fulfilled',        'Fulfilled'),
        ('payment_received', 'Payment Received'),
    ]

    table_number        = models.CharField(max_length=20)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at          = models.DateTimeField(auto_now_add=True)
    fulfilled_at        = models.DateTimeField(null=True, blank=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Order #{self.pk} — Table {self.table_number} ({self.status})"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item  = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    name       = models.CharField(max_length=200)   # snapshot / custom item name
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity   = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}× {self.name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
