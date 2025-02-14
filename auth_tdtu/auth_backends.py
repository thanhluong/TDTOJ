from social_core.backends.oauth import BaseOAuth2
from urllib.parse import unquote, urlencode, urlparse, parse_qs
import base64
import requests
from social_core.exceptions import AuthException
import json

class TDTOAuth2(BaseOAuth2):
    """Custom OAuth2 authentication backend for TDT"""
    name = 'tdt'
    AUTHORIZATION_URL = 'https://ojtdtu.duthu.net/oauth2/v1/authorize'
    ACCESS_TOKEN_URL = 'https://ojtdtu.duthu.net/oauth2/v1/token'
    DEFAULT_SCOPE = ['email', 'profile', 'openid']  # Nếu có scope khác, hãy thêm vào đây.
    def get_redirect_uri(self, state=None):
        """Ghi đè để loại bỏ `redirect_state` và ngăn double encoding"""
        redirect_uri = super().get_redirect_uri(state)  # Lấy redirect_uri gốc
        parsed_url = urlparse(unquote(redirect_uri))  # Giải mã URL nếu đã bị encode
        query_params = parse_qs(parsed_url.query)

        # Xóa `redirect_state` nếu có
        query_params.pop('redirect_state', None)

        # Tạo lại URL không có `redirect_state`
        new_query = urlencode(query_params, doseq=True)
        
        print(parsed_url.path)
        if parsed_url.path.endswith('/'):
            clean_redirect_uri = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path[:-1]}"
        else:
            clean_redirect_uri = redirect_uri  # Nếu không bị lỗi, giữ nguyên
        print(clean_redirect_uri)
        return clean_redirect_uri  

    def get_user_details(self, response):
        json_string = json.dumps(response, indent=4, ensure_ascii=False)
        print('RESSSSSSSSSSSSSSSSS',json_string)
        return {
            'name': response.get('username'),
            'uid': response.get('uid'),
            'email': response.get('email'),
            'username': response.get('username'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
        }
    def get_user_id(self, details, response):
        return response.get('uid')



    def auth_complete(self, *args, **kwargs):
        """
        Ghi đè auth_complete để gộp bước lấy Access Token và lấy thông tin user thành một bước.
        """
        # B1: Lấy code từ query string (callback URI)
        print("Start call API")
        code = self.strategy.request_data().get('code')
        if not code:
            raise AuthException(self, 'Missing authorization code.')

        # B2: Lấy client_id và client_secret từ settings
        client_id = self.setting('SOCIAL_AUTH_TDT_KEY')         # Tương ứng với SOCIAL_AUTH_EXAMPLEAPI_KEY
        client_secret = self.setting('SOCIAL_AUTH_TDT_SECRET')    # Tương ứng với SOCIAL_AUTH_EXAMPLEAPI_SECRET

        # Tạo Basic Auth code: base64("CLIENT_ID:CLIENT_SECRET")
        basic_auth_str = f"{client_id}:{client_secret}"
        basic_auth_code = base64.b64encode(basic_auth_str.encode('utf-8')).decode('utf-8')
        print(basic_auth_code)
        # Chuẩn bị header cho request
        headers = {
            'Authorization': f'Basic {basic_auth_code}',
            'Content-Type': 'application/json'
        }
        
        # B3: Lấy redirect_uri từ settings (cần phải khớp với những gì đã đăng ký với provider)
        redirect_uri = self.setting('SOCIAL_AUTH_TDT_REDIRECT_URI')  # Tương ứng với SOCIAL_AUTH_EXAMPLEAPI_REDIRECT_URI
        
        # B4: Tạo payload cho POST request
        payload = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        # B5: Gửi POST request đến token endpoint
        response = requests.post(self.ACCESS_TOKEN_URL, json=payload, headers=headers)
        if response.status_code != 200:
            try:
                error_message = response.json().get('message', 'Unknown error')
            except Exception:
                error_message = response.text or 'Unknown error'
            raise AuthException(self, f"Error POST: {error_message}")
        
        # B6: Nếu thành công, lấy dữ liệu JSON trả về
        token_data = response.json()
        
        # Kiểm tra các trường bắt buộc có tồn tại không (ví dụ: uid và access_token)
        if not token_data.get('uid') or not token_data.get('access_token'):
            raise AuthException(self, 'Invalid token data received.')
        
        # B7: Gán dữ liệu nhận được vào self.data để pipeline sử dụng.

        self.process_error(token_data)
        self.data.update(token_data)
        
        return self.do_auth(self.data.get('access_token'), response=self.data, *args, **kwargs)

