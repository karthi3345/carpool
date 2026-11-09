from django.urls import path
from .views import CityListAPIView, PopularCorridorsAPIView

urlpatterns = [
    path('cities/', CityListAPIView.as_view(), name='api-cities'),
    path('popular-corridors/', PopularCorridorsAPIView.as_view(), name='api-popular-corridors'),
]
