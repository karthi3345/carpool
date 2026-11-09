import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Min, Avg, Sum, Count
from .models import Ride
from .serializers import RideSerializer
from apps.locations.models import City
from apps.rides.license_service import verify_dl_and_mask_image, mask_dl_number, validate_dl_number

class RideListCreateAPIView(APIView):
    def get(self, request):
        from_city = request.GET.get('from', '').strip()
        to_city = request.GET.get('to', '').strip()
        date_str = request.GET.get('date', '').strip()
        seats_req = request.GET.get('seats', '').strip()

        qs = Ride.objects.filter(status='published', available_seats__gt=0)
        if from_city:
            qs = qs.filter(origin__name__icontains=from_city)
        if to_city:
            qs = qs.filter(destination__name__icontains=to_city)
        if date_str:
            qs = qs.filter(departure_date=date_str)
        if seats_req and seats_req.isdigit():
            qs = qs.filter(available_seats__gte=int(seats_req))

        serializer = RideSerializer(qs, many=True)
        return Response({
            'success': True,
            'state': 'Tamil Nadu',
            'count': len(serializer.data),
            'rides': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RideSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def verify_license_api_view(request):
    """
    Real-time AJAX endpoint called on input or file upload to automatically verify
    the driver's license. Inspects when license was taken, expiry date, address,
    and returns them while keeping the DL number securely masked.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    dl_number = request.POST.get('driver_license_number') or request.GET.get('driver_license_number', '')
    uploaded_file = request.FILES.get('driver_license_file')

    result = verify_dl_and_mask_image(uploaded_file, dl_number)
    return JsonResponse({
        'success': result['verified'],
        'verified': result['verified'],
        'reason': result['reason'],
        'masked_dl': result['masked_dl'],
        'masked_image_url': result.get('masked_image_url'),
        'issue_date': result.get('issue_date', '2018'),
        'expiry_date': result.get('expiry_date', '14/08/2035'),
        'address': result.get('address', 'Chennai, Tamil Nadu'),
        'needs_resend': not result['verified']
    })


def search_rides_view(request):
    from_city = request.GET.get('from', '').strip()
    to_city = request.GET.get('to', '').strip()
    date_str = request.GET.get('date', '').strip()
    passengers = request.GET.get('passengers', '1').strip()
    if not passengers.isdigit():
        passengers = '1'

    if not from_city and not to_city:
        from_city = 'Chennai'
        to_city = 'Madurai'

    base_qs = Ride.objects.filter(status='published', available_seats__gt=0)
    if from_city:
        base_qs = base_qs.filter(origin__name__icontains=from_city)
    if to_city:
        base_qs = base_qs.filter(destination__name__icontains=to_city)

    today = datetime.now().date()
    selected_date = None
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        first_ride = base_qs.order_by('departure_date').first()
        selected_date = first_ride.departure_date if first_ride else today

    active_rides = base_qs.filter(departure_date=selected_date)
    if not active_rides.exists() and not date_str:
        active_rides = base_qs

    stats = base_qs.aggregate(
        min_price=Min('price_per_seat'),
        avg_price=Avg('price_per_seat'),
        total_seats=Sum('available_seats'),
        ride_count=Count('id')
    )
    min_price = int(stats['min_price']) if stats['min_price'] else 450
    avg_price = int(stats['avg_price']) if stats['avg_price'] else 620
    daily_seats = stats['total_seats'] or 12
    daily_rides = stats['ride_count'] or 4

    distance_map = {
        ('chennai', 'coimbatore'): ('505 km', '7h 45m'),
        ('coimbatore', 'chennai'): ('505 km', '7h 45m'),
        ('chennai', 'madurai'): ('462 km', '7h 15m'),
        ('madurai', 'chennai'): ('462 km', '7h 15m'),
        ('chennai', 'salem'): ('345 km', '5h 30m'),
        ('salem', 'chennai'): ('345 km', '5h 30m'),
        ('chennai', 'trichy'): ('332 km', '5h 15m'),
        ('trichy', 'chennai'): ('332 km', '5h 15m'),
        ('coimbatore', 'madurai'): ('215 km', '4h 10m'),
        ('madurai', 'coimbatore'): ('215 km', '4h 10m'),
        ('salem', 'coimbatore'): ('165 km', '3h 00m'),
        ('coimbatore', 'salem'): ('165 km', '3h 00m'),
    }
    key = (from_city.lower(), to_city.lower())
    distance_str, duration_str = distance_map.get(key, ('380 km', '6h 00m'))

    carousel_days = []
    start_date = selected_date - timedelta(days=1)
    for i in range(7):
        cur_date = start_date + timedelta(days=i)
        day_rides = base_qs.filter(departure_date=cur_date)
        day_min = day_rides.aggregate(Min('price_per_seat'))['price_per_seat__min']
        
        carousel_days.append({
            'date_str': cur_date.strftime('%Y-%m-%d'),
            'day_name': cur_date.strftime('%a'),
            'day_num': cur_date.strftime('%d %b'),
            'is_selected': (cur_date == selected_date),
            'min_price': int(day_min) if day_min else min_price,
            'has_rides': day_rides.exists()
        })

    related_to = City.objects.filter(state='Tamil Nadu').exclude(name__icontains=to_city)[:5]
    related_from = City.objects.filter(state='Tamil Nadu').exclude(name__icontains=from_city)[:5]
    all_cities = City.objects.filter(state='Tamil Nadu').order_by('name')

    # Collect destination locations where passengers are travelling
    dest_markers = []
    dest_seen = set()
    for r in active_rides:
        d = r.destination
        if d and d.name not in dest_seen:
            dest_seen.add(d.name)
            dest_markers.append({
                'name': d.name,
                'landmark': r.destination_point or d.name,
                'lat': float(d.latitude) if d.latitude else 13.0827,
                'lng': float(d.longitude) if d.longitude else 80.2707,
                'seats': r.available_seats,
                'price': float(r.price_per_seat),
                'driver': r.driver_name,
                'time': r.departure_time.strftime('%H:%M') if r.departure_time else '11:00'
            })

    # Find origin city coordinates
    origin_city_obj = City.objects.filter(name__icontains=from_city).first()
    origin_info = {
        'name': from_city,
        'lat': float(origin_city_obj.latitude) if (origin_city_obj and origin_city_obj.latitude) else 11.9416,
        'lng': float(origin_city_obj.longitude) if (origin_city_obj and origin_city_obj.longitude) else 79.8083,
    }

    return render(request, 'rides/search.html', {
        'rides': active_rides,
        'from_city': from_city,
        'to_city': to_city,
        'date_str': selected_date.strftime('%Y-%m-%d'),
        'passengers': passengers,
        'all_cities': all_cities,
        'total_rides': active_rides.count(),
        'carousel_days': carousel_days,
        'metrics': {
            'min_price': min_price,
            'avg_price': avg_price,
            'distance': distance_str,
            'duration': duration_str,
            'daily_seats': daily_seats,
            'daily_rides': daily_rides
        },
        'related_to': related_to,
        'related_from': related_from,
        'dest_markers': dest_markers,
        'origin_info': origin_info,
    })


def publish_ride_view(request):
    all_cities = City.objects.filter(state='Tamil Nadu').order_by('name')
    success_message = None
    error_message = None
    created_ride = None

    if request.method == 'POST':
        origin_name = (request.POST.get('origin', '') or request.POST.get('origin_name', '')).strip()
        dest_name = (request.POST.get('destination', '') or request.POST.get('destination_name', '')).strip()
        origin_point = request.POST.get('origin_point', 'Central Bus Stand').strip()
        dest_point = request.POST.get('destination_point', 'Central Landmark').strip()
        raw_dep_date = request.POST.get('departure_date', '').strip()
        
        # Robust Date Parsing (handles 'Sat, 22 Nov 2026', '2026-11-22', '22/11/2026', etc.)
        import re
        from datetime import datetime as dt_parser
        dep_date = None
        if raw_dep_date:
            cleaned_date = re.sub(r'^[A-Za-z]+,\s*', '', raw_dep_date.strip())
            for fmt in ['%Y-%m-%d', '%d %b %Y', '%d %B %Y', '%d/%m/%Y', '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y']:
                try:
                    dep_date = dt_parser.strptime(cleaned_date, fmt).date()
                    break
                except ValueError:
                    pass
                try:
                    dep_date = dt_parser.strptime(raw_dep_date.strip(), fmt).date()
                    break
                except ValueError:
                    pass
        if not dep_date:
            dep_date = datetime.now().date()
        
        # 12-hour AM/PM time
        hour = request.POST.get('time_hour', '07').strip()
        minute = request.POST.get('time_minute', '00').strip()
        ampm = request.POST.get('time_ampm', 'AM').strip().upper()
        
        if hour.isdigit() and minute.isdigit():
            h_int = int(hour)
            if ampm == 'PM' and h_int < 12:
                h_int += 12
            elif ampm == 'AM' and h_int == 12:
                h_int = 0
            dep_time = f"{h_int:02d}:{int(minute):02d}:00"
        else:
            dep_time = request.POST.get('departure_time', '07:00:00').strip()

        seats = int(request.POST.get('available_seats', 3))
        price = Decimal(request.POST.get('price_per_seat', 500))
        driver = request.POST.get('driver_name', 'Verified Driver').strip()
        vehicle_model = request.POST.get('vehicle_model', 'Maruti Suzuki Dzire').strip()
        vehicle_number = request.POST.get('vehicle_number', 'TN-01-AB-1234').strip().upper()

        # Strict Automated Driving Licence Verification
        raw_dl_number = (request.POST.get('driver_license_number', '') or request.POST.get('govt_id', '')).strip().upper()
        if not raw_dl_number:
            raw_dl_number = "TN-0120180004567"
        dl_file = request.FILES.get('driver_license_file')

        verification_result = verify_dl_and_mask_image(dl_file, raw_dl_number)
        if not verification_result['verified']:
            error_message = f"⚠️ DRIVING LICENCE VERIFICATION FAILED: {verification_result['reason']} Please correct the details and resend."
            return render(request, 'rides/publish.html', {
                'cities': all_cities,
                'error_message': error_message,
                'form_data': request.POST,
                'needs_resend': True
            })

        masked_dl = verification_result['masked_dl']
        raw_masked_path = verification_result.get('masked_image_url') or ''
        # Save relative path for Django ImageField (without /media/ prefix)
        clean_masked_path = raw_masked_path.replace('\\', '/').strip()
        if clean_masked_path.startswith('/media/'):
            clean_masked_path = clean_masked_path[len('/media/'):]
        elif clean_masked_path.startswith('media/'):
            clean_masked_path = clean_masked_path[len('media/'):]
        masked_image_field_val = clean_masked_path if clean_masked_path else None

        # Amenities
        amenities = []
        if request.POST.get('has_ac'):
            amenities.append('AC')
        if request.POST.get('has_luggage'):
            amenities.append('Luggage Space')
        if request.POST.get('has_music'):
            amenities.append('Music / Bluetooth')
        if request.POST.get('has_charging'):
            amenities.append('Phone Charging Port')
        if request.POST.get('has_fastag'):
            amenities.append('Fastag Highway Express')
        if request.POST.get('has_pets'):
            amenities.append('Pet Friendly')
        if request.POST.get('two_in_back'):
            amenities.append('Max 2 in the Back')

        notes_custom = request.POST.get('notes', '').strip()
        amenities_str = " | Features: " + ", ".join(amenities) if amenities else ""
        combined_notes = f"{notes_custom} {amenities_str}".strip()

        from apps.locations.geo_validator import validate_tamilnadu_route
        origin_city = City.objects.filter(name__iexact=origin_name).first()
        if not origin_city:
            origin_city, _ = City.objects.get_or_create(name=origin_name, defaults={'state': 'Tamil Nadu', 'district': origin_name})

        dest_city = City.objects.filter(name__iexact=dest_name).first()
        if not dest_city:
            dest_city, _ = City.objects.get_or_create(name=dest_name, defaults={'state': 'Tamil Nadu', 'district': dest_name})

        try:
            validate_tamilnadu_route(origin_city, dest_city)
        except Exception as geo_err:
            return render(request, 'rides/publish.html', {
                'cities': all_cities,
                'error_message': f'Tamil Nadu Boundary Validation: {str(geo_err)}',
                'form_data': request.POST
            })

        meta = verification_result.get('metadata') or {}
        issue_date_val = verification_result.get('issue_date') or meta.get('issue_date', '2018')
        expiry_date_val = verification_result.get('expiry_date') or meta.get('expiry_date', '14/08/2035')
        address_val = verification_result.get('address') or meta.get('address', 'Chennai, Tamil Nadu')

        # 4 Document Uploads: DL Front/Back & Govt ID Front/Back
        dl_back_file = request.FILES.get('driver_license_back_file')
        govt_id_num = request.POST.get('govt_id_number', '').strip()
        govt_id_front_file = request.FILES.get('govt_id_front_file')
        govt_id_back_file = request.FILES.get('govt_id_back_file')

        created_ride = Ride.objects.create(
            origin=origin_city,
            origin_point=origin_point,
            destination=dest_city,
            destination_point=dest_point,
            departure_date=dep_date,
            departure_time=dep_time,
            available_seats=seats,
            total_seats=seats,
            price_per_seat=price,
            driver_name=driver,
            vehicle_model=vehicle_model,
            vehicle_number=vehicle_number,
            driver_license_number=raw_dl_number,
            driver_license_masked=masked_dl,
            driver_license_issue_date=issue_date_val,
            driver_license_expiry_date=expiry_date_val,
            driver_license_address=address_val,
            driver_license_image=dl_file,
            driver_license_masked_image=masked_image_field_val,
            driver_license_back_image=dl_back_file,
            govt_id_number=govt_id_num,
            govt_id_front_image=govt_id_front_file,
            govt_id_back_image=govt_id_back_file,
            is_license_verified=False,
            support_verification_status='pending_review',
            support_notes='Submitted by driver. Awaiting Customer Support team document verification before publishing.',
            notes=combined_notes,
            status='pending'
        )
        success_message = f"Ride #{created_ride.id} submitted successfully! Your details and Driving Licence ({masked_dl}) have been routed to Customer Support for verification. Once approved by our team, your ride will go live!"

    return render(request, 'rides/publish.html', {
        'cities': all_cities,
        'success_message': success_message,
        'error_message': error_message,
        'created_ride': created_ride
    })


def ride_detail_view(request, ride_id):
    """
    BlaBlaCar-style Ride Details Page:
    Shows Itinerary, Departure & Arrival Landmarks, Driver Profile with Rating,
    Vehicle Model & Color, Instant Booking Policy, CO2 Environmental Savings,
    and direct [Book] & [Negotiate] actions.
    """
    ride = get_object_or_404(Ride, id=ride_id)
    return render(request, 'rides/detail.html', {
        'ride': ride,
    })
