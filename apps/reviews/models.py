from django.db import models
from apps.rides.models import Ride
from apps.bookings.models import Booking

class PassengerReview(models.Model):
    RATING_CHOICES = (
        (5, '5 Stars - Outstanding Experience'),
        (4, '4 Stars - Very Good & Comfortable'),
        (3, '3 Stars - Average / Decent'),
        (2, '2 Stars - Poor Experience'),
        (1, '1 Star - Terrible / Not Recommended'),
    )

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='passenger_reviews')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    passenger_name = models.CharField(max_length=100, default='Verified Passenger')
    passenger_city = models.CharField(max_length=100, default='Chennai')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    
    # Review tags / highlights
    punctual = models.BooleanField(default=True, verbose_name="On-time Departure & Driving")
    clean_car = models.BooleanField(default=True, verbose_name="Clean & AC Comfortable Car")
    safe_driving = models.BooleanField(default=True, verbose_name="Safe & Calm Highway Driving")
    friendly = models.BooleanField(default=True, verbose_name="Polite & Friendly Co-traveller")

    review_text = models.TextField(blank=True, default='')
    driver_reply = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.passenger_name} ({self.rating}★) for {self.ride.driver_name}"
