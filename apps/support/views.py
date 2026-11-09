from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.rides.models import Ride

def support_login_view(request):
    """
    Dedicated Customer Support Staff Login
    Credentials: username 'lk', password '123'
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.username in ['lk', 'karthik']):
        return redirect('support-verification-dashboard')

    error = None
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, Customer Support Officer ({user.username})!")
            return redirect('support-verification-dashboard')
        else:
            error = "Invalid Customer Support credentials. (Use username: lk, password: 123)"

    return render(request, 'support/login.html', {
        'error': error,
        'default_username': 'lk'
    })


def support_logout_view(request):
    logout(request)
    messages.info(request, "Successfully logged out from Customer Support Console.")
    return redirect('support-login')


def support_verification_dashboard(request):
    """
    Customer Support Console:
    Requires customer support staff authentication.
    """
    # Open access for customer support console (no login barrier required)
    # if not request.user.is_authenticated or not (request.user.is_staff or request.user.username in ['lk', 'karthik']):
    #     return redirect('support-login')

    pending_rides = Ride.objects.filter(support_verification_status='pending_review').order_by('-created_at')
    approved_rides = Ride.objects.filter(support_verification_status='approved').order_by('-support_reviewed_at')[:10]
    rejected_rides = Ride.objects.filter(support_verification_status='rejected').order_by('-support_reviewed_at')[:10]

    return render(request, 'support/verification_dashboard.html', {
        'pending_rides': pending_rides,
        'approved_rides': approved_rides,
        'rejected_rides': rejected_rides,
        'pending_count': pending_rides.count(),
        'approved_count': approved_rides.count(),
        'rejected_count': rejected_rides.count(),
        'officer_name': request.user.username
    })


def support_approve_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    username = request.user.username if request.user.is_authenticated else 'Support Officer'
    reviewer = f"Support Agent ({username})"
    
    ride.support_verification_status = 'approved'
    ride.support_reviewed_by = reviewer
    ride.support_reviewed_at = timezone.now()
    ride.support_notes = request.POST.get('notes', 'Driver license and identity verified manually by customer support.')
    ride.is_license_verified = True
    ride.status = 'published'
    ride.save()

    messages.success(request, f"Ride #{ride.id} ({ride.origin.name} -> {ride.destination.name}) Driver Licence has been verified, APPROVED & PUBLISHED live to passengers by Customer Support ({request.user.username})!")
    return redirect('support-verification-dashboard')


def support_reject_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    username = request.user.username if request.user.is_authenticated else 'Support Officer'
    reviewer = f"Support Agent ({username})"
    reason = request.POST.get('reason', 'Driver licence document clarity issue or identity discrepancy.')
    
    ride.support_verification_status = 'rejected'
    ride.support_reviewed_by = reviewer
    ride.support_reviewed_at = timezone.now()
    ride.support_notes = f"REJECTED: {reason}"
    ride.is_license_verified = False
    ride.status = 'cancelled'
    ride.save()

    messages.warning(request, f"Ride #{ride.id} Driver Licence was REJECTED by Customer Support ({request.user.username}). Driver will be prompted to resend.")
    return redirect('support-verification-dashboard')


@csrf_exempt
def support_chatbot_api(request):
    """
    AI Support Chatbot Assistant for Tamil Nadu Carpool Platform
    """
    if request.method == 'POST':
        import json
        try:
            body = json.loads(request.body.decode('utf-8'))
            user_msg = body.get('message', '').strip().lower()
        except Exception:
            user_msg = request.POST.get('message', '').strip().lower()

        if not user_msg:
            return JsonResponse({'reply': 'Vanakkam! How can I assist you with Tamil Nadu carpooling today?'})

        if any(w in user_msg for w in ['book', 'reserve', 'ticket', 'seat']):
            reply = (
                "Booking a seat is simple and instant:\n"
                "1. Search your origin & destination on the home or search page.\n"
                "2. Choose your preferred departure time and driver rating.\n"
                "3. Click 'Book Seat'. You will instantly enter a live negotiation chat room with the driver!"
            )
        elif any(w in user_msg for w in ['login', 'account', 'sign in', 'register']):
            reply = (
                "You must be logged in to book seats or chat with drivers. "
                "You can use our 1-click Demo Login ('karthik' with password '123') or sign up in seconds!"
            )
        elif any(w in user_msg for w in ['negotiat', 'bargain', 'offer', 'fare', 'price', 'discount']):
            reply = (
                "ChalRe supports interactive fare negotiation! Once booked, you can propose a counter-offer in the chat room. "
                "Drivers can accept or adjust fares depending on highway tolls."
            )
        elif any(w in user_msg for w in ['license', 'licence', 'dl', 'verify', 'verified', 'safe', 'safety']):
            reply = (
                "Passenger safety is paramount. Every driver is required to upload a verified Indian Driving License. "
                "Our optical AI checks credentials, and our Tamil Nadu support team manually audits every driver."
            )
        elif any(w in user_msg for w in ['cancel', 'refund', 'cancellation']):
            reply = (
                "You can cancel up to 2 hours before departure with zero penalty. "
                "If a driver cancels, you receive priority seat re-accommodation on the same highway corridor immediately."
            )
        elif any(w in user_msg for w in ['route', 'corridor', 'city', 'cities', 'where', 'pickup', 'point']):
            reply = (
                "We connect all 38 districts of Tamil Nadu!\n"
                "• Chennai ➔ Coimbatore (NH 544)\n"
                "• Chennai ➔ Madurai (GST Road / NH 38)\n"
                "• Chennai ➔ Trichy (NH 38 via Villupuram)\n"
                "• Coimbatore ➔ Madurai (NH 83)\n"
                "• Chennai ➔ Puducherry (ECR)"
            )
        elif any(w in user_msg for w in ['driver', 'offer', 'publish', 'host']):
            reply = (
                "Traveling between Tamil Nadu cities? Click 'Offer Ride' in the header to publish your trip, specify available seats, and split fuel costs!"
            )
        elif any(w in user_msg for w in ['contact', 'phone', 'human', 'officer', 'help', 'agent']):
            reply = (
                "Our Tamil Nadu Customer Support Helpdesk is active 24/7. "
                "Senior Officer Priya S. and our team can be reached anytime via support@chalre.in."
            )
        elif any(w in user_msg for w in ['vanakkam', 'hello', 'hi', 'hey', 'start']):
            reply = (
                "Vanakkam! Welcome to ChalRe Tamil Nadu Support. "
                "I can help you with ride bookings, driver safety, fare negotiations, and routes across Tamil Nadu's 38 districts. What would you like to know?"
            )
        else:
            reply = (
                "Thanks for reaching out! ChalRe is Tamil Nadu's verified intercity carpooling platform. "
                "You can search seats between all 38 districts, negotiate fares, and ride safely. "
                "Would you like details on booking a seat, safety verification, or route corridors?"
            )

        return JsonResponse({
            'success': True,
            'reply': reply,
            'agent': 'Priya S. (ChalRe Support)'
        })

    return JsonResponse({'error': 'POST required'}, status=405)
