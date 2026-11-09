from django.db import models

class City(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=50, default='Tamil Nadu')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.district}"

class PopularPoint(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='points')
    name = models.CharField(max_length=150)
    point_type = models.CharField(max_length=50, default='Bus Stand') # Bus Stand, Railway Station, Metro, Toll Plaza

    def __str__(self):
        return f"{self.name} ({self.city.name})"
