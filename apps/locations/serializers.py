from rest_framework import serializers
from .models import City, PopularPoint

class PopularPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopularPoint
        fields = ['id', 'name', 'point_type']

class CitySerializer(serializers.ModelSerializer):
    points = PopularPointSerializer(many=True, read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'district', 'state', 'latitude', 'longitude', 'is_popular', 'points']
