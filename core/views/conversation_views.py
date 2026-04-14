import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.db_service import DatabaseService


@require_http_methods(["GET"])
def get_conversations(request):
    """Lấy danh sách tất cả hội thoại"""
    user = DatabaseService.get_or_create_user("User")
    conversations = DatabaseService.get_user_conversations(user)
    
    data = []
    for conv in conversations:
        data.append({
            'id': conv.id,
            'title': conv.title,
            'last_question': conv.last_question,
            'last_updated': conv.last_updated.strftime('%H:%M %d/%m/%Y'),
            'total_messages': conv.total_messages,
            'total_documents': conv.total_documents
        })
    
    return JsonResponse({
        'success': True,
        'conversations': data
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_conversation(request):
    """Tạo hội thoại mới"""
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Cuộc trò chuyện mới')
        user = DatabaseService.get_or_create_user("User")
        
        conversation = DatabaseService.create_conversation(user, title)
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'title': conversation.title
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def rename_conversation(request):
    """Đổi tên hội thoại"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        new_title = data.get('new_title', '').strip()
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        if not new_title:
            return JsonResponse({'error': 'New title required'}, status=400)
        
        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        conversation.title = new_title
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation renamed successfully',
            'conversation_id': conversation_id,
            'new_title': new_title
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_conversation(request):
    """Xóa hội thoại"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        DatabaseService.clear_all_documents(conversation_id)
        conversation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation deleted successfully',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)