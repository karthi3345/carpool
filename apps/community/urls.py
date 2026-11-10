from django.urls import path
from .views import (
    community_feed_view,
    create_post_view,
    toggle_like_view,
    toggle_reel_like_view,
    add_comment_view,
)

urlpatterns = [
    path('', community_feed_view, name='community-feed'),
    path('post/create/', create_post_view, name='community-post-create'),
    path('post/<int:post_id>/like/', toggle_like_view, name='community-post-like'),
    path('reel/<int:reel_id>/like/', toggle_reel_like_view, name='community-reel-like'),
    path('post/<int:post_id>/comment/', add_comment_view, name='community-post-comment'),
]
