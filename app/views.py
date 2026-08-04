from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.views.decorators.http import require_POST

from app.models import UserProfile, Post, Comment, Like, Follow, Notification, SavedPost
from app.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm
from app.utils import create_notification


def unread_notifications_context(request):
    """Context processor to provide unread notification count across templates."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}


def landing_view(request):
    """Landing page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MyFriend, {user.username}! Your account has been created successfully.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User login view with username/email support and inactive user detection."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username_or_email or not password:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'login.html')

        user = None
        # Check by email or username
        user_candidates = User.objects.filter(
            Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
        )

        target_candidate = user_candidates.first()
        if target_candidate and not target_candidate.is_active:
            messages.error(request, "Your account is currently inactive. Please contact support.")
            return render(request, 'login.html')

        if target_candidate:
            user = authenticate(request, username=target_candidate.username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'home')
            else:
                messages.error(request, "Your account is currently inactive.")
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'login.html')


@login_required
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('landing')


@login_required
def home_view(request):
    """Main feed displaying posts from followed users + user's own posts, optimized against N+1 queries."""
    post_form = PostForm()
    comment_form = CommentForm()

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been published!")
            return redirect('home')

    following_ids = request.user.following_set.values_list('following_id', flat=True)
    followed_user_ids = list(following_ids) + [request.user.id]

    feed_posts = Post.objects.filter(author_id__in=followed_user_ids).distinct()

    if feed_posts.count() < 3:
        feed_posts = Post.objects.all()

    # Optimize with select_related and prefetch_related
    comments_prefetch = Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author', 'author__profile').order_by('created_at')
    )

    feed_posts = feed_posts.select_related('author', 'author__profile').prefetch_related('likes', comments_prefetch)

    paginator = Paginator(feed_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    liked_post_ids = set(Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))
    saved_post_ids = set(SavedPost.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))

    suggested_users = User.objects.exclude(id__in=followed_user_ids).select_related('profile')[:5]
    trending_users = User.objects.exclude(id=request.user.id).select_related('profile').annotate(followers_cnt=Count('followers_set')).order_by('-followers_cnt')[:5]

    context = {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'post_form': post_form,
        'comment_form': comment_form,
        'liked_post_ids': liked_post_ids,
        'saved_post_ids': saved_post_ids,
        'suggested_users': suggested_users,
        'trending_users': trending_users,
    }
    return render(request, 'home.html', context)


@login_required
def profile_view(request, username):
    """User profile page showing details, posts, saved, and liked posts."""
    profile_user = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    profile = profile_user.profile

    is_self = (request.user == profile_user)
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    active_tab = request.GET.get('tab', 'posts')

    comments_prefetch = Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author', 'author__profile').order_by('created_at')
    )

    if active_tab == 'saved' and is_self:
        posts = Post.objects.filter(saved_by__user=request.user).select_related('author', 'author__profile').prefetch_related('likes', comments_prefetch)
    elif active_tab == 'liked' and is_self:
        posts = Post.objects.filter(likes__user=request.user).select_related('author', 'author__profile').prefetch_related('likes', comments_prefetch)
    else:
        active_tab = 'posts'
        posts = Post.objects.filter(author=profile_user).select_related('author', 'author__profile').prefetch_related('likes', comments_prefetch)

    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    liked_post_ids = set(Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))
    saved_post_ids = set(SavedPost.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))

    comment_form = CommentForm()

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'is_self': is_self,
        'is_following': is_following,
        'active_tab': active_tab,
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'liked_post_ids': liked_post_ids,
        'saved_post_ids': saved_post_ids,
        'comment_form': comment_form,
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit current user profile details."""
    profile = request.user.profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'edit_profile.html', context)


@login_required
def followers_view(request, username):
    """Display list of followers for a given user."""
    target_user = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    followers_relations = Follow.objects.filter(following=target_user).select_related('follower', 'follower__profile')

    user_following_ids = set(request.user.following_set.values_list('following_id', flat=True))

    context = {
        'target_user': target_user,
        'followers_relations': followers_relations,
        'user_following_ids': user_following_ids,
    }
    return render(request, 'followers.html', context)


@login_required
def following_view(request, username):
    """Display list of users followed by a given user."""
    target_user = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    following_relations = Follow.objects.filter(follower=target_user).select_related('following', 'following__profile')

    user_following_ids = set(request.user.following_set.values_list('following_id', flat=True))

    context = {
        'target_user': target_user,
        'following_relations': following_relations,
        'user_following_ids': user_following_ids,
    }
    return render(request, 'following.html', context)


@login_required
def notifications_view(request):
    """Display user notifications."""
    notifications = Notification.objects.filter(receiver=request.user).select_related('sender', 'sender__profile', 'post')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications.html', context)


@login_required
@require_POST
def mark_notifications_read_ajax(request):
    """AJAX endpoint to mark all unread notifications as read."""
    Notification.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
def search_view(request):
    """Search users by username/name or posts by caption."""
    query = request.GET.get('q', '').strip()
    users_results = []
    posts_results = []

    comments_prefetch = Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author', 'author__profile').order_by('created_at')
    )

    if query:
        users_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).select_related('profile').distinct()[:20]

        posts_results = Post.objects.filter(
            caption__icontains=query
        ).select_related('author', 'author__profile').prefetch_related('likes', comments_prefetch).distinct()[:20]

    user_following_ids = set(request.user.following_set.values_list('following_id', flat=True))
    liked_post_ids = set(Like.objects.filter(user=request.user, post__in=posts_results).values_list('post_id', flat=True))
    saved_post_ids = set(SavedPost.objects.filter(user=request.user, post__in=posts_results).values_list('post_id', flat=True))

    context = {
        'query': query,
        'users_results': users_results,
        'posts_results': posts_results,
        'user_following_ids': user_following_ids,
        'liked_post_ids': liked_post_ids,
        'saved_post_ids': saved_post_ids,
        'comment_form': CommentForm(),
    }
    return render(request, 'search.html', context)


@login_required
def settings_view(request):
    """User account settings and password change."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'settings.html', {'form': form})


@login_required
def post_detail_view(request, post_id):
    """Detailed view for a single post with comments."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile').prefetch_related('likes'),
        id=post_id
    )
    comments = post.comments.select_related('author', 'author__profile').all()
    comment_form = CommentForm()

    is_liked = Like.objects.filter(user=request.user, post=post).exists()
    is_saved = SavedPost.objects.filter(user=request.user, post=post).exists()

    if request.method == 'POST':
        c_form = CommentForm(request.POST)
        if c_form.is_valid():
            comment = c_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            create_notification(sender=request.user, receiver=post.author, notification_type='comment', post=post)
            messages.success(request, "Comment added successfully!")
            return redirect('post_detail', post_id=post.id)

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_saved': is_saved,
    }
    return render(request, 'post_detail.html', context)


@login_required
def edit_post_view(request, post_id):
    """Edit an existing post owned by request.user."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully!")
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'edit_post.html', {'form': form, 'post': post})


@login_required
@require_POST
def delete_post_view(request, post_id):
    """Delete a post owned by request.user."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    post.delete()
    messages.success(request, "Post has been deleted.")
    return redirect('home')


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    """Delete a comment if user is comment author or post author."""
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user and comment.post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    post_id = comment.post.id
    comment.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'deleted', 'comments_count': Comment.objects.filter(post_id=post_id).count()})

    messages.success(request, "Comment deleted.")
    return redirect('post_detail', post_id=post_id)


# ===================== AJAX API ENDPOINTS ===================== #

@login_required
@require_POST
def like_post_ajax(request, post_id):
    """AJAX endpoint to like/unlike a post."""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        create_notification(sender=request.user, receiver=post.author, notification_type='like', post=post)

    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes_count
    })


@login_required
@require_POST
def save_post_ajax(request, post_id):
    """AJAX endpoint to save/unsave a post."""
    post = get_object_or_404(Post, id=post_id)
    saved_item, created = SavedPost.objects.get_or_create(user=request.user, post=post)

    if not created:
        saved_item.delete()
        saved = False
    else:
        saved = True

    return JsonResponse({'saved': saved})


@login_required
@require_POST
def follow_user_ajax(request, user_id):
    """AJAX endpoint to follow/unfollow a user."""
    target_user = get_object_or_404(User.objects.select_related('profile'), id=user_id)

    if target_user == request.user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

    if not created:
        follow.delete()
        following = False
    else:
        following = True
        create_notification(sender=request.user, receiver=target_user, notification_type='follow')

    return JsonResponse({
        'following': following,
        'followers_count': target_user.profile.followers_count
    })


@login_required
@require_POST
def add_comment_ajax(request, post_id):
    """AJAX endpoint to add a comment to a post."""
    post = get_object_or_404(Post, id=post_id)
    comment_text = request.POST.get('comment', '').strip()

    if not comment_text:
        return JsonResponse({'error': 'Comment content cannot be empty.'}, status=400)

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        comment=comment_text
    )

    create_notification(sender=request.user, receiver=post.author, notification_type='comment', post=post)

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author_username': comment.author.username,
            'author_avatar': comment.author.profile.avatar_url,
            'author_profile_url': f"/profile/{comment.author.username}/",
            'text': comment.comment,
            'created_at': 'Just now'
        },
        'comments_count': post.comments_count
    })


# Custom Error Handlers
def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
