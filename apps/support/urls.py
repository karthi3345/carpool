from django.urls import path
from .views import (
    support_verification_dashboard,
    support_approve_ride,
    support_reject_ride,
    support_login_view,
    support_logout_view,
    support_chatbot_api,
)

urlpatterns = [
    path('', support_verification_dashboard, name='support-verification-dashboard'),
    path('login/', support_login_view, name='support-login'),
    path('logout/', support_logout_view, name='support-logout'),
    path('rides/<int:ride_id>/approve/', support_approve_ride, name='support-approve-ride'),
    path('rides/<int:ride_id>/reject/', support_reject_ride, name='support-reject-ride'),
    path('chat/', support_chatbot_api, name='support-chatbot-api'),
]
