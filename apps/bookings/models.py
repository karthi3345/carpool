from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.rides.models import Ride

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Driver Approval'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected by Driver'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='passenger_bookings')
    passenger_name = models.CharField(max_length=120)
    passenger_phone = models.CharField(max_length=20)
    seats_booked = models.PositiveIntegerField(default=1)
    
    # Original fare and agreed negotiated fare
    original_price = models.DecimalField(max_digits=7, decimal_places=2)
    agreed_price = models.DecimalField(max_digits=7, decimal_places=2)
    
    pickup_point = models.CharField(max_length=200, blank=True)
    dropoff_point = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.booking_code} - {self.passenger_name} ({self.ride.origin.name} -> {self.ride.destination.name}) [{self.status}]"

    @property
    def total_cost(self):
        return self.agreed_price * self.seats_booked


class BookingSeatHold(models.Model):
    """
    Temporary seat hold (default 15 minutes) for pending requests
    to prevent phantom overbooking while drivers review requests.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='seat_hold')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='seat_holds')
    seats_held = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"SeatHold {self.seats_held} seats for Booking #{self.booking.booking_code} (Active: {self.is_active})"
