# myproject/pipeline.py

from judge.models import Profile, Language

def create_profile(backend, user, response, *args, **kwargs):
    """
    Pipeline function: Tạo hoặc cập nhật Profile cho người dùng nếu chưa có.
    Có thể sử dụng dữ liệu từ `response` nếu cần cập nhật thêm thông tin.
    """
    # Nếu Profile đã tồn tại, không cần tạo mới
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        # Sử dụng giá trị mặc định cho language, timezone, v.v...
        profile = Profile.objects.create(
            user=user,
            language=Language.get_default_language(),  # hoặc lấy từ settings của bạn
            # Có thể thêm các trường khác nếu response chứa dữ liệu cần thiết
        )
    # Nếu bạn muốn cập nhật thêm thông tin từ response, thực hiện ở đây
    # Ví dụ: profile.timezone = response.get('timezone', profile.timezone)
    profile.save()
    return {'profile': profile}
