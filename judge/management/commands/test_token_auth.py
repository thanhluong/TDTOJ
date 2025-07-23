from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
import requests
import json

class Command(BaseCommand):
    help = 'Test token authentication system'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to test with')
        parser.add_argument('--base-url', type=str, default='http://127.0.0.1:8000', help='Base URL for testing')

    def handle(self, *args, **options):
        username = options['username']
        base_url = options['base_url']
        
        try:
            # Lấy access token
            user = User.objects.get(username=username)
            social_auth = UserSocialAuth.objects.filter(
                user=user, 
                provider='tdt'
            ).first()
            
            if not social_auth or not social_auth.extra_data.get('access_token'):
                self.stdout.write(
                    self.style.ERROR(f'No access token found for user {username}')
                )
                return
            
            access_token = social_auth.extra_data['access_token']
            self.stdout.write(f'Testing with token: {access_token[:20]}...')
            
            # Test endpoints
            endpoints = [
                {
                    'name': 'Token Test',
                    'url': f'{base_url}/api/tdtu/test-token/?tokenid={access_token}',
                    'method': 'GET'
                },
                {
                    'name': 'Organizations List', 
                    'url': f'{base_url}/api/tdtu/organizations/?tokenid={access_token}',
                    'method': 'GET'
                },
                {
                    'name': 'Create Organization',
                    'url': f'{base_url}/api/tdtu/organizations/?tokenid={access_token}',
                    'method': 'POST',
                    'data': {
                        'name': 'Test Organization from API',
                        'slug': 'test-org-api',
                        'short_name': 'TestOrgAPI'
                    }
                }
            ]
            
            for endpoint in endpoints:
                self.stdout.write(f"\n--- Testing {endpoint['name']} ---")
                self.stdout.write(f"URL: {endpoint['url']}")
                
                try:
                    if endpoint['method'] == 'GET':
                        response = requests.get(endpoint['url'])
                    elif endpoint['method'] == 'POST':
                        response = requests.post(
                            endpoint['url'], 
                            json=endpoint.get('data', {}),
                            headers={'Content-Type': 'application/json'}
                        )
                    
                    self.stdout.write(f"Status: {response.status_code}")
                    
                    if response.status_code == 200 or response.status_code == 201:
                        result = response.json()
                        
                        # Hiển thị thông tin user đã đăng nhập
                        if 'authenticated_user' in result:
                            auth_user = result['authenticated_user']
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ Authenticated as: {auth_user}")
                            )
                        
                        # Hiển thị message nếu có
                        if 'message' in result:
                            self.stdout.write(f"Message: {result['message']}")
                        
                        # Hiển thị organization info nếu có
                        if 'name' in result and 'id' in result:
                            self.stdout.write(f"Organization: {result['name']} (ID: {result['id']})")
                        
                    else:
                        error_msg = response.text
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', error_msg)
                        except:
                            pass
                        self.stdout.write(
                            self.style.ERROR(f"✗ Error: {error_msg}")
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Request failed: {e}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Testing completed for user {username}')
            )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
