import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.db.models import Max, Sum, Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from judge.models import Organization, Contest, Profile, ContestParticipation, ContestSubmission, Problem, Submission


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