from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser


ADMINISTRATORS = (
    ('Lincoln1234', 'Ignatius12345'),
    ('Menny-wizzy1', 'menny1234'),
)


class Command(BaseCommand):
    help = 'Create the two permanent CEWMS system administrator accounts if absent.'

    def handle(self, *args, **options):
        for username, password in ADMINISTRATORS:
            user = CustomUser.objects.filter(username=username).first()
            if user is None:
                CustomUser.objects.create_user(
                    username=username,
                    password=password,
                    user_type='SYSTEM_ADMIN',
                )
                self.stdout.write(self.style.SUCCESS(f'{username}: created as SYSTEM_ADMIN.'))
            elif user.user_type != 'SYSTEM_ADMIN':
                self.stdout.write(self.style.WARNING(
                    f'{username}: already exists with role {user.user_type}; no changes made. '
                    'Review the account and set its role to SYSTEM_ADMIN explicitly if appropriate.'
                ))
            else:
                self.stdout.write(f'{username}: already exists as SYSTEM_ADMIN; no changes made.')
