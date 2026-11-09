from django.urls import path
from .views import submit_passenger_review, get_ride_reviews_api

urlpatterns = [
    path('rides/<int:ride_id>/submit/', submit_passenger_review, name='submit-passenger-review'),
    path('rides/<int:ride_id>/list/', get_ride_reviews_api, name='api-ride-reviews'),
]
