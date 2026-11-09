from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def dummy_login_view(request):
    error_message = None
    next_url = request.GET.get('next', '/')

    # Ensure default dummy account exists with password 123
    demo_user, _ = User.objects.get_or_create(
        username='karthik',
        defaults={'first_name': 'Karthik', 'last_name': 'Raja', 'email': 'karthik@chalre.in'}
    )
    if not demo_user.check_password('123'):
        demo_user.set_password('123')
        demo_user.save()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Quick one-click demo login button support
        if 'quick_demo' in request.POST:
            username = 'karthik'
            password = '123'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            # If user entered password 123 for any user, allow auto-create or login
            if password == '123' and username:
                user, _ = User.objects.get_or_create(username=username, defaults={'first_name': username.title()})
                user.set_password('123')
                user.save()
                login(request, user)
                return redirect(next_url)
            error_message = "Invalid credentials. (Hint: Use username 'karthik' with password '123')"

    return render(request, 'accounts/login.html', {
        'error_message': error_message,
        'next_url': next_url
    })

def dummy_logout_view(request):
    logout(request)
    return redirect('/')
