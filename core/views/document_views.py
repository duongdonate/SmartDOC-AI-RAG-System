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
def upload_document(request): # Đổi tên cho chuẩn ngữ nghĩa
    """API upload nhiều file (hỗ trợ PDF và DOCX)"""
    try:
        # Lấy danh sách file từ form data (Front-end phải gửi key là 'files')
        uploaded_files = request.FILES.getlist('files')
        
        if not uploaded_files:
            # Fallback cho trường hợp gọi API cũ
            if 'pdf_file' in request.FILES:
                uploaded_files = [request.FILES['pdf_file']]
            else:
                return JsonResponse({'error': 'No files uploaded'}, status=400)
        
        conversation_id = request.POST.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        saved_documents = []
        
        # 1. Lưu các file MỚI vào Database và thư mục media/pdf
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_ext = file_name.lower().split('.')[-1]
            
            if file_ext not in ['pdf', 'docx']:
                continue # Bỏ qua file sai định dạng
            
            # DatabaseService sẽ tạo bản ghi mới (Append)
            document = DatabaseService.save_document(
                conversation_id=conversation_id,
                file=uploaded_file,
                file_name=file_name,
                file_size=uploaded_file.size
            )
            
            if document:
                saved_documents.append(document)

        if not saved_documents:
            return JsonResponse({'error': 'Không thể lưu tài liệu hợp lệ nào'}, status=400)
        
        # 2. Truy vấn TẤT CẢ tài liệu của hội thoại này (Cũ + Mới)
        all_docs = DatabaseService.get_conversation_documents(conversation_id)
        
        file_paths = [doc.file_path for doc in all_docs]
        file_names = [doc.file_name for doc in all_docs]
        
        # 3. Gọi RAG service để băm và nhào nặn lại toàn bộ dữ liệu
        # Tại sao phải băm lại toàn bộ? Vì thuật toán BM25 cần đọc toàn bộ văn bản để tính điểm từ khóa chính xác
        success = rag_service.process_multiple_files(
            file_paths=file_paths,
            file_names=file_names
        )
        
        # 4. Lưu Index xuống ổ cứng
        if success:
            rag_service._save_vectorstore(
                conversation_id=int(conversation_id), 
                source_file_paths=file_paths
            )
            
            # Tính tổng dung lượng của TẤT CẢ các file
            total_size_mb = sum(doc.file_size for doc in all_docs) / (1024 * 1024)
            
            return JsonResponse({
                'success': True,
                'message': f'✅ Đã tải lên thêm {len(saved_documents)} tài liệu mới! (Tổng cộng đang có: {len(all_docs)} tài liệu)',
                'file_names': file_names, # Trả về danh sách TẤT CẢ file
                'total_files': len(all_docs),
                'total_size': f"{total_size_mb:.2f} MB"
            })
        else:
            return JsonResponse({'error': 'Lỗi khi xử lý vector dữ liệu cho các file'}, status=500)
            
    except Exception as e:
        print(f"Error in upload_documents: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def load_document(request):
    """Restore toàn bộ context (nhiều docs) cho conversation từ vector index."""
    try:
        data = json.loads(request.body)
        conversation_id = data.get("conversation_id")

        if not conversation_id:
            return JsonResponse({"error": "Missing parameters"}, status=400)

        conversation_id_int = int(conversation_id)
        from core.models import Document

        # Lấy TẤT CẢ document của conversation này
        documents = Document.objects.filter(conversation_id=conversation_id_int, is_active=True)
        if not documents.exists():
            return JsonResponse({"error": "Không tìm thấy tài liệu nào cho hội thoại này"}, status=404)

        file_paths = [doc.file_path for doc in documents]
        file_names = [doc.file_name for doc in documents]

        # Gọi hàm load list file mới của rag_service
        # Chú ý: Bạn cần cập nhật hàm load_or_create_conversation_index trong RAGService để nhận list file
        success = rag_service._load_vectorstore_if_compatible(
            conversation_id=conversation_id_int,
            file_names=file_names,
            source_file_paths=file_paths
        )
        
        # Nếu bộ cache không tương thích (bị xóa hoặc đổi chunk_size), tạo lại
        if not success:
             success = rag_service.process_multiple_files(file_paths, file_names)
             if success:
                rag_service._save_vectorstore(conversation_id_int, file_paths)

        if not success:
            return JsonResponse({"error": "Failed to load documents into memory"}, status=500)

        return JsonResponse({
            "success": True,
            "message": f"Đã tải lại {len(file_names)} tài liệu vào bộ nhớ",
            "file_names": file_names,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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
        rag_service.clear_persisted_index(conversation_id)
        rag_service.clear()
        
        if success:
            return JsonResponse({'success': True, 'message': 'All documents cleared'})
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)