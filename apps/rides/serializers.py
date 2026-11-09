from rest_framework import serializers
from .models import Ride
from apps.locations.serializers import CitySerializer

class RideSerializer(serializers.ModelSerializer):
    origin = CitySerializer(read_only=True)
    destination = CitySerializer(read_only=True)

    class Meta:
        model = Ride
        fields = [
            'id', 'origin', 'origin_point', 'destination', 'destination_point',
            'departure_date', 'departure_time', 'estimated_arrival', 'duration_text',
            'driver_name', 'driver_rating', 'vehicle_model', 'vehicle_number',
            'available_seats', 'total_seats', 'price_per_seat', 'status', 'notes'
        ]
