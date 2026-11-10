import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def login_view(request):
    error_message = None
    next_url = request.GET.get('next', '/')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not identifier or not password:
            error_message = "Please enter both username/email and password."
            return render(request, 'accounts/login.html', {
                'error_message': error_message,
                'next_url': next_url,
                'entered_identifier': identifier
            })

        user = None
        # 1. Check case-insensitive username match
        matched_user = User.objects.filter(username__iexact=identifier).first()
        
        # 2. If not found by username or looks like an email, check case-insensitive email match
        if not matched_user:
            matched_user = User.objects.filter(email__iexact=identifier).first()

        if matched_user:
            user = authenticate(request, username=matched_user.username, password=password)

        # 3. Direct authenticate fallback
        if user is None:
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            error_message = "Invalid username/email or password. Please verify your credentials and try again."

    return render(request, 'accounts/login.html', {
        'error_message': error_message,
        'next_url': next_url
    })


def register_view(request):
    error_message = None
    form_data = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        email_otp_verified = request.POST.get('email_otp_verified', '0') == '1'
        phone_otp_verified = request.POST.get('phone_otp_verified', '0') == '1'

        form_data = {
            'username': username,
            'email': email,
            'phone_number': phone_number,
        }

        # Rigorous Validations
        if not username or not email or not phone_number or not password:
            error_message = "All fields (Username, Email ID, Mobile Number, Password) are required."
        elif not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            error_message = "Username must be 3-30 characters long and can only contain letters, numbers, and underscores."
        elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            error_message = "Please enter a valid email address (e.g. name@example.com)."
        elif not re.match(r'^[6-9]\d{9}$', phone_number):
            error_message = "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error_message = "Password and Confirm Password do not match."
        elif not email_otp_verified:
            error_message = "Please verify your Email ID with the 4-digit OTP (dummy OTP 2727)."
        elif not phone_otp_verified:
            error_message = "Please verify your Mobile Number with the 4-digit OTP (dummy OTP 2727)."
        elif User.objects.filter(username__iexact=username).exists():
            error_message = f"The username '{username}' is already taken. Please choose another username."
        elif User.objects.filter(email__iexact=email).exists():
            error_message = f"An account with email '{email}' already exists. Please log in instead."
        else:
            # Create user account with explicit password hashing
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=username.title()
            )
            user.set_password(password)
            user.save()

            # Authenticate and login the new registered user directly
            auth_user = authenticate(request, username=username, password=password)
            if auth_user:
                login(request, auth_user)
            else:
                login(request, user)
            return redirect('/')

    return render(request, 'accounts/register.html', {
        'error_message': error_message,
        'form_data': form_data
    })


def logout_view(request):
    logout(request)
    return redirect('/')
