from django.core.management.base import BaseCommand
from apps.locations.models import City, PopularPoint

TAMIL_NADU_DISTRICTS_DATA = [
    {
        'name': 'Chennai',
        'district': 'Chennai',
        'is_popular': True,
        'lat': 13.0827, 'lng': 80.2707,
        'points': ['Koyambedu CMBT', 'Guindy Kathipara', 'Tambaram Sanatorium', 'Perungalathur Bypass', 'Chennai Central']
    },
    {
        'name': 'Coimbatore',
        'district': 'Coimbatore',
        'is_popular': True,
        'lat': 11.0168, 'lng': 76.9558,
        'points': ['Gandhipuram Central Bus Stand', 'Singanallur Bus Stand', 'Ukkadam Bus Stand', 'KMCH Avinashi Road', 'Hope College']
    },
    {
        'name': 'Madurai',
        'district': 'Madurai',
        'is_popular': True,
        'lat': 9.9252, 'lng': 78.1198,
        'points': ['Mattuthavani Integrated Bus Stand (MIBT)', 'Arapalayam Bus Stand', 'Periyar Bus Stand', 'Goripalayam', 'Koodal Nagar']
    },
    {
        'name': 'Tiruchirappalli (Trichy)',
        'district': 'Tiruchirappalli',
        'is_popular': True,
        'lat': 10.7905, 'lng': 78.7047,
        'points': ['Central Bus Stand', 'Chatram Bus Stand', 'TVS Tollgate', 'Samayapuram Toll Plaza', 'NIT Trichy Tanjore Road']
    },
    {
        'name': 'Salem',
        'district': 'Salem',
        'is_popular': True,
        'lat': 11.6643, 'lng': 78.1460,
        'points': ['New Bus Stand', 'Old Bus Stand', 'AVR Roundana', 'Kondalampatti Bypass', 'Seelanaickenpatti']
    },
    {
        'name': 'Tirunelveli',
        'district': 'Tirunelveli',
        'is_popular': True,
        'lat': 8.7139, 'lng': 77.7567,
        'points': ['New Bus Stand (Vaeinthaankulam)', 'Palayamkottai Bus Stand', 'Junction Railway Station', 'Vannarpettai']
    },
    {
        'name': 'Erode',
        'district': 'Erode',
        'is_popular': True,
        'lat': 11.3410, 'lng': 77.7172,
        'points': ['Central Bus Stand', 'Solar Bus Terminal', 'Perundurai Bypass', 'Thindal']
    },
    {
        'name': 'Tiruppur',
        'district': 'Tiruppur',
        'is_popular': True,
        'lat': 11.1085, 'lng': 77.3411,
        'points': ['Old Bus Stand', 'New Bus Stand', 'Avinashi Bypass', 'Palladam Road']
    },
    {
        'name': 'Vellore',
        'district': 'Vellore',
        'is_popular': True,
        'lat': 12.9165, 'lng': 79.1325,
        'points': ['New Bus Stand', 'Katpadi Junction', 'Green Circle', 'VIT Campus Entrance', 'Bagayam']
    },
    {
        'name': 'Thanjavur',
        'district': 'Thanjavur',
        'is_popular': True,
        'lat': 10.7870, 'lng': 79.1378,
        'points': ['New Bus Stand', 'Old Bus Stand', 'Medical College Road', 'Vallam']
    },
    {
        'name': 'Dindigul',
        'district': 'Dindigul',
        'is_popular': True,
        'lat': 10.3673, 'lng': 77.9803,
        'points': ['Dindigul Central Bus Stand', 'Nagal Nagar', 'Bypass Tollgate', 'Collectorate']
    },
    {
        'name': 'Nagercoil (Kanyakumari)',
        'district': 'Kanyakumari',
        'is_popular': True,
        'lat': 8.1833, 'lng': 77.4119,
        'points': ['Vadasery Christopher Bus Stand', 'Anna Bus Stand', 'Chettikulam', 'Kavalkinaru Junction']
    },
    {
        'name': 'Tuticorin (Thoothukudi)',
        'district': 'Thoothukudi',
        'is_popular': False,
        'lat': 8.7642, 'lng': 78.1348,
        'points': ['New Bus Stand', 'Old Bus Stand', 'VVD Signal', 'Harbour Estate']
    },
    {
        'name': 'Hosur',
        'district': 'Krishnagiri',
        'is_popular': True,
        'lat': 12.7409, 'lng': 77.8253,
        'points': ['Hosur Bus Stand', 'Zuzuvadi Border', 'Bagalur HUDCO', 'Sipcot Ring Road']
    },
    {
        'name': 'Kanchipuram',
        'district': 'Kanchipuram',
        'is_popular': False,
        'lat': 12.8342, 'lng': 79.7036,
        'points': ['Kanchipuram Bus Stand', 'Sunguvarchatram Bypass', 'Sriperumbudur Toll']
    },
    {
        'name': 'Chengalpattu',
        'district': 'Chengalpattu',
        'is_popular': True,
        'lat': 12.6841, 'lng': 79.9836,
        'points': ['Chengalpattu Old Bus Stand', 'Mahindra World City Toll', 'Toll Plaza Paranur', 'Guduvanchery']
    },
    {
        'name': 'Karur',
        'district': 'Karur',
        'is_popular': False,
        'lat': 10.9601, 'lng': 78.0766,
        'points': ['Central Bus Stand', 'Vengamedu', 'Thanthonimalai', 'Bypass Ring Road']
    },
    {
        'name': 'Namakkal',
        'district': 'Namakkal',
        'is_popular': False,
        'lat': 11.2189, 'lng': 78.1674,
        'points': ['Namakkal Bus Stand', 'Mudalaipatti Bypass', 'Mohanur Road']
    },
    {
        'name': 'Krishnagiri',
        'district': 'Krishnagiri',
        'is_popular': False,
        'lat': 12.5186, 'lng': 78.2137,
        'points': ['New Bus Stand', 'Tollgate NH 44', 'Rayakottai Flyover']
    },
    {
        'name': 'Dharmapuri',
        'district': 'Dharmapuri',
        'is_popular': False,
        'lat': 12.1211, 'lng': 78.1582,
        'points': ['Dharmapuri Central Bus Stand', 'Four Road Junction', 'Thoppur Tollgate']
    },
    {
        'name': 'Cuddalore',
        'district': 'Cuddalore',
        'is_popular': False,
        'lat': 11.7480, 'lng': 79.7714,
        'points': ['Cuddalore Bus Stand', 'Thirupapuliyur', 'Nellikuppam Road']
    },
    {
        'name': 'Villupuram',
        'district': 'Villupuram',
        'is_popular': True,
        'lat': 11.9401, 'lng': 79.4861,
        'points': ['Villupuram New Bus Stand', 'Janakipuram Tollgate', 'Vikravandi Toll Plaza']
    },
    {
        'name': 'Tiruvannamalai',
        'district': 'Tiruvannamalai',
        'is_popular': True,
        'lat': 12.2253, 'lng': 79.0747,
        'points': ['Central Bus Stand', 'Girivalam Path Point', 'Chengam Road', 'Polur Road']
    },
    {
        'name': 'Pudukkottai',
        'district': 'Pudukkottai',
        'is_popular': False,
        'lat': 10.3797, 'lng': 78.8208,
        'points': ['Pudukkottai New Bus Stand', 'Old Bus Stand', 'Machuvadi']
    },
    {
        'name': 'Sivaganga',
        'district': 'Sivaganga',
        'is_popular': False,
        'lat': 9.8433, 'lng': 78.4809,
        'points': ['Sivaganga Bus Stand', 'Karaikudi New Bus Stand', 'Devakottai Rastha']
    },
    {
        'name': 'Ramanathapuram',
        'district': 'Ramanathapuram',
        'is_popular': False,
        'lat': 9.3639, 'lng': 78.8395,
        'points': ['Ramanathapuram Bus Stand', 'Rameswaram Temple Stand', 'Paramakudi Bus Stand']
    },
    {
        'name': 'Virudhunagar',
        'district': 'Virudhunagar',
        'is_popular': False,
        'lat': 9.5680, 'lng': 77.9624,
        'points': ['Virudhunagar Bus Stand', 'Sivakasi Bus Stand', 'Aruppukottai Stand']
    },
    {
        'name': 'Theni',
        'district': 'Theni',
        'is_popular': False,
        'lat': 10.0104, 'lng': 77.4768,
        'points': ['Theni New Bus Stand', 'Periyakulam Stand', 'Bodinayakanur Stand', 'Cumbum']
    },
    {
        'name': 'Nagapattinam',
        'district': 'Nagapattinam',
        'is_popular': False,
        'lat': 10.7672, 'lng': 79.8449,
        'points': ['Nagapattinam Bus Stand', 'Velankanni Stand', 'Nagore Dargah Stand']
    },
    {
        'name': 'Mayiladuthurai',
        'district': 'Mayiladuthurai',
        'is_popular': False,
        'lat': 11.1075, 'lng': 79.6524,
        'points': ['Mayiladuthurai New Bus Stand', 'Sirkazhi Stand', 'Kuthalam']
    },
    {
        'name': 'Tiruvarur',
        'district': 'Tiruvarur',
        'is_popular': False,
        'lat': 10.7725, 'lng': 79.6365,
        'points': ['Tiruvarur New Bus Stand', 'Mannargudi Stand', 'Thiruthuraipoondi']
    },
    {
        'name': 'Nilgiris (Ooty)',
        'district': 'Nilgiris',
        'is_popular': True,
        'lat': 11.4102, 'lng': 76.6950,
        'points': ['Ooty Central Bus Stand', 'Coonoor Bus Stand', 'Kotagiri Stand', 'Gudalur Stand']
    },
    {
        'name': 'Tenkasi',
        'district': 'Tenkasi',
        'is_popular': False,
        'lat': 8.9594, 'lng': 77.3161,
        'points': ['Tenkasi New Bus Stand', 'Courtallam Falls Stand', 'Sankarankovil Stand']
    },
    {
        'name': 'Ranipet',
        'district': 'Ranipet',
        'is_popular': False,
        'lat': 12.9224, 'lng': 79.3330,
        'points': ['Ranipet Stand', 'Walajah Tollgate', 'Arcot Bus Stand', 'Arakkonam Junction']
    },
    {
        'name': 'Tirupathur',
        'district': 'Tirupathur',
        'is_popular': False,
        'lat': 12.4965, 'lng': 78.5678,
        'points': ['Tirupathur Bus Stand', 'Vaniyambadi Tollgate', 'Ambur Bypass']
    },
    {
        'name': 'Kallakurichi',
        'district': 'Kallakurichi',
        'is_popular': False,
        'lat': 11.7383, 'lng': 78.9639,
        'points': ['Kallakurichi Bus Stand', 'Chinnasalem Bypass', 'Ulundurpet Tollgate']
    },
    {
        'name': 'Ariyalur',
        'district': 'Ariyalur',
        'is_popular': False,
        'lat': 11.1401, 'lng': 79.0786,
        'points': ['Ariyalur Bus Stand', 'Jayankondam Stand', 'Sendurai']
    },
    {
        'name': 'Perambalur',
        'district': 'Perambalur',
        'is_popular': False,
        'lat': 11.2342, 'lng': 78.8820,
        'points': ['Perambalur New Bus Stand', 'NH 38 Bypass Stand', 'Thirumandurai Tollgate']
    }
]

class Command(BaseCommand):
    help = 'Seeds all 38 Tamil Nadu districts and major pickup points'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Tamil Nadu Districts & Cities Seeder...'))
        total_cities = 0
        total_points = 0

        for item in TAMIL_NADU_DISTRICTS_DATA:
            city, created = City.objects.get_or_create(
                name=item['name'],
                defaults={
                    'district': item['district'],
                    'state': 'Tamil Nadu',
                    'is_popular': item['is_popular'],
                    'latitude': item['lat'],
                    'longitude': item['lng'],
                }
            )
            if created:
                total_cities += 1

            for pt in item['points']:
                point, pt_created = PopularPoint.objects.get_or_create(
                    city=city,
                    name=pt
                )
                if pt_created:
                    total_points += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded successfully: {total_cities} Tamil Nadu Cities, {total_points} Pickup Points. Total in DB: {City.objects.count()} TN cities.'
        ))
