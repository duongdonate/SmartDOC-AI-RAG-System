from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import tempfile
import os
from datetime import datetime

import pytz

from .services.rag_service import rag_service
from .services.db_service import DatabaseService

# ============= PAGE VIEWS =============
def home(request):
    """Trang home"""
    return render(request, 'home.html')

def dashboard(request):   
    """Trang dashboard - hiển thị tất cả hội thoại"""
    user = DatabaseService.get_or_create_user("User")
    conversations = DatabaseService.get_user_conversations(user)
    ho_chi_minh_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    chat_history = []
    for conv in conversations:
        local_time = conv.last_updated.astimezone(ho_chi_minh_tz)
        chat_history.append({
            'id': conv.id,
            'title': conv.title,
            'preview': conv.last_question if conv.last_question else "Chưa có câu hỏi nào",
            'time': local_time.strftime('%H:%M %d/%m/%Y'),
            'messages': conv.total_messages
        })
    
    context = {
        'chat_history': chat_history,
        'user_name': user.name
    }
    return render(request, 'dashboard.html', context)

def chat(request, conversation_id=None):
    """Trang chat với conversation cụ thể"""
    print("=" * 50)
    print(f"CHAT VIEW CALLED with conversation_id: {conversation_id}")
    print(f"Type: {type(conversation_id)}")
    
    user = DatabaseService.get_or_create_user("User")
    
    # Nếu có conversation_id, cố gắng lấy hội thoại đó
    if conversation_id:
        conversation = DatabaseService.get_conversation(conversation_id)
        print(f"Found conversation: {conversation}")
        if conversation:
            print(f"Conversation title: {conversation.title}")
            print(f"Conversation last question: {conversation.last_question}")
        else:
            print(f"Conversation with ID {conversation_id} NOT FOUND!")
            # Nếu không tìm thấy, tạo mới
            conversation = DatabaseService.create_conversation(user, "Cuộc trò chuyện mới")
            conversation_id = conversation.id
            print(f"Created new conversation with ID: {conversation_id}")
    else:
        # Nếu không có conversation_id, tạo mới
        conversation = DatabaseService.create_conversation(user, "Cuộc trò chuyện mới")
        conversation_id = conversation.id
        print(f"Created new conversation with ID: {conversation_id}")
    
    # Lấy lịch sử tin nhắn
    messages_list = DatabaseService.get_conversation_messages(conversation_id)
    print(f"Found {len(messages_list)} messages")
    
    messages_data = []
    for msg in messages_list:
        messages_data.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    
    # Lấy lịch sử câu hỏi
    question_history = DatabaseService.get_question_history(conversation_id)
    print(f"Found {len(question_history)} questions")
    
    questions_data = []
    for q in question_history:
        questions_data.append({
            'id': q.id,
            'question': q.question,
            'timestamp': q.timestamp.strftime('%H:%M %d/%m')
        })
    
    # Lấy danh sách documents (hỗ trợ cả PDF và DOCX)
    documents = DatabaseService.get_conversation_documents(conversation_id)
    documents_data = []
    for doc in documents:
        file_size_mb = doc.file_size / (1024 * 1024)
        size_str = f"{file_size_mb:.1f} MB" if file_size_mb > 1 else f"{doc.file_size / 1024:.0f} KB"
        
        # Xác định loại file dựa trên phần mở rộng
        file_ext = doc.file_name.lower().split('.')[-1]
        file_type = "DOCX" if file_ext == 'docx' else "PDF"
        
        documents_data.append({
            'id': doc.id,
            'name': doc.file_name,
            'size': size_str,
            'type': file_type,
            'file_ext': file_ext,
            'uploaded_at': doc.uploaded_at.strftime('%H:%M %d/%m/%Y')
        })
    
    context = {
        'conversation_id': conversation_id,
        'conversation_title': conversation.title,
        'messages': messages_data,
        'recent_questions': questions_data,
        'documents': documents_data,
        'has_document': len(documents_data) > 0
    }
    
    print(f"Returning context with conversation_id: {conversation_id}")
    print("=" * 50)
    
    return render(request, 'chat.html', context)


# ============= API ENDPOINTS =============

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
        
        # Kiểm tra định dạng file
        if file_ext not in ['pdf', 'docx']:
            return JsonResponse({'error': 'Chỉ hỗ trợ file PDF hoặc DOCX'}, status=400)
        
        # Xóa document cũ
        existing_docs = DatabaseService.get_conversation_documents(conversation_id)
        for doc in existing_docs:
            DatabaseService.delete_document(doc.id)
        
        # Lưu document mới vào database
        document = DatabaseService.save_document(
            conversation_id=conversation_id,
            file=uploaded_file,
            file_name=file_name,
            file_size=uploaded_file.size
        )
        
        if not document:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        # Xử lý file với RAG service (hỗ trợ cả PDF và DOCX)
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
def ask_question(request):
    """API hỏi đáp dựa trên tài liệu (PDF/DOCX)"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        # Kiểm tra xem có document đã upload chưa
        if rag_service.vector_store is None:
            return JsonResponse({
                'success': False,
                'answer': '⚠️ Vui lòng tải lên một file PDF hoặc DOCX trước khi đặt câu hỏi.',
                'sources': []
            }, status=200)
        
        # Lưu câu hỏi của user vào database
        DatabaseService.add_message(conversation_id, 'user', question)
        DatabaseService.update_conversation_last_question(conversation_id, question)
        DatabaseService.add_question_history(conversation_id, question)
        
        # Gọi RAG service để trả lời
        result = rag_service.ask_question(question)
        
        # Tạo answer đầy đủ (bao gồm cả sources) để lưu vào database
        full_answer = result['answer']
        sources = result.get('sources', [])
        
        if sources and len(sources) > 0:
            full_answer += '\n\n📚 **Nguồn tham khảo:**'
            for idx, source in enumerate(sources):
                page_info = f" (Trang {source.get('page_number', '?')})" if source.get('page_number') else ''
                type_info = f" [{source.get('file_type', 'PDF').upper()}]" if source.get('file_type') else ''
                content_preview = source.get('content', '')[:100] + '...' if len(source.get('content', '')) > 100 else source.get('content', '')
                full_answer += f"\n{idx + 1}.{type_info}{page_info}: \"{content_preview}\""
        
        # Lưu câu trả lời ĐẦY ĐỦ (bao gồm cả sources) vào database
        DatabaseService.add_message(conversation_id, 'assistant', full_answer)
        
        return JsonResponse({
            'success': True,
            'answer': result['answer'],
            'full_answer': full_answer,  # Trả về cả full_answer nếu cần
            'sources': sources
        })
        
    except Exception as e:
        print(f"Error in ask_question: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def clear_history(request):
    """Xóa lịch sử chat của conversation"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        success = DatabaseService.clear_conversation_history(conversation_id)
        
        if success:
            return JsonResponse({'success': True, 'message': 'History cleared'})
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
            
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


@require_http_methods(["GET"])
def check_status(request):
    """Kiểm tra trạng thái service"""
    conversation_id = request.GET.get('conversation_id')
    doc_info = rag_service.get_document_info() if hasattr(rag_service, 'get_document_info') else {}
    
    return JsonResponse({
        'has_document': rag_service.vector_store is not None,
        'model_loaded': rag_service.llm is not None,
        'conversation_id': conversation_id,
        'current_file': doc_info.get('file_name'),
        'current_file_type': doc_info.get('file_type')
    })


@require_http_methods(["GET"])
def get_questions(request):
    """Lấy danh sách câu hỏi của conversation"""
    conversation_id = request.GET.get('conversation_id')
    if not conversation_id:
        return JsonResponse({'error': 'Conversation ID required'}, status=400)
    
    questions = DatabaseService.get_question_history(conversation_id)
    questions_data = [
        {
            'question': q.question,
            'timestamp': q.timestamp.strftime('%H:%M %d/%m/%Y')
        }
        for q in questions
    ]
    
    return JsonResponse({
        'success': True,
        'questions': questions_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def add_question(request):
    """Thêm câu hỏi vào lịch sử"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not question or not conversation_id:
            return JsonResponse({'error': 'Question and conversation_id required'}, status=400)
        
        DatabaseService.add_question_history(conversation_id, question)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
def load_document(request):
    """Tải lại document đã có vào RAG service (hỗ trợ PDF và DOCX)"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        document_id = data.get('document_id')
        
        if not conversation_id or not document_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        # Lấy thông tin document từ database
        from core.models import Document
        document = Document.objects.get(id=document_id, conversation_id=conversation_id)
        
        # Xác định loại file
        file_ext = document.file_name.lower().split('.')[-1]
        
        # Đọc file từ đường dẫn
        with open(document.file_path, 'rb') as f:
            from django.core.files.base import ContentFile
            file_content = ContentFile(f.read(), name=document.file_name)
            
            # Xử lý file với RAG service
            if hasattr(rag_service, 'process_document'):
                success = rag_service.process_document(file_content, document.file_name)
            else:
                # Fallback cho process_pdf nếu chưa cập nhật rag_service
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
                
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
        
        # Lấy conversation và cập nhật tên
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


@csrf_exempt
@require_http_methods(["POST"])
def delete_conversation(request):
    """Xóa hội thoại"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return JsonResponse({'error': 'Conversation ID required'}, status=400)
        
        # Lấy conversation và xóa
        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        # Xóa tất cả documents liên quan (cả file vật lý)
        DatabaseService.clear_all_documents(conversation_id)
        
        # Xóa conversation
        conversation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation deleted successfully',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
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
        
        # Cập nhật cấu hình
        rag_service.update_chunk_config(int(chunk_size), int(chunk_overlap))
        
        # Nếu có tài liệu, reprocess
        if conversation_id:
            from core.models import Document
            documents = Document.objects.filter(conversation_id=conversation_id, is_active=True)
            if documents.exists():
                doc = documents.first()
                with open(doc.file_path, 'rb') as f:
                    from django.core.files.base import ContentFile
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