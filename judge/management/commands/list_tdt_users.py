from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
import json

class Command(BaseCommand):
    help = 'List all users with TDT OAuth tokens'

    def add_arguments(self, parser):
        parser.add_argument('--show-tokens', action='store_true', help='Show actual tokens (truncated)')

    def handle(self, *args, **options):
        show_tokens = options.get('show_tokens', False)
        
        # Lấy tất cả TDT social auth
        tdt_users = UserSocialAuth.objects.filter(provider='tdt').select_related('user')
        
        if not tdt_users.exists():
            self.stdout.write(self.style.WARNING('No TDT OAuth users found'))
            return
        
        self.stdout.write(f'Found {tdt_users.count()} TDT OAuth users:')
        self.stdout.write('-' * 50)
        
        for social in tdt_users:
            user = social.user
            self.stdout.write(f'User: {user.username} (ID: {user.id})')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'UID: {social.extra_data.get("uid", "N/A")}')
            
            # Kiểm tra access_token
            access_token = social.extra_data.get('access_token')
            if access_token:
                if show_tokens:
                    self.stdout.write(f'Access Token: {access_token[:20]}...')
                else:
                    self.stdout.write(self.style.SUCCESS('✓ Has access token'))
                    
                # Tạo test URL
                test_url = f'/api/tdtu/test-token/?tokenid={access_token}'
                self.stdout.write(f'Test URL: {test_url}')
            else:
                self.stdout.write(self.style.ERROR('✗ No access token'))
            
            # Kiểm tra các trường khác
            refresh_token = social.extra_data.get('refresh_token')
            if refresh_token:
                self.stdout.write('✓ Has refresh token')
            
            expires_in = social.extra_data.get('expires_in')
            if expires_in:
                self.stdout.write(f'Expires in: {expires_in} seconds')
            
            self.stdout.write('-' * 30)
        
        # Hướng dẫn sử dụng
        self.stdout.write(self.style.SUCCESS('\nUsage examples:'))
        self.stdout.write('GET /api/tdtu/test-token/?tokenid=YOUR_TOKEN')
        self.stdout.write('GET /api/tdtu/organizations/?tokenid=YOUR_TOKEN')
        self.stdout.write('POST /api/tdtu/organizations/?tokenid=YOUR_TOKEN')
