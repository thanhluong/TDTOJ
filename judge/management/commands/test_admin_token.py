from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

class Command(BaseCommand):
    help = 'Test admin token authentication system'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to test admin access')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            
            # Kiểm tra user có quyền admin không
            if not (user.is_staff or user.is_superuser):
                self.stdout.write(
                    self.style.ERROR(f'User {username} is not staff or superuser')
                )
                self.stdout.write('To make user admin, run:')
                self.stdout.write(f'python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username=\'{username}\'); u.is_staff=True; u.save()"')
                return
            
            # Lấy access token
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
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ User {username} has admin privileges and valid token')
            )
            
            # Hiển thị các admin URLs
            base_url = 'http://127.0.0.1:8000'  # Có thể thay đổi theo môi trường
            
            admin_urls = {
                'Get Admin URLs': f'{base_url}/api/tdtu/admin-access/?tokenid={access_token}',
                'Admin Home': f'{base_url}/admin/?tokenid={access_token}',
                'Organizations': f'{base_url}/admin/judge/organization/?tokenid={access_token}',
                'Contests': f'{base_url}/admin/judge/contest/?tokenid={access_token}',
                'Problems': f'{base_url}/admin/judge/problem/?tokenid={access_token}',
                'Users': f'{base_url}/admin/auth/user/?tokenid={access_token}',
                'Profiles': f'{base_url}/admin/judge/profile/?tokenid={access_token}',
            }
            
            self.stdout.write('\n📋 Admin Access URLs:')
            self.stdout.write('=' * 50)
            
            for name, url in admin_urls.items():
                self.stdout.write(f'{name}:')
                self.stdout.write(f'  {url}')
                self.stdout.write('')
            
            self.stdout.write('🔧 How it works:')
            self.stdout.write('1. Click any admin URL above')
            self.stdout.write('2. The tokenid parameter will automatically log you in')
            self.stdout.write('3. You will be redirected to the clean admin URL')
            self.stdout.write('4. You can then navigate normally in Django admin')
            
            self.stdout.write('\n📝 Note:')
            self.stdout.write('- Only works for staff/superuser accounts')
            self.stdout.write('- Token is automatically removed from URL after login')
            self.stdout.write('- Session will persist until logout or expiry')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
