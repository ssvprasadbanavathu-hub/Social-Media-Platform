from django.urls import path
from django.contrib.auth import views as auth_views
from app import views

urlpatterns = [
    # Pages
    path('', views.home_view, name='home'),
    path('landing/', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Profile & Settings
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/followers/', views.followers_view, name='followers'),
    path('profile/<str:username>/following/', views.following_view, name='following'),
    path('settings/', views.settings_view, name='settings'),

    # Posts & Comments
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),

    # Features
    path('search/', views.search_view, name='search'),
    path('notifications/', views.notifications_view, name='notifications'),

    # AJAX API Endpoints
    path('ajax/like/<int:post_id>/', views.like_post_ajax, name='like_post_ajax'),
    path('ajax/save/<int:post_id>/', views.save_post_ajax, name='save_post_ajax'),
    path('ajax/follow/<int:user_id>/', views.follow_user_ajax, name='follow_user_ajax'),
    path('ajax/comment/<int:post_id>/', views.add_comment_ajax, name='add_comment_ajax'),
    path('ajax/notifications/read/', views.mark_notifications_read_ajax, name='mark_notifications_read_ajax'),
]
