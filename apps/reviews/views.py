from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from apps.rides.models import Ride
from apps.bookings.models import Booking
from apps.reviews.models import PassengerReview

def submit_passenger_review(request, ride_id):
    """
    POST: Passenger submits rating (1-5), review text, and highlight tags.
    """
    ride = get_object_or_404(Ride, id=ride_id)

    if request.method == 'POST':
        passenger_name = request.POST.get('passenger_name', 'Verified Passenger').strip()
        passenger_city = request.POST.get('passenger_city', 'Tamil Nadu').strip()
        rating = int(request.POST.get('rating', 5))
        review_text = request.POST.get('review_text', '').strip()
        booking_code = request.POST.get('booking_code', '').strip()

        booking = None
        if booking_code:
            booking = Booking.objects.filter(booking_code=booking_code).first()

        punctual = bool(request.POST.get('punctual'))
        clean_car = bool(request.POST.get('clean_car'))
        safe_driving = bool(request.POST.get('safe_driving'))
        friendly = bool(request.POST.get('friendly'))

        # Create passenger review
        review = PassengerReview.objects.create(
            ride=ride,
            booking=booking,
            passenger_name=passenger_name if passenger_name else 'Verified Passenger',
            passenger_city=passenger_city if passenger_city else 'Tamil Nadu',
            rating=rating,
            review_text=review_text,
            punctual=punctual,
            clean_car=clean_car,
            safe_driving=safe_driving,
            friendly=friendly
        )

        # Recalculate average driver rating
        all_reviews = PassengerReview.objects.filter(ride__driver_name=ride.driver_name)
        if all_reviews.exists():
            total = sum([r.rating for r in all_reviews])
            new_avg = round(total / all_reviews.count(), 1)
            Ride.objects.filter(driver_name=ride.driver_name).update(driver_rating=new_avg)

        messages.success(request, f"Thank you {passenger_name}! Your {rating}★ review for driver {ride.driver_name} has been published.")

        if booking_code:
            return redirect('booking-chat', booking_code=booking_code)
        return redirect(request.META.get('HTTP_REFERER', '/rides/search/'))

    return redirect('/rides/search/')


def get_ride_reviews_api(request, ride_id):
    """
    JSON API to fetch passenger reviews for a ride / driver
    """
    ride = get_object_or_404(Ride, id=ride_id)
    reviews = ride.passenger_reviews.all()

    reviews_data = []
    for r in reviews:
        reviews_data.append({
            'id': r.id,
            'passenger_name': r.passenger_name,
            'passenger_city': r.passenger_city,
            'rating': r.rating,
            'review_text': r.review_text,
            'punctual': r.punctual,
            'clean_car': r.clean_car,
            'safe_driving': r.safe_driving,
            'friendly': r.friendly,
            'driver_reply': r.driver_reply,
            'created_at': r.created_at.strftime('%d %b %Y')
        })

    return JsonResponse({
        'success': True,
        'driver_name': ride.driver_name,
        'driver_rating': float(ride.driver_rating),
        'total_reviews': len(reviews_data),
        'reviews': reviews_data
    })
