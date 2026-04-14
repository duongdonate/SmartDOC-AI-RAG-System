import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.db_service import DatabaseService


@require_http_methods(["GET"])
def get_user(request):
    """Lấy thông tin người dùng từ database"""
    try:
        user = DatabaseService.get_or_create_user("User")
        return JsonResponse({
            'success': True,
            'user_name': user.name,
            'user_id': user.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_user_name(request):
    """Cập nhật tên người dùng"""
    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        
        user = DatabaseService.get_or_create_user("User")
        user.name = new_name
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User name updated successfully',
            'user_name': user.name
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)