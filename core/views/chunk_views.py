import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

from ..services.rag_service import rag_service


@require_http_methods(["GET"])
def get_chunk_config(request):
    """Lấy cấu hình chunk hiện tại"""
    try:
        config = rag_service.get_chunk_config()
        return JsonResponse({
            'success': True,
            'chunk_size': config['chunk_size'],
            'chunk_overlap': config['chunk_overlap']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_chunk_config(request):
    """Cập nhật cấu hình chunk và reprocess tài liệu"""
    try:
        data = json.loads(request.body)
        chunk_size = data.get('chunk_size')
        chunk_overlap = data.get('chunk_overlap')
        conversation_id = data.get('conversation_id')
        
        if not chunk_size or not chunk_overlap:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        rag_service.update_chunk_config(int(chunk_size), int(chunk_overlap))
        
        if conversation_id:
            from core.models import Document
            documents = Document.objects.filter(conversation_id=conversation_id, is_active=True)
            if documents.exists():
                doc = documents.first()
                with open(doc.file_path, 'rb') as f:
                    file_content = ContentFile(f.read(), name=doc.file_name)
                    success = rag_service.process_document_with_config(
                        file_content, 
                        doc.file_name,
                        chunk_size=int(chunk_size),
                        chunk_overlap=int(chunk_overlap)
                    )
                    if success:
                        return JsonResponse({
                            'success': True,
                            'message': f'Đã cập nhật cấu hình và xử lý lại tài liệu',
                            'chunk_size': chunk_size,
                            'chunk_overlap': chunk_overlap
                        })
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật cấu hình chunk',
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)