from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from apps.rides.models import Ride
from apps.bookings.models import Booking
from apps.messaging.models import RideMessage
from .services import (
    create_booking_request,
    driver_approve_booking,
    driver_reject_booking,
    get_effective_available_seats
)

@csrf_exempt
def create_booking_view(request):
    """
    POST: Submit booking request for driver approval.
    Enforces authentication and Tamil Nadu boundary validation.
    """
    if request.method == 'POST':
        ride_id = request.POST.get('ride_id')
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('accept', '') or
            request.POST.get('is_ajax') == '1'
        )

        # Enforce authentication: without login, booking is disallowed
        if not request.user.is_authenticated:
            target_next = f"/rides/{ride_id}/" if ride_id else (request.META.get('HTTP_REFERER') or '/')
            login_url = f"/accounts/login/?next={target_next}"
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'login_required': True,
                    'login_url': login_url,
                    'error': 'Please sign in to book your ride.'
                }, status=401)
            return redirect(login_url)

        ride = get_object_or_404(Ride, id=ride_id)
        seats = int(request.POST.get('seats', 1))
        name = request.POST.get('passenger_name', '').strip()
        phone = request.POST.get('passenger_phone') or request.POST.get('phone', '').strip()
        pickup = request.POST.get('pickup_point', '').strip()
        dropoff = request.POST.get('dropoff_point', '').strip()

        try:
            booking = create_booking_request(
                ride=ride,
                user=request.user,
                seats=seats,
                passenger_name=name,
                passenger_phone=phone,
                pickup=pickup,
                dropoff=dropoff
            )
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e)
            if is_ajax:
                return JsonResponse({'success': False, 'error': msg}, status=400)
            return redirect(f"/rides/{ride_id}/?error={msg}")

        chat_url = f'/bookings/{booking.booking_code}/chat/'
        if is_ajax:
            return JsonResponse({
                'success': True,
                'booking_code': booking.booking_code,
                'status': booking.status,
                'chat_url': chat_url
            })
        return redirect(chat_url)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


def booking_chat_view(request, booking_code):
    """
    Interactive chat room & Driver Approval Actions console
    """
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/bookings/{booking_code}/chat/")

    booking = get_object_or_404(Booking, booking_code=booking_code)
    messages = booking.messages.all()

    return render(request, 'bookings/chat.html', {
        'booking': booking,
        'ride': booking.ride,
        'messages': messages,
    })


@csrf_exempt
def driver_approve_booking_view(request, booking_code):
    """
    POST: Driver approves passenger booking request (atomic lock & seat allocation)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    booking = get_object_or_404(Booking, booking_code=booking_code)
    try:
        driver_approve_booking(booking.id, request.user)
        return JsonResponse({'success': True, 'status': 'confirmed'})
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
def driver_reject_booking_view(request, booking_code):
    """
    POST: Driver declines passenger booking request
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    booking = get_object_or_404(Booking, booking_code=booking_code)
    reason = request.POST.get('reason', 'Schedule full')
    try:
        driver_reject_booking(booking.id, reason)
        return JsonResponse({'success': True, 'status': 'rejected'})
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
def send_message_view(request, booking_code):
    """
    POST: Send message or counter-offer fare in live negotiation room
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'login_required': True, 'error': 'Login required'}, status=401)

    if request.method == 'POST':
        booking = get_object_or_404(Booking, booking_code=booking_code)
        sender_type = request.POST.get('sender_type', 'passenger')
        sender_name = request.POST.get('sender_name', booking.passenger_name)
        text = request.POST.get('text', '').strip()
        is_offer = request.POST.get('is_offer', 'false') == 'true'
        offer_price_val = request.POST.get('offer_price', None)

        offer_price = None
        offer_status = 'none'

        if is_offer and offer_price_val:
            try:
                offer_price = Decimal(offer_price_val)
                offer_status = 'pending'
                text = f"Proposed new fare: ₹{offer_price}/seat. {text}"
            except Exception:
                is_offer = False

        msg = RideMessage.objects.create(
            booking=booking,
            sender_type=sender_type,
            sender_name=sender_name,
            text=text,
            is_price_offer=is_offer,
            proposed_price=offer_price,
            offer_status=offer_status
        )

        # Natural simulated response for demo
        if sender_type == 'passenger' and is_offer and offer_price:
            if offer_price >= booking.original_price * Decimal('0.8'):
                booking.agreed_price = offer_price
                booking.save()
                msg.offer_status = 'accepted'
                msg.save()

                RideMessage.objects.create(
                    booking=booking,
                    sender_type='driver',
                    sender_name=booking.ride.driver_name,
                    text=f"Agreed! I accept your offered price of ₹{offer_price} per seat. Looking forward to travelling together!"
                )
            else:
                counter = int(booking.original_price * Decimal('0.9'))
                RideMessage.objects.create(
                    booking=booking,
                    sender_type='driver',
                    sender_name=booking.ride.driver_name,
                    text=f"₹{offer_price} is a bit low considering highway tolls. How about ₹{counter} per seat?"
                )

        return JsonResponse({
            'success': True,
            'agreed_price': str(booking.agreed_price),
            'total_cost': str(booking.total_cost)
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
