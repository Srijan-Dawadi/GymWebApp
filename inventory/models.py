from django.db import models


class EquipmentCategory(models.TextChoices):
    DUMBBELLS = 'dumbbells', 'Dumbbells'
    BARBELLS = 'barbells', 'Barbells & Bars'
    WEIGHT_PLATES = 'weight_plates', 'Weight Plates'
    CARDIO = 'cardio', 'Cardio Machines'
    STRENGTH = 'strength', 'Strength Machines'
    ACCESSORIES = 'accessories', 'Accessories'


class EquipmentStatus(models.TextChoices):
    GOOD = 'good', 'Good'
    MAINTENANCE = 'maintenance', 'Needs Maintenance'
    OUT_OF_SERVICE = 'out_of_service', 'Out of Service'


class InventoryItem(models.Model):
    """Unified inventory model for all gym equipment."""
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=EquipmentCategory.choices,
        default=EquipmentCategory.ACCESSORIES,
    )
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.GOOD,
    )
    # Optional spec fields
    weight_kg = models.FloatField(null=True, blank=True, help_text='Weight in kg (for dumbbells/plates/bars)')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'weight_kg', 'name']

    def __str__(self):
        return self.name

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def category_label(self):
        return self.get_category_display()
