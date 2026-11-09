from django.urls import path
from .views import (
    create_booking_view,
    booking_chat_view,
    send_message_view,
    driver_approve_booking_view,
    driver_reject_booking_view,
)

urlpatterns = [
    path('create/', create_booking_view, name='booking-create'),
    path('<str:booking_code>/chat/', booking_chat_view, name='booking-chat'),
    path('<str:booking_code>/send-message/', send_message_view, name='booking-send-message'),
    path('<str:booking_code>/approve/', driver_approve_booking_view, name='booking-approve'),
    path('<str:booking_code>/reject/', driver_reject_booking_view, name='booking-reject'),
]
