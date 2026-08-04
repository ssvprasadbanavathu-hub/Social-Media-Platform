from django.contrib import admin
from django.utils.html import format_html
from app.models import UserProfile, Post, Comment, Like, Follow, Notification, SavedPost

admin.site.site_header = "MyFriend Administration"
admin.site.site_title = "MyFriend Admin Portal"
admin.site.index_title = "Welcome to MyFriend Super Administrator Portal"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'website', 'avatar_preview', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'location', 'bio')
    list_filter = ('created_at',)
    readonly_fields = ('avatar_preview', 'created_at')
    ordering = ('-created_at',)

    def avatar_preview(self, obj):
        return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.avatar_url)
    avatar_preview.short_description = 'Avatar'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'caption_truncated', 'image_preview', 'likes_count', 'comments_count', 'created_at')
    search_fields = ('author__username', 'author__email', 'caption')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def caption_truncated(self, obj):
        return obj.caption[:50] + ('...' if len(obj.caption) > 50 else '')
    caption_truncated.short_description = 'Caption'

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover;" />', obj.image_url)
        return "No image"
    image_preview.short_description = 'Media'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'comment_truncated', 'created_at')
    search_fields = ('author__username', 'comment', 'post__caption')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def comment_truncated(self, obj):
        return obj.comment[:40] + ('...' if len(obj.comment) > 40 else '')
    comment_truncated.short_description = 'Comment'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    search_fields = ('user__username', 'post__caption')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'receiver', 'sender', 'notification_type', 'is_read', 'created_at')
    search_fields = ('receiver__username', 'sender__username')
    list_filter = ('notification_type', 'is_read', 'created_at')
    ordering = ('-created_at',)


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    search_fields = ('user__username', 'post__caption')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
