from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from social_django.models import UserSocialAuth
import logging

logger = logging.getLogger(__name__)

class AdminTokenAuthMiddleware:
    """
    Middleware để tự động đăng nhập user khi truy cập admin với tokenid
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Chỉ xử lý cho các trang admin
        if request.path.startswith('/admin/'):
            # Lấy tokenid từ query parameters
            token = request.GET.get('tokenid')
            
            # Nếu có token và user chưa đăng nhập
            if token and not request.user.is_authenticated:
                user = self.verify_and_login_user(request, token)
                if user:
                    logger.info(f"Auto-logged in user {user.username} for admin access")
                    
                    # Redirect để loại bỏ tokenid khỏi URL
                    clean_url = request.path
                    if request.GET:
                        # Giữ lại các query parameters khác, loại bỏ tokenid
                        params = request.GET.copy()
                        params.pop('tokenid', None)
                        if params:
                            clean_url += '?' + params.urlencode()
                    
                    return HttpResponseRedirect(clean_url)
        
        response = self.get_response(request)
        return response

    def verify_and_login_user(self, request, token):
        """
        Verify token và tự động đăng nhập user
        """
        try:
            # Tìm user có access_token khớp với token
            social_auths = UserSocialAuth.objects.filter(provider='tdt').select_related('user')
            
            for social_auth in social_auths:
                stored_token = social_auth.extra_data.get('access_token')
                if stored_token and stored_token == token:
                    user = social_auth.user
                    
                    # Kiểm tra user có quyền truy cập admin không
                    if user.is_staff or user.is_superuser:
                        # Đăng nhập user
                        login(request, user)
                        
                        # Set profile nếu có
                        try:
                            request.profile = user.profile
                        except:
                            request.profile = None
                        
                        logger.info(f"Successfully authenticated admin user: {user.username}")
                        return user
                    else:
                        logger.warning(f"User {user.username} is not staff/admin")
                        return None
            
            logger.warning(f"No matching token found for admin access: {token[:10]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying admin token: {e}")
            return None
