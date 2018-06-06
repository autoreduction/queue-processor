from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates a super user in the database'

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        User.objects.filter(username='super').delete()
        User.objects.create_superuser('super', '', 'super')
