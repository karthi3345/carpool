from django.db import models
from apps.bookings.models import Booking

class RideMessage(models.Model):
    SENDER_TYPES = (
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
        ('system', 'System Notification'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=15, choices=SENDER_TYPES)
    sender_name = models.CharField(max_length=100)
    text = models.TextField()
    
    # Negotiation offer if this message contains a price counter-offer
    proposed_price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_price_offer = models.BooleanField(default=False)
    offer_status = models.CharField(max_length=20, default='none') # none, pending, accepted, rejected

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender_type}] {self.sender_name}: {self.text[:30]}"
