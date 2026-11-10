import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import CommunityPost, PostLike, PostComment

def get_user_identifier(request):
    if request.user.is_authenticated:
        return request.user.username
    if not request.session.session_key:
        request.session.save()
    return f"guest_{request.session.session_key}"

def get_author_name(request):
    if request.user.is_authenticated:
        return request.user.get_full_name() or request.user.username
    return request.POST.get('author_name', '').strip() or 'Travel Enthusiast'

def community_feed_view(request):
    """
    Facebook-styled Community Feed with posts, comments, likes, media, tags
    """
    tag_filter = request.GET.get('tag', 'all')
    search_query = request.GET.get('q', '').strip()

    posts_qs = CommunityPost.objects.all().prefetch_related('likes', 'comments')

    if tag_filter and tag_filter != 'all':
        posts_qs = posts_qs.filter(travel_tag__icontains=tag_filter)
    if search_query:
        posts_qs = posts_qs.filter(
            Q(content__icontains=search_query) |
            Q(author_name__icontains=search_query) |
            Q(travel_tag__icontains=search_query) |
            Q(author_city__icontains=search_query)
        )

    current_user_id = get_user_identifier(request)

    # Attach whether current user has liked each post
    post_list = []
    for p in posts_qs:
        liked_by_me = p.likes.filter(user_identifier=current_user_id).exists()
        post_list.append({
            'post': p,
            'liked_by_me': liked_by_me,
            'comments': p.comments.all()
        })

    tags = [
        'All Posts',
        'Travel Story',
        'Carpool Buddy',
        'Road Trip Tips',
        'Chennai to Bangalore',
        'Western Ghats Ride',
        'Safety & Verification'
    ]

    return render(request, 'community/feed.html', {
        'posts': post_list,
        'current_tag': tag_filter,
        'search_query': search_query,
        'tags': tags,
        'user_name': get_author_name(request),
        'is_logged_in': request.user.is_authenticated
    })


@csrf_exempt
def create_post_view(request):
    """
    Create a new community status post (with optional image)
    """
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Post content cannot be empty.'}, status=400)
            return redirect('/community/')

        author_name = get_author_name(request)
        author_city = request.POST.get('author_city', '').strip() or 'Tamil Nadu'
        travel_tag = request.POST.get('travel_tag', '').strip() or 'Travel Story'
        image_url = request.POST.get('image_url', '').strip()
        uploaded_image = request.FILES.get('image')

        user = request.user if request.user.is_authenticated else None

        post = CommunityPost.objects.create(
            author=user,
            author_name=author_name,
            author_city=author_city,
            content=content,
            travel_tag=travel_tag,
            image=uploaded_image,
            image_url=image_url
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
            return JsonResponse({
                'success': True,
                'post_id': post.id,
                'author_name': post.author_name,
                'content': post.content,
                'tag': post.travel_tag,
                'created_at': post.created_at.strftime('%d %b %Y, %I:%M %p')
            })

        return redirect('/community/')

    return redirect('/community/')


@csrf_exempt
def toggle_like_view(request, post_id):
    """
    Like / Unlike post via AJAX
    """
    if request.method == 'POST':
        post = get_object_or_404(CommunityPost, id=post_id)
        user_identifier = get_user_identifier(request)
        user = request.user if request.user.is_authenticated else None

        existing_like = PostLike.objects.filter(post=post, user_identifier=user_identifier).first()
        if existing_like:
            existing_like.delete()
            liked = False
        else:
            PostLike.objects.create(post=post, user=user, user_identifier=user_identifier)
            liked = True

        total_likes = post.likes.count()

        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': total_likes
        })

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@csrf_exempt
def add_comment_view(request, post_id):
    """
    Add a comment to a community post
    """
    if request.method == 'POST':
        post = get_object_or_404(CommunityPost, id=post_id)
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)

        author_name = get_author_name(request)
        user = request.user if request.user.is_authenticated else None

        comment = PostComment.objects.create(
            post=post,
            author=user,
            author_name=author_name,
            text=text
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'author_name': comment.author_name,
                'text': comment.text,
                'created_at': 'Just now',
                'total_comments': post.comments.count()
            })

        return redirect('/community/')

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
