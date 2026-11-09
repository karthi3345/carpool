import random
import string
from datetime import timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.rides.models import Ride
from apps.bookings.models import Booking, BookingSeatHold
from apps.messaging.models import RideMessage

SEAT_HOLD_DURATION_MINUTES = 15

def generate_booking_code():
    return 'CR-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_effective_available_seats(ride):
    """
    Calculates actual free seats = Total Seats - (Confirmed Seats + Active Unexpired Holds)
    """
    confirmed = Booking.objects.filter(
        ride=ride, status='confirmed'
    ).aggregate(s=Sum('seats_booked'))['s'] or 0

    now = timezone.now()
    active_holds = BookingSeatHold.objects.filter(
        ride=ride,
        is_active=True,
        expires_at__gt=now
    ).exclude(booking__status='confirmed').aggregate(s=Sum('seats_held'))['s'] or 0

    return max(0, ride.total_seats - (confirmed + active_holds))

def create_booking_request(ride, user, seats=1, passenger_name='', passenger_phone='', pickup='', dropoff=''):
    """
    Passenger requests booking -> Status becomes PENDING with a 15-minute SeatHold.
    Mandatory rule: All bookings require driver approval.
    """
    if not user or not user.is_authenticated:
        raise ValidationError("Authentication required to book seats.")

    if ride.status in ['cancelled', 'completed']:
        raise ValidationError(f"This ride is {ride.status} and cannot accept bookings.")

    if ride.available_seats < seats:
        raise ValidationError("Not enough seats available.")

    # Check effective seats considering unexpired holds
    available_now = get_effective_available_seats(ride)
    if available_now < seats:
        raise ValidationError("Seats are temporarily on hold for another pending request. Please check back shortly.")

    name = passenger_name or (user.get_full_name() or user.username)
    phone = passenger_phone or '+91 9876543210'

    code = generate_booking_code()
    expires_at = timezone.now() + timedelta(minutes=SEAT_HOLD_DURATION_MINUTES)

    with transaction.atomic():
        booking = Booking.objects.create(
            ride=ride,
            passenger=user,
            passenger_name=name,
            passenger_phone=phone,
            seats_booked=seats,
            original_price=ride.price_per_seat,
            agreed_price=ride.price_per_seat,
            pickup_point=pickup or ride.origin_point,
            dropoff_point=dropoff or ride.destination_point,
            status='pending',
            booking_code=code
        )

        BookingSeatHold.objects.create(
            booking=booking,
            ride=ride,
            seats_held=seats,
            expires_at=expires_at,
            is_active=True
        )

        # Create system notification messages
        RideMessage.objects.create(
            booking=booking,
            sender_type='system',
            sender_name='ChalRe System',
            text=f"Booking request submitted for {seats} seat(s). Awaiting driver approval. Hold expires in 15 minutes."
        )

        RideMessage.objects.create(
            booking=booking,
            sender_type='driver',
            sender_name=ride.driver_name,
            text=f"Vanakkam {name}! I received your request for {seats} seat(s) from {booking.pickup_point} to {booking.dropoff_point}. I will review and confirm shortly."
        )

    return booking

def driver_approve_booking(booking_id, driver_user=None):
    """
    Driver accepts request:
    1. select_for_update() row lock on Ride
    2. Recalculate confirmed seats
    3. Verify capacity
    4. Confirm booking & atomically update ride available_seats
    """
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(id=booking_id)
        if booking.status != 'pending':
            raise ValidationError(f"Booking is already {booking.status}.")

        ride = Ride.objects.select_for_update().get(id=booking.ride_id)
        if ride.status in ['cancelled', 'completed']:
            booking.status = 'rejected'
            booking.save()
            raise ValidationError(f"Cannot accept booking: Ride has been {ride.status}.")

        confirmed_count = Booking.objects.filter(
            ride=ride, status='confirmed'
        ).aggregate(s=Sum('seats_booked'))['s'] or 0

        remaining_capacity = ride.total_seats - confirmed_count
        if remaining_capacity < booking.seats_booked:
            booking.status = 'rejected'
            booking.save()
            if hasattr(booking, 'seat_hold'):
                booking.seat_hold.is_active = False
                booking.seat_hold.save()
            raise ValidationError("Insufficient seats available to confirm this request.")

        # Confirm booking
        booking.status = 'confirmed'
        booking.save()

        # Release temporary hold (it is now permanently confirmed)
        if hasattr(booking, 'seat_hold'):
            booking.seat_hold.is_active = False
            booking.seat_hold.save()

        # Update cached ride availability
        ride.available_seats = max(0, remaining_capacity - booking.seats_booked)
        if ride.available_seats == 0:
            ride.status = 'fully_booked'
        ride.save()

        RideMessage.objects.create(
            booking=booking,
            sender_type='system',
            sender_name='ChalRe System',
            text="✅ Booking CONFIRMED by driver! Have a pleasant and safe journey across Tamil Nadu."
        )

    return booking

def driver_reject_booking(booking_id, reason="Driver unable to accommodate route schedule"):
    """
    Driver rejects booking request
    """
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(id=booking_id)
        if booking.status != 'pending':
            raise ValidationError(f"Booking is already {booking.status}.")

        booking.status = 'rejected'
        booking.save()

        if hasattr(booking, 'seat_hold'):
            booking.seat_hold.is_active = False
            booking.seat_hold.save()

        RideMessage.objects.create(
            booking=booking,
            sender_type='driver',
            sender_name=booking.ride.driver_name,
            text=f"Request declined: {reason}. We encourage you to check alternative verified rides on this corridor."
        )

    return booking
