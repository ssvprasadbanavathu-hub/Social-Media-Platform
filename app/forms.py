import os
from django import forms
from django.contrib.auth.models import User
from app.models import UserProfile, Post, Comment


def validate_image_file(image):
    """Validate uploaded image file size and extension."""
    if image:
        # 5MB size limit
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image file size must be 5MB or smaller.")
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in valid_extensions:
            raise forms.ValidationError("Unsupported image format. Allowed formats: JPG, JPEG, PNG, GIF, WEBP.")
    return image


class UserRegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email address cannot be empty.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        full_name = self.cleaned_data.get('full_name', '').strip()
        names = full_name.split(' ', 1)
        user.first_name = names[0]
        if len(names) > 1:
            user.last_name = names[1]
            
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        existing = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell the world about yourself...'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (e.g. San Francisco, CA)'})
    )
    website = forms.URLField(
        max_length=200,
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Website (e.g. https://yourwebsite.com)'})
    )
    profile_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'profile_image_input', 'accept': 'image/*'})
    )
    cover_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'cover_image_input', 'accept': 'image/*'})
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'website', 'profile_image', 'cover_image']

    def clean_profile_image(self):
        return validate_image_file(self.cleaned_data.get('profile_image'))

    def clean_cover_image(self):
        return validate_image_file(self.cleaned_data.get('cover_image'))


class PostForm(forms.ModelForm):
    caption = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control border-0 bg-transparent shadow-none',
            'rows': 3,
            'placeholder': "What's on your mind?"
        })
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'd-none',
            'id': 'post-image-input',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Post
        fields = ['caption', 'image']

    def clean_image(self):
        return validate_image_file(self.cleaned_data.get('image'))


class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill pe-5',
            'placeholder': 'Write a comment...'
        })
    )

    class Meta:
        model = Comment
        fields = ['comment']
