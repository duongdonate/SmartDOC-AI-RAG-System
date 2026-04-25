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
    """Cập nhật cấu hình chunk và reprocess TẤT CẢ tài liệu"""
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
            # Lấy tất cả documents
            documents = Document.objects.filter(conversation_id=conversation_id, is_active=True)
            
            if documents.exists():
                file_paths = [doc.file_path for doc in documents]
                file_names = [doc.file_name for doc in documents]
                
                # Băm lại dữ liệu bằng config mới
                success = rag_service.process_multiple_files(
                    file_paths=file_paths, 
                    file_names=file_names
                )
                
                if success:
                    # Lưu đè lại bản index mới
                    rag_service._save_vectorstore(int(conversation_id), file_paths)
                    return JsonResponse({
                        'success': True,
                        'message': f'Đã cập nhật cấu hình và xử lý lại {len(documents)} tài liệu',
                        'chunk_size': chunk_size,
                        'chunk_overlap': chunk_overlap
                    })
                else:
                    return JsonResponse({'error': 'Cập nhật chunk thành công nhưng lỗi khi xử lý lại file'}, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật cấu hình chunk (chưa áp dụng file nào)',
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)