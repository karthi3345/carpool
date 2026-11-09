from django.urls import path
from .views import dummy_login_view, dummy_logout_view

urlpatterns = [
    path('login/', dummy_login_view, name='login'),
    path('logout/', dummy_logout_view, name='logout'),
    path('register/', dummy_login_view, name='register'),
]
