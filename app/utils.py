from app.models import Notification

def create_notification(sender, receiver, notification_type, post=None):
    """
    Creates a notification if sender != receiver.
    Prevents generating spam notifications to oneself.
    """
    if sender != receiver:
        # Avoid duplicated unread notification for the same action
        existing = Notification.objects.filter(
            sender=sender,
            receiver=receiver,
            notification_type=notification_type,
            post=post,
            is_read=False
        ).first()

        if not existing:
            Notification.objects.create(
                sender=sender,
                receiver=receiver,
                notification_type=notification_type,
                post=post
            )
