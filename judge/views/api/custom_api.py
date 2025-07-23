import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Sum, Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
import datetime
import random
import string
from judge.models import Organization, Contest, Profile, ContestParticipation, ContestSubmission, Problem, Submission
from social_django.models import UserSocialAuth

def generate_random_key(length=16):
    allowed_chars = string.ascii_lowercase + string.digits + '_'
    return ''.join(random.choices(allowed_chars, k=length))


def verify_token(token):
    """
    Placeholder for token verification.
    In the future, this will call side A's API to verify the token.
    """
    # Mock implementation - always return success with dummy user data
    """
    Kiểm tra token có tồn tại trong database không và trả về user data
    """
    if not token:
        return False, None
    
    try:
        # Tìm user có access_token khớp với token được cung cấp
        social_auth = UserSocialAuth.objects.filter(
            provider='tdt',
            extra_data__access_token=token
        ).select_related('user').first()
        
        if not social_auth:
            return False, None
        
        # Trả về thông tin user
        user = social_auth.user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'uid': social_auth.extra_data.get('uid'),
            'social_auth_id': social_auth.id
        }
        
        return True, user_data
        
    except Exception as e:
        print(f"Error verifying token: {e}")
        return False, None


def token_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Lấy token từ URL parameter 'tokenid'
        token = request.GET.get('tokenid')
        
        if not token:
            return JsonResponse({'error': 'Token is required in URL parameter "tokenid"'}, status=401)
        
        is_valid, user_data = verify_token(token)
        
        if not is_valid:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Attach user data to request
        request.user_data = user_data
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


class OrganizationAPIView(View):
    def get(self, request):
        organizations = Organization.objects.all()
        
        # Filtering
        name = request.GET.get('name')
        if name:
            organizations = organizations.filter(name__icontains=name)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start = (page - 1) * page_size
        end = page * page_size
        
        total_count = organizations.count()
        organizations = organizations[start:end]
        
        result = {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': [
                {
                    'id': org.id,
                    'name': org.name,
                    'slug': org.slug,
                    'short_name': org.short_name,
                    'about': org.about,
                    'is_open': org.is_open,
                    'member_count': org.members.count(),
                }
                for org in organizations
            ]
        }
        
        return JsonResponse(result)
    
    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'slug', 'short_name']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Create organization
            organization = Organization(
                name=data['name'],
                slug=data['slug'],
                short_name=data['short_name'],
                about=data.get('about', ''),
                is_open=data.get('is_open', False),
            )
            organization.save()
            
            # Add current user as admin
            organization.admins.add(request.profile)
            
            return JsonResponse({
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
                'short_name': organization.short_name,
                'about': organization.about,
                'is_open': organization.is_open,
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class OrganizationContestsAPIView(View):
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        
        contests = Contest.objects.filter(organizations=organization)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start = (page - 1) * page_size
        end = page * page_size
        
        total_count = contests.count()
        contests = contests[start:end]
        
        result = {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
            },
            'results': [
                {
                    'id': contest.id,
                    'key': contest.key,
                    'name': contest.name,
                    'start_time': contest.start_time.isoformat(),
                    'end_time': contest.end_time.isoformat(),
                    'time_limit': contest.time_limit.total_seconds() if contest.time_limit else None,
                    'is_rated': contest.is_rated,
                    'is_private': contest.is_private,
                }
                for contest in contests
            ]
        }
        
        return JsonResponse(result)


class ContestScoreboardAPIView(View):
    def get(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        
        # Check permission
        if not contest.is_accessible_by(request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get all users and their submissions for this contest
        participations = ContestParticipation.objects.filter(
            contest=contest,
            virtual=0,
        ).select_related('user')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))
        start = (page - 1) * page_size
        end = page * page_size
        
        total_count = participations.count()
        
        # Get contest problems
        problems = list(contest.contest_problems.order_by('order')
                        .select_related('problem')
                        .only('id', 'problem__name', 'problem__code', 'points'))
        
        # Calculate scores
        scoreboard = []
        for participation in participations:
            # Get best submission for each problem
            problem_scores = {}
            cumulative_time = 0
            total_score = 0
            
            submissions = ContestSubmission.objects.filter(
                participation=participation
            ).values('problem_id').annotate(
                score=Max('points')
            )
            
            for submission in submissions:
                problem_id = submission['problem_id']
                problem_scores[problem_id] = submission['score']
                total_score += submission['score']
            
            # Add to scoreboard
            scoreboard.append({
                'user': {
                    'id': participation.user.id,
                    'username': participation.user.user.username,
                    'points': participation.user.points,
                    'rating': participation.user.rating,
                },
                'score': total_score,
                'problem_scores': problem_scores,
                'cumulative_time': cumulative_time,
            })
        
        # Sort by score (descending)
        scoreboard.sort(key=lambda x: x['score'], reverse=True)
        scoreboard = scoreboard[start:end]
        
        result = {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'contest': {
                'id': contest.id,
                'key': contest.key,
                'name': contest.name,
            },
            'problems': [
                {
                    'id': problem.id,
                    'name': problem.problem.name,
                    'code': problem.problem.code,
                    'points': problem.points,
                }
                for problem in problems
            ],
            'results': scoreboard
        }
        
        return JsonResponse(result)


class OrganizationUsersAPIView(View):
    def get(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        
        users = organization.members.all()
        
        # Sorting
        sort_by = request.GET.get('sort', '-rating')
        if sort_by.startswith('-'):
            users = users.order_by(sort_by)
        else:
            users = users.order_by(sort_by)
            
        # Select related user to avoid N+1 queries
        users = users.select_related('user')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start = (page - 1) * page_size
        end = page * page_size
        
        total_count = users.count()
        users = users[start:end]
        
        result = {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
            },
            'results': [
                {
                    'id': user.id,
                    'username': user.user.username,
                    'points': user.points,
                    'performance_points': user.performance_points,
                    'problem_count': user.problem_count,
                    'display_rank': user.display_rank,
                    'rating': user.rating,
                }
                for user in users
            ]
        }
        
        return JsonResponse(result)

@method_decorator(csrf_exempt, name='dispatch')
class TDTUOrganizationAPIView(View):
    @method_decorator(token_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'slug', 'short_name']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'error': f'Missing required field: {field}'
                    }, status=400)

            existing_organization = Organization.objects.filter(slug=data['slug']).first()
            if existing_organization:
                # Nếu tổ chức đã tồn tại, trả về redirect link cho contest
                redirect_link = request.build_absolute_uri(
                    reverse('admin:judge_contest_add')
                )
                return JsonResponse({
                    'message': 'Organization already exists',
                    'id': existing_organization.id,
                    'name': existing_organization.name,
                    'slug': existing_organization.slug,
                    'short_name': existing_organization.short_name,
                    'redirect_link': redirect_link
                }, status=200)
                
            # Create organization
            organization = Organization(
                name=data['name'],
                slug=data['slug'],
                short_name=data['short_name'],
                about=data.get('about', ''),
                is_open=data.get('is_open', False),
            )
            organization.save()
            
            # Get the requesting user or create if not exists
            try:
                profile = Profile.objects.get(user__username=request.user_data['username'])
            except Profile.DoesNotExist:
                # In a real implementation, we would create a new user here
                # For now, just return an error
                return JsonResponse({'error': 'User not found'}, status=404)
            
            # Add user as admin
            organization.admins.add(profile)
            
            # Add users to organization if provided
            if 'users' in data and isinstance(data['users'], list):
                for username in data['users']:
                    try:
                        user_profile = Profile.objects.get(user__username=username)
                        organization.members.add(user_profile)
                    except Profile.DoesNotExist:
                        # Skip users that don't exist, but log them
                        print(f"User {username} not found, skipping")
            
            # Generate redirect link for contest creation
            redirect_link = request.build_absolute_uri(
                reverse('admin:judge_contest_add')
            )
            
            return JsonResponse({
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
                'short_name': organization.short_name,
                'redirect_link': redirect_link,
                'authenticated_user': request.user_data['username']
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
    @method_decorator(token_required)
    def get(self, request):
        organizations = Organization.objects.all()
        
        # Filtering
        name = request.GET.get('name')
        if name:
            organizations = organizations.filter(name__icontains=name)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start = (page - 1) * page_size
        end = page * page_size
        
        total_count = organizations.count()
        organizations = organizations[start:end]
        
        result = {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': [
                {
                    'id': org.id,
                    'name': org.name,
                    'slug': org.slug,
                    'short_name': org.short_name,
                    'about': org.about,
                    'is_open': org.is_open,
                    'member_count': org.members.count(),
                }
                for org in organizations
            ]
        }
        
        return JsonResponse(result)

class TDTUOrganizationEditLinkView(View):
    @method_decorator(token_required)
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(Organization, id=org_id)
            
            # Generate edit link
            edit_path = f"/admin/judge/organization/{organization.id}/change/"
            edit_link = request.build_absolute_uri(edit_path)
            # edit_link = request.build_absolute_uri(
            #     reverse('organization_edit', args=[organization.id])
            # )
            
            return JsonResponse({
                'organization_id': organization.id,
                'edit_link': edit_link
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TDTUOrganizationDeleteView(View):
    
    def dispatch(self, request, *args, **kwargs):
        # Add CORS headers
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, '__setitem__'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'DELETE, OPTIONS, GET, POST'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    def options(self, request, org_id):
        """Handle preflight requests for DELETE method"""
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'DELETE, OPTIONS, GET, POST'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    @method_decorator(token_required)
    def delete(self, request, org_id):
        try:
            organization = get_object_or_404(Organization, id=org_id)
            
            # Store organization name for response
            org_name = organization.name
            
            # Delete organization
            organization.delete()
            
            return JsonResponse({
                'message': f'Organization {org_name} deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500) 
        

@method_decorator(csrf_exempt, name='dispatch')
class TDTUCreateContestView(View):
    @method_decorator(token_required)
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(Organization, id=org_id)

            data = json.loads(request.body)
            contest_name = data.get("name", "New Contest")
            is_private = data.get("is_private", True)

            contest = Contest.objects.create(
                name=contest_name,
                is_private=is_private,
                start_time=datetime.datetime.now(),
                end_time=datetime.datetime.now(),
                key=generate_random_key(),
            )
            contest.organizations.add(organization)

            # Trả về link tạo contest trong Django admin
            redirect_link = request.build_absolute_uri(
                reverse('admin:judge_contest_change', args=[contest.id])
            )

            return JsonResponse({
                'contest_id': contest.id,
                'contest_name': contest.name,
                'redirect_link': redirect_link
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class TDTUContestEditLinkView(View):
    @method_decorator(token_required)
    def get(self, request, org_id, contest_id):
        try:
            # Xác thực organization tồn tại
            organization = get_object_or_404(Organization, id=org_id)

            # Xác thực contest tồn tại
            contest = get_object_or_404(Contest, id=contest_id)

            # Kiểm tra contest có thuộc về organization không
            if not contest.organizations.filter(id=organization.id).exists():
                return JsonResponse({'error': 'Contest does not belong to this organization'}, status=403)

            # Tạo link chỉnh sửa contest trong admin
            edit_link = request.build_absolute_uri(
                reverse('admin:judge_contest_change', args=[contest.id])
            )

            return JsonResponse({
                'contest_id': contest.id,
                'organization_id': organization.id,
                'edit_link': edit_link
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TDTUContestDeleteView(View):
    
    def dispatch(self, request, *args, **kwargs):
        # Add CORS headers
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, '__setitem__'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'DELETE, OPTIONS, GET, POST'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    def options(self, request, org_id, contest_id):
        """Handle preflight requests for DELETE method"""
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'DELETE, OPTIONS, GET, POST'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    def get(self, request, org_id, contest_id):
        """Debug method to check if the view is accessible"""
        return JsonResponse({
            'message': 'Contest delete endpoint is accessible',
            'org_id': org_id,
            'contest_id': contest_id,
            'method': 'GET'
        })
    
    @method_decorator(token_required)
    def delete(self, request, *args, **kwargs):
        org_id = kwargs.get('org_id')
        contest_id = kwargs.get('contest_id')
        try:
            # Xác thực organization
            organization = get_object_or_404(Organization, id=org_id)

            # Xác thực contest
            contest = get_object_or_404(Contest, id=contest_id)

            # Kiểm tra contest có thuộc organization không
            if not contest.organizations.filter(id=organization.id).exists():
                return JsonResponse({
                    'error': 'Contest does not belong to this organization'
                }, status=403)

            contest_name = contest.name
            contest.delete()

            return JsonResponse({
                'message': f'Contest "{contest_name}" (ID: {contest_id}) deleted successfully.'
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class TDTUContestRankingView(View):
    @method_decorator(token_required)
    def get(self, request, contest_id):
        try:
            contest = get_object_or_404(Contest, id=contest_id)

            # Lấy tất cả user đã tham gia contest
            participations = ContestParticipation.objects.filter(
                contest=contest,
                virtual=0
            ).select_related('user')

            problems = list(contest.contest_problems.order_by('order')
                            .select_related('problem')
                            .only('id', 'problem__name', 'problem__code', 'points'))

            scoreboard = []
            for participation in participations:
                user = participation.user
                user_profile = {
                    'id': user.id,
                    'username': user.user.username,
                }

                # Tính điểm theo bài
                submissions = ContestSubmission.objects.filter(
                    participation=participation
                ).values('problem_id').annotate(
                    score=Max('points')
                )

                problem_scores = {p['problem_id']: p['score'] for p in submissions}
                total_score = sum(problem_scores.values())

                scoreboard.append({
                    'user': user_profile,
                    'total_score': total_score,
                    'problem_scores': problem_scores
                })

            # Sắp xếp giảm dần theo tổng điểm
            scoreboard.sort(key=lambda x: x['total_score'], reverse=True)

            return JsonResponse({
                'contest': {
                    'id': contest.id,
                    'name': contest.name,
                    'key': contest.key,
                },
                'results': scoreboard
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class TDTUTokenTestView(View):
    @method_decorator(token_required)
    def get(self, request):
        """Endpoint để test token có hợp lệ không"""
        return JsonResponse({
            'message': 'Token is valid',
            'user_data': request.user_data,
            'timestamp': datetime.datetime.now().isoformat()
        })