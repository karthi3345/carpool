from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import City
from .serializers import CitySerializer

class CityListAPIView(APIView):
    """
    REST API endpoint: Returns all Tamil Nadu cities or filters by search query.
    GET /api/v1/locations/cities/?q=che
    """
    def get(self, request):
        query = request.GET.get('q', '').strip()
        popular_only = request.GET.get('popular', '').lower() == 'true'

        cities = City.objects.filter(state='Tamil Nadu')
        if popular_only:
            cities = cities.filter(is_popular=True)
        if query:
            cities = cities.filter(Q(name__icontains=query) | Q(district__icontains=query))

        serializer = CitySerializer(cities, many=True)
        return Response({
            'success': True,
            'state': 'Tamil Nadu',
            'count': len(serializer.data),
            'cities': serializer.data
        }, status=status.HTTP_200_OK)

class PopularCorridorsAPIView(APIView):
    """
    REST API endpoint for popular Tamil Nadu intercity routes.
    GET /api/v1/locations/popular-corridors/
    """
    def get(self, request):
        corridors = [
            {'from': 'Chennai', 'to': 'Coimbatore', 'distance': '510 km', 'duration': '7h 30m', 'fare_from': 650, 'highway': 'NH 48 / NH 544'},
            {'from': 'Chennai', 'to': 'Madurai', 'distance': '460 km', 'duration': '6h 45m', 'fare_from': 580, 'highway': 'NH 38 (GST Road)'},
            {'from': 'Chennai', 'to': 'Trichy', 'distance': '330 km', 'duration': '5h 15m', 'fare_from': 450, 'highway': 'NH 38'},
            {'from': 'Coimbatore', 'to': 'Madurai', 'distance': '215 km', 'duration': '3h 45m', 'fare_from': 320, 'highway': 'NH 83'},
            {'from': 'Chennai', 'to': 'Salem', 'distance': '345 km', 'duration': '5h 20m', 'fare_from': 480, 'highway': 'NH 48 / NH 79'},
            {'from': 'Madurai', 'to': 'Tirunelveli', 'distance': '160 km', 'duration': '2h 30m', 'fare_from': 250, 'highway': 'NH 44'},
            {'from': 'Coimbatore', 'to': 'Salem', 'distance': '165 km', 'duration': '2h 45m', 'fare_from': 280, 'highway': 'NH 544'},
            {'from': 'Trichy', 'to': 'Thanjavur', 'distance': '58 km', 'duration': '1h 05m', 'fare_from': 120, 'highway': 'NH 83'},
        ]
        return Response({
            'success': True,
            'state': 'Tamil Nadu',
            'corridors': corridors
        }, status=status.HTTP_200_OK)
