from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date, time
from apps.locations.models import City
from apps.rides.models import Ride

class Command(BaseCommand):
    help = 'Seeds active intercity carpool rides across Tamil Nadu'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding Tamil Nadu Highway Rides...'))

        routes_data = [
            ('Chennai', 'Coimbatore', 650, '7h 30m', 'Koyambedu CMBT', 'Gandhipuram Stand'),
            ('Coimbatore', 'Chennai', 650, '7h 30m', 'Hope College Avinashi Rd', 'Guindy Kathipara'),
            ('Chennai', 'Madurai', 580, '6h 45m', 'Tambaram Sanatorium', 'Mattuthavani MIBT'),
            ('Madurai', 'Chennai', 580, '6h 45m', 'Arapalayam Bus Stand', 'Perungalathur Bypass'),
            ('Chennai', 'Trichy', 450, '5h 15m', 'Koyambedu CMBT', 'Central Bus Stand'),
            ('Trichy', 'Chennai', 450, '5h 15m', 'TVS Tollgate', 'Tambaram Station'),
            ('Coimbatore', 'Madurai', 320, '3h 45m', 'Singanallur Stand', 'Periyar Bus Stand'),
            ('Madurai', 'Coimbatore', 320, '3h 45m', 'Goripalayam', 'Ukkadam Bus Stand'),
            ('Chennai', 'Salem', 480, '5h 20m', 'Guindy Metro', 'New Bus Stand AVR'),
            ('Salem', 'Chennai', 480, '5h 20m', 'Kondalampatti Bypass', 'Koyambedu CMBT'),
            ('Madurai', 'Tirunelveli', 250, '2h 30m', 'Mattuthavani MIBT', 'Vaeinthaankulam Stand'),
            ('Coimbatore', 'Salem', 280, '2h 45m', 'KMCH Avinashi Rd', 'AVR Roundana'),
        ]

        drivers = [
            ('Suresh Kumar', 'Maruti Swift Dzire', 'TN-01-BK-4567'),
            ('Karthik Raja', 'Honda City i-VTEC', 'TN-09-CB-1289'),
            ('Aravind Swaminathan', 'Hyundai Creta SX', 'TN-38-AL-8890'),
            ('Vignesh Natarajan', 'Tata Nexon EV Max', 'TN-07-CY-3341'),
            ('Manoj Pandian', 'Toyota Innova Crysta', 'TN-58-EK-9022'),
            ('Praveen Kumar', 'Volkswagen Virtus GT', 'TN-02-BM-7711'),
        ]

        today = date.today()
        created_count = 0

        # Seed 7 days ahead
        for day_offset in range(0, 8):
            ride_date = today + timedelta(days=day_offset)
            for i, r in enumerate(routes_data):
                origin_city = City.objects.filter(name=r[0]).first()
                dest_city = City.objects.filter(name=r[1]).first()
                if not origin_city or not dest_city:
                    continue

                drv = drivers[i % len(drivers)]
                dep_hour = 6 + (i * 2) % 15
                dep_time = time(dep_hour, 30 if i % 2 == 1 else 0)

                ride, created = Ride.objects.get_or_create(
                    origin=origin_city,
                    destination=dest_city,
                    departure_date=ride_date,
                    departure_time=dep_time,
                    defaults={
                        'origin_point': r[4],
                        'destination_point': r[5],
                        'price_per_seat': r[2],
                        'duration_text': r[3],
                        'driver_name': drv[0],
                        'vehicle_model': drv[1],
                        'vehicle_number': drv[2],
                        'available_seats': 3,
                        'total_seats': 4,
                        'status': 'published',
                        'notes': 'Verified Tamil Nadu intercity carpool. Clean AC sedan, strictly no smoking.'
                    }
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded successfully: {created_count} active rides across Tamil Nadu. Total active rides in DB: {Ride.objects.count()}'
        ))
