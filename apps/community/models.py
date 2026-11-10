from django.db import models
from django.contrib.auth.models import User

class CommunityPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts', null=True, blank=True)
    author_name = models.CharField(max_length=120)
    author_city = models.CharField(max_length=100, default='Chennai, TN')
    content = models.TextField()
    image = models.ImageField(upload_to='community_posts/', null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True) # supports external or preset travel images
    travel_tag = models.CharField(max_length=80, blank=True, default='Travel Story') # e.g. Chennai to Ooty, Ride Experience, Travel Tip, Carpool Buddy
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name}: {self.content[:40]}"

    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def total_comments(self):
        return self.comments.count()


class TravelReel(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_reels', null=True, blank=True)
    creator_name = models.CharField(max_length=120)
    creator_avatar = models.CharField(max_length=255, blank=True, default='')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='travel_reels/', null=True, blank=True)
    video_url = models.CharField(max_length=500, default='/static/videos/car_drive.mp4')
    sound_title = models.CharField(max_length=150, default='Original Audio - Highway Beats')
    route_tag = models.CharField(max_length=100, default='Chennai → Ooty')
    likes_count = models.PositiveIntegerField(default=120)
    comments_count = models.PositiveIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.creator_name} - {self.title}"

    @property
    def get_video_src(self):
        if self.video_file:
            return self.video_file.url
        return self.video_url


class PostLike(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes', null=True, blank=True)
    user_identifier = models.CharField(max_length=120) # stores username or guest session ID
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user_identifier')

    def __str__(self):
        return f"{self.user_identifier} likes #{self.post_id}"


class PostComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments', null=True, blank=True)
    author_name = models.CharField(max_length=120)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author_name} on #{self.post_id}: {self.text[:30]}"
