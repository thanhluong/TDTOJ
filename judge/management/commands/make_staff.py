from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Make a user staff/admin'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to make staff')
        parser.add_argument('--superuser', action='store_true', help='Also make superuser')
        parser.add_argument('--remove', action='store_true', help='Remove staff privileges')

    def handle(self, *args, **options):
        username = options['username']
        make_superuser = options.get('superuser', False)
        remove_privileges = options.get('remove', False)
        
        try:
            user = User.objects.get(username=username)
            
            if remove_privileges:
                user.is_staff = False
                user.is_superuser = False
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Removed admin privileges from {username}')
                )
            else:
                user.is_staff = True
                if make_superuser:
                    user.is_superuser = True
                user.save()
                
                privileges = 'staff'
                if make_superuser:
                    privileges += ' and superuser'
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Made {username} {privileges}')
                )
            
            # Hiển thị trạng thái hiện tại
            self.stdout.write(f'\nCurrent status for {username}:')
            self.stdout.write(f'  Staff: {user.is_staff}')
            self.stdout.write(f'  Superuser: {user.is_superuser}')
            self.stdout.write(f'  Active: {user.is_active}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
