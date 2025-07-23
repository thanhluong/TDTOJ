from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

class Command(BaseCommand):
    help = 'Get access token for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to get token for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            social_auth = UserSocialAuth.objects.filter(
                user=user, 
                provider='tdt'
            ).first()
            
            if social_auth and social_auth.extra_data.get('access_token'):
                access_token = social_auth.extra_data['access_token']
                self.stdout.write(
                    self.style.SUCCESS(f'Access token for {username}: {access_token}')
                )
                self.stdout.write(f'Test URL: /api/tdtu/test-token/?tokenid={access_token}')
                self.stdout.write(f'Organization API URL: /api/tdtu/organizations/?tokenid={access_token}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'No access token found for user {username}')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
