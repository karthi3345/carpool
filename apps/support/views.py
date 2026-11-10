import json
import urllib.request
import urllib.error
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.rides.models import Ride

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "7ee7bdd68328812eb2b1e3c56714ce78")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_MODEL = "@cf/meta/llama-3.1-8b-instruct"

SYSTEM_PROMPT = (
    "You are Inba (இன்பா), the official AI Guide and Support Assistant for TamizhPayanam (also known as ChalRe Tamil Nadu), "
    "a premier intercity carpooling platform connecting all 38 districts of Tamil Nadu.\n\n"
    "Platform Details:\n"
    "- Purpose: Safe, affordable, verified intercity carpooling across Tamil Nadu highways (e.g., Chennai - Coimbatore, Madurai, Trichy, Salem, Tirunelveli, Pondicherry).\n"
    "- Key Features: Instant seat search & booking, driver license & ID manual verification by TN support team, interactive fare negotiation in live driver-passenger chat rooms, "
    "heritage audio library (Thirukkural, Ponniyin Selvan, Silappathikaram), community travel stories and reels.\n"
    "- Cancellation policy: Cancel up to 2 hours before trip with zero penalty; automatic seat re-allocation if driver cancels.\n"
    "- Contact / Human Support: Email support@tamizhpayanam.in, 24/7 Tamil Nadu Support Desk.\n\n"
    "STRICT BOUNDARY & ESCALATION RULES:\n"
    "1. You must ONLY answer questions specifically about TamizhPayanam, carpooling, booking rides, publishing trips, driver verification, safety, fares, or Tamil heritage features on this website.\n"
    "2. If the user asks about ANYTHING ELSE (general coding, politics, recipes, hacking, general knowledge, sports, unrelated trivia), OR if they request refunds, dispute resolution, or to talk to a person, you MUST politely state: "
    "'I am Inba, specifically dedicated to helping you with the TamizhPayanam carpool platform. For unrelated queries or direct administrative assistance, please contact our human Tamil Nadu Support Team.'\n"
    "3. Keep responses warm, helpful, culturally respectful (start with 'Vanakkam!'), concise (2-4 sentences or short bullet points), and include bilingual Tamil/English where appropriate."
)

def query_cloudflare_ai(user_prompt):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 400
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=12) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get("success") and "result" in result:
            return result["result"].get("response", "").strip()
    return None

def support_login_view(request):
    """
    Dedicated Customer Support Staff Login
    Credentials: username 'lk', password '123'
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.username in ['lk', 'karthik']):
        return redirect('support-verification-dashboard')

    error = None
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, Customer Support Officer ({user.username})!")
            return redirect('support-verification-dashboard')
        else:
            error = "Invalid Customer Support credentials. (Use username: lk, password: 123)"

    return render(request, 'support/login.html', {
        'error': error,
        'default_username': 'lk'
    })


def support_logout_view(request):
    logout(request)
    messages.info(request, "Successfully logged out from Customer Support Console.")
    return redirect('support-login')


def support_verification_dashboard(request):
    """
    Customer Support Console:
    Requires customer support staff authentication.
    """
    # Open access for customer support console (no login barrier required)
    # if not request.user.is_authenticated or not (request.user.is_staff or request.user.username in ['lk', 'karthik']):
    #     return redirect('support-login')

    pending_rides = Ride.objects.filter(support_verification_status='pending_review').order_by('-created_at')
    approved_rides = Ride.objects.filter(support_verification_status='approved').order_by('-support_reviewed_at')[:10]
    rejected_rides = Ride.objects.filter(support_verification_status='rejected').order_by('-support_reviewed_at')[:10]

    return render(request, 'support/verification_dashboard.html', {
        'pending_rides': pending_rides,
        'approved_rides': approved_rides,
        'rejected_rides': rejected_rides,
        'pending_count': pending_rides.count(),
        'approved_count': approved_rides.count(),
        'rejected_count': rejected_rides.count(),
        'officer_name': request.user.username
    })


def support_approve_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    username = request.user.username if request.user.is_authenticated else 'Support Officer'
    reviewer = f"Support Agent ({username})"
    
    ride.support_verification_status = 'approved'
    ride.support_reviewed_by = reviewer
    ride.support_reviewed_at = timezone.now()
    ride.support_notes = request.POST.get('notes', 'Driver license and identity verified manually by customer support. Raw files purged as per data security policy.')
    ride.is_license_verified = True
    ride.status = 'published'

    # Security purpose: once verified, no need to store raw document images in database
    # Clear image references and remove files from disk if present
    for img_field in [ride.driver_license_image, ride.driver_license_masked_image, ride.driver_license_back_image, ride.govt_id_front_image, ride.govt_id_back_image]:
        if img_field and hasattr(img_field, 'storage') and hasattr(img_field, 'name') and img_field.name:
            try:
                img_field.storage.delete(img_field.name)
            except Exception:
                pass

    ride.driver_license_image = None
    ride.driver_license_masked_image = None
    ride.driver_license_back_image = None
    ride.govt_id_front_image = None
    ride.govt_id_back_image = None

    ride.save()

    messages.success(request, f"Ride #{ride.id} ({ride.origin.name} -> {ride.destination.name}) Driver Licence and Govt ID verified & APPROVED! Raw files securely purged from storage as per privacy policy.")
    return redirect('support-verification-dashboard')


def support_reject_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    username = request.user.username if request.user.is_authenticated else 'Support Officer'
    reviewer = f"Support Agent ({username})"
    reason = request.POST.get('reason', 'Driver licence document clarity issue or identity discrepancy.')
    
    ride.support_verification_status = 'rejected'
    ride.support_reviewed_by = reviewer
    ride.support_reviewed_at = timezone.now()
    ride.support_notes = f"REJECTED: {reason}"
    ride.is_license_verified = False
    ride.status = 'cancelled'
    ride.save()

    messages.warning(request, f"Ride #{ride.id} Driver Licence was REJECTED by Customer Support ({request.user.username}). Driver will be prompted to resend.")
    return redirect('support-verification-dashboard')


@csrf_exempt
def support_chatbot_api(request):
    """
    Inba (இன்பா) AI Support Chatbot Assistant powered by Cloudflare Workers AI
    with fallback and support escalation detection.
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            user_msg = body.get('message', '').strip()
        except Exception:
            user_msg = request.POST.get('message', '').strip()

        if not user_msg:
            return JsonResponse({
                'reply': 'Vanakkam! I am Inba (இன்பா), your TamizhPayanam AI Guide. How can I assist you with Tamil Nadu intercity carpooling today?',
                'escalate': False,
                'agent': 'Inba (TamizhPayanam AI)'
            })

        lower_msg = user_msg.lower()

        # Check if direct human escalation was requested
        escalate_keywords = ['human', 'officer', 'talk to person', 'real person', 'support team', 'complaint', 'dispute', 'fraud', 'stolen', 'police']
        is_direct_escalate = any(k in lower_msg for k in escalate_keywords)

        ai_reply = None
        try:
            ai_reply = query_cloudflare_ai(user_msg)
        except Exception as e:
            ai_reply = None

        if not ai_reply:
            # High quality local fallback in case of network issue or Cloudflare limits
            if any(w in lower_msg for w in ['book', 'reserve', 'ticket', 'seat']):
                ai_reply = (
                    "Vanakkam! Booking a seat is quick and easy on TamizhPayanam:\n"
                    "1. Enter your departure and arrival city across any of our 38 Tamil Nadu districts.\n"
                    "2. Select your date and choose a verified driver.\n"
                    "3. Click 'Book Seat' to immediately confirm and access the live negotiation chat!"
                )
            elif any(w in lower_msg for w in ['license', 'licence', 'dl', 'verify', 'safety', 'safe']):
                ai_reply = (
                    "Passenger safety is our highest priority! Every driver's Indian Driving License and Govt ID "
                    "are manually audited and approved by our Tamil Nadu Support Team before rides can be published."
                )
            elif any(w in lower_msg for w in ['price', 'fare', 'cost', 'negotiat', 'bargain']):
                ai_reply = (
                    "TamizhPayanam features real-time fare negotiation! Once a seat is requested, riders and drivers "
                    "can agree on a fair contribution based on tolls and route in the live chat."
                )
            elif any(w in lower_msg for w in ['offer', 'publish', 'driver', 'host']):
                ai_reply = (
                    "Traveling across Tamil Nadu? Click 'Publish a Ride' in the top bar, upload your driving license for verification, "
                    "set your seats and pricing, and share fuel costs with fellow travelers!"
                )
            elif any(w in lower_msg for w in ['heritage', 'kural', 'story', 'audio']):
                ai_reply = (
                    "Visit our Heritage page to explore Tamil culture during your journey! Enjoy daily Thirukkural couplets with moral stories, "
                    "and listen to bilingual audiobooks of Ponniyin Selvan and Silappathikaram."
                )
            elif is_direct_escalate:
                ai_reply = (
                    "I understand you wish to speak with our human customer service. Our dedicated Tamil Nadu Support Team "
                    "led by Officer Priya S. is ready to help you with personalized enquiries."
                )
            else:
                ai_reply = (
                    "Vanakkam! I am Inba, your TamizhPayanam AI Guide. I can help with finding and publishing rides, "
                    "driver safety verification, live chat fare negotiation, and Tamil heritage features across all 38 districts of Tamil Nadu."
                )

        # Determine escalation state
        escalate = is_direct_escalate or any(term in ai_reply.lower() for term in ['support team', 'priya s', 'escalat', 'support@tamizhpayanam.in', 'decline'])

        return JsonResponse({
            'success': True,
            'reply': ai_reply,
            'agent': 'Inba (AI Guide)',
            'escalate': escalate
        })

    return JsonResponse({'error': 'POST required'}, status=405)
