from django.db import models

# Create your models here.
class Dumbells(models.Model):
    name = models.CharField(max_length=100)
    weight = models.FloatField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.name
    
class Treadmills(models.Model):
    name = models.CharField(max_length=100)
    speed = models.FloatField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.name    
    
class ExerciseBikes(models.Model):
    name = models.CharField(max_length=100)
    resistance_levels = models.IntegerField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.name
    
class Barbells(models.Model):
    name = models.CharField(max_length=100)
    weight = models.FloatField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.name