from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            phone='09031185402',
            defaults={'full_name': 'Roxxie Wilcox'},
        )
        user.full_name = 'Roxxie Wilcox'
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password('RoxXie@1')
        user.save()
        self.stdout.write('Superuser created.' if created else 'Superuser updated.')