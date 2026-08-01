/**
 * MyFriend Main JavaScript Interactive Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initLikeToggle();
    initSaveToggle();
    initFollowToggle();
    initCommentAjax();
    initNotifications();
    initImagePreviews();
});

/**
 * Get Django CSRF Cookie Value
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Dark Mode Theme Initialization & Persistence
 */
function initDarkMode() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement;

    const savedTheme = localStorage.getItem('myfriend-theme') || 'light';
    htmlElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('myfriend-theme', newTheme);
            updateThemeIcon(newTheme);
            showToast(`Switched to ${newTheme} mode`, 'info');
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-toggle-icon');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'fas fa-sun text-warning';
        } else {
            icon.className = 'fas fa-moon text-secondary';
        }
    }
}

/**
 * Like / Unlike Post AJAX Handler
 */
function initLikeToggle() {
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-like-trigger');
        if (!btn) return;

        e.preventDefault();
        const postId = btn.dataset.postId;
        const icon = btn.querySelector('.like-icon');
        const countSpan = btn.querySelector('.like-count');

        try {
            const response = await fetch(`/ajax/like/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.liked) {
                    btn.classList.add('liked');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                } else {
                    btn.classList.remove('liked');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
                if (countSpan) {
                    countSpan.textContent = data.likes_count;
                }
            } else if (response.status === 403 || response.status === 401) {
                window.location.href = '/login/';
            }
        } catch (error) {
            console.error('Error liking post:', error);
            showToast('Unable to process request.', 'danger');
        }
    });
}

/**
 * Save / Bookmark Post AJAX Handler
 */
function initSaveToggle() {
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-save-trigger');
        if (!btn) return;

        e.preventDefault();
        const postId = btn.dataset.postId;
        const icon = btn.querySelector('.save-icon');

        try {
            const response = await fetch(`/ajax/save/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.saved) {
                    btn.classList.add('saved');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    showToast('Post saved to your bookmarks', 'success');
                } else {
                    btn.classList.remove('saved');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    showToast('Post removed from bookmarks', 'info');
                }
            }
        } catch (error) {
            console.error('Error saving post:', error);
        }
    });
}

/**
 * Follow / Unfollow User AJAX Handler
 */
function initFollowToggle() {
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-follow-trigger');
        if (!btn) return;

        e.preventDefault();
        const userId = btn.dataset.userId;

        try {
            const response = await fetch(`/ajax/follow/${userId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.following) {
                    btn.classList.remove('btn-outline-primary', 'btn-accent');
                    btn.classList.add('btn-secondary');
                    btn.innerHTML = '<i class="fas fa-user-check me-1"></i> Following';
                } else {
                    btn.classList.remove('btn-secondary');
                    btn.classList.add('btn-accent');
                    btn.innerHTML = '<i class="fas fa-user-plus me-1"></i> Follow';
                }

                const followersCountElem = document.getElementById(`followers-count-${userId}`);
                if (followersCountElem) {
                    followersCountElem.textContent = data.followers_count;
                }
            }
        } catch (error) {
            console.error('Error toggling follow:', error);
        }
    });
}

/**
 * AJAX Comment Submission
 */
function initCommentForm(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const postId = form.dataset.postId;
        const input = form.querySelector('input[name="comment"]');
        const commentText = input.value.trim();

        if (!commentText) return;

        const formData = new FormData();
        formData.append('comment', commentText);

        try {
            const response = await fetch(`/ajax/comment/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    input.value = '';
                    
                    const list = document.getElementById(`comments-list-${postId}`);
                    if (list) {
                        const newCommentHtml = `
                            <div class="d-flex gap-2 mb-2 align-items-start animate__animated animate__fadeIn">
                                <img src="${data.comment.author_avatar}" class="avatar-sm" alt="Avatar">
                                <div class="bg-body-secondary p-2 px-3 rounded-4 w-100 position-relative">
                                    <div class="fw-semibold text-dark text-decoration-none">
                                        <a href="${data.comment.author_profile_url}" class="text-decoration-none text-reset">${data.comment.author_username}</a>
                                    </div>
                                    <p class="mb-0 text-break small">${escapeHtml(data.comment.text)}</p>
                                    <span class="text-muted text-xs ms-1">${data.comment.created_at}</span>
                                </div>
                            </div>
                        `;
                        list.insertAdjacentHTML('afterbegin', newCommentHtml);
                    }

                    const countSpan = document.getElementById(`comments-count-${postId}`);
                    if (countSpan) {
                        countSpan.textContent = data.comments_count;
                    }
                }
            }
        } catch (error) {
            console.error('Error posting comment:', error);
        }
    });
}

function initCommentAjax() {
    document.querySelectorAll('.comment-form-ajax').forEach(form => {
        initCommentForm(form);
    });
}

/**
 * Notifications Management
 */
function initNotifications() {
    const markReadBtn = document.getElementById('mark-notifications-read-btn');
    if (markReadBtn) {
        markReadBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/ajax/notifications/read/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (response.ok) {
                    document.querySelectorAll('.notification-item.unread').forEach(item => {
                        item.classList.remove('unread');
                    });
                    const badge = document.getElementById('notification-badge');
                    if (badge) badge.remove();
                    showToast('Notifications marked as read.', 'success');
                }
            } catch (error) {
                console.error('Error marking notifications as read:', error);
            }
        });
    }
}

/**
 * Image Upload Live Preview Handler
 */
function initImagePreviews() {
    const postImageInput = document.getElementById('post-image-input');
    const postImagePreview = document.getElementById('post-image-preview');
    const postImagePreviewImg = document.getElementById('post-image-preview-img');
    const removeImageBtn = document.getElementById('remove-post-image');

    if (postImageInput && postImagePreviewImg) {
        postImageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    postImagePreviewImg.src = event.target.result;
                    postImagePreview.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            }
        });

        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', () => {
                postImageInput.value = '';
                postImagePreviewImg.src = '';
                postImagePreview.classList.add('d-none');
            });
        }
    }
}

/**
 * Toast Notification Helper
 */
function showToast(message, type = 'primary') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0 shadow mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastElem = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastElem, { delay: 3500 });
    bsToast.show();

    toastElem.addEventListener('hidden.bs.toast', () => {
        toastElem.remove();
    });
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
