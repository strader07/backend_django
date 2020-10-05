from users.models import Profile


def get_user_data(user):
    try:
        profile = Profile.objects.get(owner=user)
        return {
            'username': user.username,
            'push_notification': profile.push_notification,
            'telegram_notification': profile.telegram_notification,
            'email_notification': profile.email_notification,
            'notification_message': profile.notification_message
        }
    except Exception as e:
        print(e)
        return {
            'username': user.username,
            'push_notification': False,
            'telegram_notification': False,
            'email_notification': False,
            'notification_message': ''
        }
