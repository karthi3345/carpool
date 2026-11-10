import json
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from datetime import date
from apps.locations.models import City
from apps.rides.models import Ride
from apps.reviews.models import PassengerReview
from django.db.models import Q
from apps.bookings.models import Booking

def home_preview(request):
    popular_cities = City.objects.filter(state='Tamil Nadu', is_popular=True)[:8]
    all_cities_qs = City.objects.filter(state='Tamil Nadu').order_by('name')
    
    cities_data = []
    for c in all_cities_qs:
        if c.latitude and c.longitude:
            cities_data.append({
                'name': c.name,
                'district': c.district,
                'lat': float(c.latitude),
                'lng': float(c.longitude),
                'is_popular': bool(c.is_popular)
            })

    today = date.today()
    active_rides = Ride.objects.filter(departure_date=today)
    if not active_rides.exists():
        active_rides = Ride.objects.all()[:35]

    corridors = []
    seen = set()
    for r in active_rides:
        key = (r.origin.name, r.destination.name)
        if key not in seen and r.origin and r.destination:
            seen.add(key)
            corridors.append({
                'ride_id': r.id,
                'from_name': r.origin.name,
                'from_lat': float(r.origin.latitude or 13.0827),
                'from_lng': float(r.origin.longitude or 80.2707),
                'to_name': r.destination.name,
                'to_landmark': r.destination_point or r.destination.name,
                'to_lat': float(r.destination.latitude or 13.0827),
                'to_lng': float(r.destination.longitude or 80.2707),
                'price': float(r.price_per_seat),
                'time': r.departure_time.strftime('%H:%M') if r.departure_time else '11:00',
                'driver': r.driver_name,
                'driver_rating': float(r.driver_rating or 4.8),
                'available_seats': r.available_seats
            })

    featured_reviews = PassengerReview.objects.filter(rating__gte=4).order_by('-created_at')[:6]
    total_reviews_count = PassengerReview.objects.count()

    return render(request, 'public/home.html', {
        'popular_cities': popular_cities,
        'all_cities': all_cities_qs,
        'cities_json': json.dumps(cities_data),
        'corridors': corridors,
        'corridors_json': json.dumps(corridors),
        'featured_reviews': featured_reviews,
        'total_reviews_count': total_reviews_count,
    })


def explore_map_view(request):
    return render(request, 'public/explore_map.html')

def my_rides_view(request):
    tab = request.GET.get('tab', 'upcoming')
    # Support 'past' as synonym for 'completed'
    if tab == 'past':
        tab = 'completed'
    
    # Exclude all dummy/seeded rides: Only show real rides published by users (which contain driver credentials and ride features)
    all_rides = Ride.objects.filter(notes__contains='Features:').order_by('-id')
    
    # If the user is logged in, optionally filter by user's name if matching rides exist
    if request.user.is_authenticated:
        user_name = (request.user.get_full_name() or request.user.username).strip().lower()
        user_rides = all_rides.filter(driver_name__icontains=user_name)
        if user_rides.exists():
            all_rides = user_rides
    
    if tab in ['completed', 'past']:
        rides = all_rides.filter(status='completed')
    elif tab == 'cancelled':
        rides = all_rides.filter(status='cancelled')
    else:
        # upcoming / active / published / pending
        tab = 'upcoming'
        rides = all_rides.filter(status__in=['published', 'pending', 'active', 'fully_booked'])
        
    cancelled_param = request.GET.get('cancelled') == '1'
    return render(request, 'rides/my_rides.html', {
        'rides': rides,
        'current_tab': tab,
        'cancelled_alert': cancelled_param
    })

def user_profile_view(request):
    return render(request, 'accounts/profile.html')

def inbox_messages_view(request):
    # Support both list view and active conversation view
    tab = request.GET.get('tab', 'all')
    active_code = request.GET.get('code')
    
    threads = []
    if request.user.is_authenticated:
        user_name = (request.user.get_full_name() or request.user.username).strip()
        user_threads_qs = Booking.objects.filter(
            Q(passenger=request.user) |
            Q(passenger_name__icontains=user_name) |
            Q(ride__driver_name__icontains=user_name)
        ).distinct().order_by('-updated_at')
    else:
        # For guest/demo view, show recent booking conversation threads
        user_threads_qs = Booking.objects.filter(messages__isnull=False).distinct().order_by('-updated_at')[:5]

    for b in user_threads_qs:
        last_msg = b.messages.order_by('-created_at').first()
        # Identify the other party
        is_user_driver = request.user.is_authenticated and (user_name.lower() in b.ride.driver_name.lower())
        other_party_name = b.passenger_name if is_user_driver else b.ride.driver_name
        other_party_role = "Passenger" if is_user_driver else "Driver"
        
        threads.append({
            'booking': b,
            'other_party_name': other_party_name,
            'other_party_role': other_party_role,
            'route': f"{b.ride.origin.name} → {b.ride.destination.name}",
            'last_message': last_msg.text if last_msg else "Conversation initiated",
            'last_time': last_msg.created_at if last_msg else b.created_at,
            'has_unread': b.status == 'pending',
            'chat_url': f"/bookings/{b.booking_code}/chat/",
        })

    active_thread = None
    if active_code:
        active_thread = next((t for t in threads if t['booking'].booking_code == active_code), None)
    if not active_thread and threads:
        active_thread = threads[0]

    return render(request, 'messages/inbox.html', {
        'threads': threads,
        'active_thread': active_thread,
        'threads_count': len(threads),
        'current_tab': tab
    })

def payment_history_view(request):
    return render(request, 'payments/history.html')

def reviews_list_view(request):
    return render(request, 'reviews/list.html')

def help_center_view(request):
    return render(request, 'support/help_center.html')

def admin_dashboard_view(request):
    return render(request, 'dashboard/admin_dashboard.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_preview, name='home'),
    path('explore/', explore_map_view, name='explore_map'),
    path('rides/my-rides/', my_rides_view, name='my-rides'),
    path('accounts/profile/', user_profile_view, name='user-profile'),
    path('messages/list/', inbox_messages_view, name='messages-list'),
    path('messages/', inbox_messages_view, name='messages-inbox'),
    path('payments/history/', payment_history_view, name='payment-history'),
    path('reviews/', reviews_list_view, name='reviews-list'),
    path('support/help/', help_center_view, name='help-center'),
    path('dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('api/v1/locations/', include('apps.locations.urls')),
    path('api/v1/rides/', include('apps.rides.urls')),
    path('rides/', include('apps.rides.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('support/', include('apps.support.urls')),
    path('community/', include('apps.community.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
