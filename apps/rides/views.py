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


def check_driver_verified_api_view(request):
    """
    Check if a driver is already verified by Customer Support based on DL number,
    Govt ID, vehicle plate, or driver name. Once verified, no re-verification needed!
    """
    dl = request.GET.get('dl', '').strip().upper()
    govt_id = request.GET.get('govt_id', '').strip()
    plate = request.GET.get('plate', '').strip().upper()
    driver_name = request.GET.get('driver_name', '').strip()

    clean_dl = dl.replace('-', '').replace(' ', '')
    clean_plate = plate.replace('-', '').replace(' ', '')

    from django.db.models import Q
    query = Q(support_verification_status='approved')

    matches = []
    if len(clean_dl) >= 5:
        matches.append(Q(driver_license_number__icontains=clean_dl) | Q(driver_license_number__icontains=dl))
    if len(govt_id) >= 4:
        matches.append(Q(govt_id_number__iexact=govt_id))
    if len(clean_plate) >= 4:
        matches.append(Q(vehicle_number__icontains=clean_plate) | Q(vehicle_number__icontains=plate))
    if driver_name and len(driver_name) >= 3:
        matches.append(Q(driver_name__iexact=driver_name))

    if matches:
        combined_q = matches[0]
        for m in matches[1:]:
            combined_q = combined_q | m
        approved_ride = Ride.objects.filter(query & combined_q).order_by('-id').first()
        if approved_ride:
            return JsonResponse({
                'is_verified': True,
                'driver_name': approved_ride.driver_name,
                'masked_dl': approved_ride.driver_license_masked or approved_ride.driver_license_number,
                'vehicle_model': approved_ride.vehicle_model,
                'vehicle_number': approved_ride.vehicle_number,
                'govt_id_number': approved_ride.govt_id_number,
                'verified_by': approved_ride.support_reviewed_by or 'Customer Support Officer',
                'message': f"Driver verified previously! No need to re-upload documents or wait for support review."
            })

    return JsonResponse({'is_verified': False})


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

    # If user searched same origin and destination, fallback to Madurai destination to prevent identical route
    if from_city and to_city and from_city.strip().lower() == to_city.strip().lower():
        to_city = 'Madurai' if from_city.strip().lower() != 'madurai' else 'Coimbatore'

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

        # Strict validation: Departure and Destination cannot be the same!
        if origin_name and dest_name and origin_name.strip().lower() == dest_name.strip().lower():
            error_message = f"Departure and Destination cannot be the same city ({origin_name.title()}). Please select different cities for pickup and drop."
            return render(request, 'rides/publish.html', {
                'cities': all_cities,
                'error_message': error_message,
                'form_data': request.POST
            })
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

        raw_dl_number = (request.POST.get('driver_license_number', '') or request.POST.get('govt_id', '')).strip().upper()
        if not raw_dl_number:
            raw_dl_number = "TN-0120180004567"
        dl_file = request.FILES.get('driver_license_file')
        dl_back_file = request.FILES.get('driver_license_back_file')
        govt_id_num = request.POST.get('govt_id_number', '').strip()
        govt_id_front_file = request.FILES.get('govt_id_front_file')
        govt_id_back_file = request.FILES.get('govt_id_back_file')

        # CHECK UPFRONT IF DRIVER WAS ALREADY VERIFIED FOR A PREVIOUS RIDE
        # If verified before, skip all OCR checks and skip support review!
        from django.db.models import Q
        clean_dl_check = raw_dl_number.replace('-', '').replace(' ', '')
        clean_plate_check = vehicle_number.replace('-', '').replace(' ', '')

        existing_verified_ride = Ride.objects.filter(
            support_verification_status='approved'
        ).filter(
            Q(driver_license_number__iexact=raw_dl_number) |
            Q(driver_license_number__icontains=clean_dl_check) |
            (Q(driver_name__iexact=driver) & Q(vehicle_number__icontains=clean_plate_check)) |
            (Q(govt_id_number__iexact=govt_id_num) if govt_id_num else Q(pk__isnull=True))
        ).order_by('-id').first()

        if existing_verified_ride:
            # ALREADY VERIFIED DRIVER: Skip OCR verification completely!
            masked_dl = existing_verified_ride.driver_license_masked or mask_dl_number(raw_dl_number)
            masked_image_field_val = existing_verified_ride.driver_license_masked_image
            issue_date_val = existing_verified_ride.driver_license_issue_date or '2018'
            expiry_date_val = existing_verified_ride.driver_license_expiry_date or '14/08/2035'
            address_val = existing_verified_ride.driver_license_address or 'Tamil Nadu, India'
        else:
            # First-time unverified driver: perform strict automated verification
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
            clean_masked_path = raw_masked_path.replace('\\', '/').strip()
            if clean_masked_path.startswith('/media/'):
                clean_masked_path = clean_masked_path[len('/media/'):]
            elif clean_masked_path.startswith('media/'):
                clean_masked_path = clean_masked_path[len('media/'):]
            masked_image_field_val = clean_masked_path if clean_masked_path else None
            meta = verification_result.get('metadata') or {}
            issue_date_val = verification_result.get('issue_date') or meta.get('issue_date', '2018')
            expiry_date_val = verification_result.get('expiry_date') or meta.get('expiry_date', '14/08/2035')
            address_val = verification_result.get('address') or meta.get('address', 'Chennai, Tamil Nadu')

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

        # Driver check already performed upfront (existing_verified_ride)

        if existing_verified_ride:
            # Driver is already verified! Publish ride immediately without support delay
            support_status = 'approved'
            ride_status = 'published'
            is_verified = True
            reviewer = existing_verified_ride.support_reviewed_by or 'System Auto-Approval (Previously Verified Driver)'
            support_notes = f"Auto-approved: Driver ({driver}) Driving Licence & Identity previously audited and verified in Ride #{existing_verified_ride.id}."
            
            # Inherit previous verified docs if user omitted uploading them again
            final_dl_front = dl_file or existing_verified_ride.driver_license_image
            final_dl_masked = masked_image_field_val or existing_verified_ride.driver_license_masked_image
            final_dl_back = dl_back_file or existing_verified_ride.driver_license_back_image
            final_govt_num = govt_id_num or existing_verified_ride.govt_id_number
            final_govt_front = govt_id_front_file or existing_verified_ride.govt_id_front_image
            final_govt_back = govt_id_back_file or existing_verified_ride.govt_id_back_image

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
                driver_license_image=final_dl_front,
                driver_license_masked_image=final_dl_masked,
                driver_license_back_image=final_dl_back,
                govt_id_number=final_govt_num,
                govt_id_front_image=final_govt_front,
                govt_id_back_image=final_govt_back,
                is_license_verified=is_verified,
                support_verification_status=support_status,
                support_reviewed_by=reviewer,
                support_reviewed_at=datetime.now(),
                support_notes=support_notes,
                notes=combined_notes,
                status=ride_status
            )
            success_message = f"🎉 Ride #{created_ride.id} is LIVE! You are a VERIFIED DRIVER on TamizhPayanam. No re-verification needed - your ride has been instantly published!"
            is_already_verified = True
        else:
            # First-time unverified driver -> routes to customer support
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
            is_already_verified = False

    return render(request, 'rides/publish.html', {
        'cities': all_cities,
        'success_message': success_message,
        'error_message': error_message,
        'created_ride': created_ride,
        'is_already_verified': locals().get('is_already_verified', False)
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


def cancel_ride_view(request, ride_id):
    """
    Allow driver to cancel their published ride.
    """
    ride = get_object_or_404(Ride, id=ride_id)
    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', 'Driver personal emergency or plan change').strip()
        ride.status = 'cancelled'
        ride.support_notes = f"CANCELLED BY DRIVER: {cancellation_reason}"
        ride.save()
        return redirect('/rides/my-rides/?cancelled=1')
    return render(request, 'rides/cancel_confirm.html', {'ride': ride})
