from django.urls import path
from .views import (
    ride_detail_view,
    RideListCreateAPIView,
    search_rides_view,
    publish_ride_view,
    verify_license_api_view
)

urlpatterns = [
    path('', RideListCreateAPIView.as_view(), name='api-rides-list'),
    path('search/', search_rides_view, name='rides-search'),
    path('publish/', publish_ride_view, name='rides-publish'),
    path('<int:ride_id>/', ride_detail_view, name='ride-detail'),
    path('verify-license/', verify_license_api_view, name='api-verify-license'),
]
