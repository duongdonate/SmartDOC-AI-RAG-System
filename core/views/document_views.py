import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

from ..services.rag_service import rag_service
from ..services.db_service import DatabaseService


@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    """API upload file (hỗ trợ PDF và DOCX)"""
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        conversation_id = request.POST.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        uploaded_file = request.FILES['pdf_file']
        file_name = uploaded_file.name
        file_ext = file_name.lower().split('.')[-1]
        
        if file_ext not in ['pdf', 'docx']:
            return JsonResponse({'error': 'Chỉ hỗ trợ file PDF hoặc DOCX'}, status=400)
        
        # Xóa document cũ
        existing_docs = DatabaseService.get_conversation_documents(conversation_id)
        for doc in existing_docs:
            DatabaseService.delete_document(doc.id)
        
        # Lưu document mới
        document = DatabaseService.save_document(
            conversation_id=conversation_id,
            file=uploaded_file,
            file_name=file_name,
            file_size=uploaded_file.size
        )
        
        if not document:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        # Xử lý file với RAG service
        success = rag_service.process_document(uploaded_file, file_name)
        
        if success:
            file_size_kb = uploaded_file.size / 1024
            size_display = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024:.1f} MB"
            file_type_display = "PDF" if file_ext == 'pdf' else "DOCX"
            
            return JsonResponse({
                'success': True,
                'message': f'✅ {file_type_display} "{file_name}" đã được xử lý thành công!',
                'filename': file_name,
                'document_id': document.id,
                'file_size': size_display,
                'file_type': file_ext
            })
        else:
            return JsonResponse({'error': f'Không thể xử lý file {file_name}'}, status=500)
            
    except Exception as e:
        print(f"Error in upload_pdf: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def load_document(request):
    """Tải lại document đã có vào RAG service"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        document_id = data.get('document_id')
        
        if not conversation_id or not document_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        from core.models import Document
        document = Document.objects.get(id=document_id, conversation_id=conversation_id)
        file_ext = document.file_name.lower().split('.')[-1]
        
        with open(document.file_path, 'rb') as f:
            file_content = ContentFile(f.read(), name=document.file_name)
            
            if hasattr(rag_service, 'process_document'):
                success = rag_service.process_document(file_content, document.file_name)
            else:
                success = rag_service.process_pdf(file_content)
            
            if success:
                file_type_display = "DOCX" if file_ext == 'docx' else "PDF"
                return JsonResponse({
                    'success': True,
                    'message': f'Đã tải lại {file_type_display} {document.file_name}',
                    'file_type': file_ext
                })
            else:
                return JsonResponse({'error': 'Failed to load document'}, status=500)
                
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_document(request):
    """Xóa document đã upload"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        success = DatabaseService.clear_all_documents(conversation_id)
        rag_service.clear()
        
        if success:
            return JsonResponse({'success': True, 'message': 'All documents cleared'})
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)