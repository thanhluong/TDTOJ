#!/usr/bin/env python3
"""
Script để test admin token authentication

Usage:
    python test_admin_flow.py username
"""

import sys
import os
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmoj.settings')
django.setup()

from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

def test_admin_flow(username):
    print(f"🔍 Testing admin token authentication for: {username}")
    print("=" * 60)
    
    try:
        # 1. Kiểm tra user tồn tại
        user = User.objects.get(username=username)
        print(f"✓ User found: {user.username}")
        
        # 2. Kiểm tra quyền admin
        if not (user.is_staff or user.is_superuser):
            print(f"❌ User {username} is not staff/admin")
            print(f"💡 Run: python manage.py make_staff {username}")
            return False
        
        print(f"✓ Admin privileges: staff={user.is_staff}, superuser={user.is_superuser}")
        
        # 3. Kiểm tra access token
        social_auth = UserSocialAuth.objects.filter(user=user, provider='tdt').first()
        if not social_auth or not social_auth.extra_data.get('access_token'):
            print(f"❌ No TDT access token found for {username}")
            print("💡 User needs to login via TDT OAuth first")
            return False
        
        access_token = social_auth.extra_data['access_token']
        print(f"✓ Access token found: {access_token[:20]}...")
        
        # 4. Tạo test URLs
        base_url = 'http://127.0.0.1:8000'
        
        print(f"\n🎯 Test URLs:")
        print(f"Admin Access API: {base_url}/api/tdtu/admin-access/?tokenid={access_token}")
        print(f"Direct Admin: {base_url}/admin/?tokenid={access_token}")
        
        print(f"\n🔧 How to test:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Open any of the URLs above in browser")
        print("3. Should automatically log you in and redirect to clean admin URL")
        
        return True
        
    except User.DoesNotExist:
        print(f"❌ User {username} does not exist")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_admin_flow.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    success = test_admin_flow(username)
    
    if success:
        print(f"\n🎉 Admin token authentication is ready for {username}!")
    else:
        print(f"\n💔 Setup incomplete for {username}")
        sys.exit(1)
