from django.db import models
from apps.locations.models import City

class Ride(models.Model):
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('fully_booked', 'Fully Booked'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    origin = models.ForeignKey(City, on_delete=models.CASCADE, related_name='departing_rides')
    origin_point = models.CharField(max_length=150, default='Central Bus Stand / CMBT')
    destination = models.ForeignKey(City, on_delete=models.CASCADE, related_name='arriving_rides')
    destination_point = models.CharField(max_length=150, default='Central Bus Stand')

    departure_date = models.DateField(db_index=True)
    departure_time = models.TimeField()
    estimated_arrival = models.TimeField(null=True, blank=True)
    duration_text = models.CharField(max_length=50, default='4h 30m')

    driver_name = models.CharField(max_length=100, default='Suresh Kumar')
    driver_rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.9)
    vehicle_model = models.CharField(max_length=100, default='Maruti Swift Dzire')
    vehicle_number = models.CharField(max_length=30, default='TN-01-BK-4567')

    driver_license_number = models.CharField(max_length=50, blank=True, default='')
    driver_license_masked = models.CharField(max_length=50, blank=True, default='')
    driver_license_issue_date = models.CharField(max_length=50, blank=True, default='')
    driver_license_expiry_date = models.CharField(max_length=50, blank=True, default='')
    driver_license_address = models.CharField(max_length=255, blank=True, default='')
    driver_license_image = models.ImageField(upload_to='licenses/', null=True, blank=True)
    driver_license_masked_image = models.ImageField(upload_to='licenses/masked/', null=True, blank=True)
    driver_license_back_image = models.ImageField(upload_to='licenses/back/', null=True, blank=True)
    govt_id_number = models.CharField(max_length=50, blank=True, default='')
    govt_id_front_image = models.ImageField(upload_to='govt_ids/front/', null=True, blank=True)
    govt_id_back_image = models.ImageField(upload_to='govt_ids/back/', null=True, blank=True)
    is_license_verified = models.BooleanField(default=True)
    SUPPORT_STATUS_CHOICES = (
        ('pending_review', 'Pending Customer Support Review'),
        ('approved', 'Verified & Approved by Support'),
        ('rejected', 'Rejected by Support'),
    )
    support_verification_status = models.CharField(max_length=30, choices=SUPPORT_STATUS_CHOICES, default='pending_review')
    support_reviewed_by = models.CharField(max_length=100, blank=True, default='')
    support_reviewed_at = models.DateTimeField(null=True, blank=True)
    support_notes = models.TextField(blank=True, default='Awaiting customer support document manual verification.')
    available_seats = models.PositiveIntegerField(default=3)
    total_seats = models.PositiveIntegerField(default=3)
    FUEL_TYPE_CHOICES = (
        ('Petrol', 'Petrol ⛽'),
        ('Diesel', 'Diesel ⛽'),
        ('EV', 'Electric (EV) ⚡'),
        ('CNG', 'CNG 🌿'),
    )
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, default='Petrol', blank=True)
    price_per_seat = models.DecimalField(max_digits=7, decimal_places=2, default=450.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    notes = models.TextField(blank=True, default='Comfortable AC ride. Clean car, strictly no smoking.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['departure_date', 'departure_time']

    def __str__(self):
        return f"{self.origin.name} -> {self.destination.name} on {self.departure_date} (Rs.{self.price_per_seat})"
