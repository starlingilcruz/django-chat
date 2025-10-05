"""
Management command to create initial superuser
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create initial superuser if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()
        email = "root@openchat.com"
        password = "Root@123456"

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Superuser {email} already exists. Skipping."))
        else:
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} created successfully!"))
