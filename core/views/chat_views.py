import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.rag_service import rag_service
from ..services.db_service import DatabaseService


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
        
        if rag_service.vector_store is None:
            return JsonResponse({
                'success': False,
                'answer': '⚠️ Vui lòng tải lên một file PDF hoặc DOCX trước khi đặt câu hỏi.',
                'sources': []
            }, status=200)
        
        # Lưu câu hỏi
        DatabaseService.add_message(conversation_id, 'user', question)
        DatabaseService.update_conversation_last_question(conversation_id, question)
        DatabaseService.add_question_history(conversation_id, question)
        
        # Gọi RAG service
        result = rag_service.ask_question(question)
        
        # Tạo answer đầy đủ
        full_answer = result['answer']
        sources = result.get('sources', [])
        
        if sources and len(sources) > 0:
            full_answer += '\n\n📚 **Nguồn tham khảo:** \n'
            for idx, source in enumerate(sources):
                # Hiển thị nguồn context với tên file và số trang (nếu có)
                file_name_info = f" **[{source.get('source_file')}]** " if source.get('source_file') else ''
                page_number = source.get('page_number')
                if isinstance(page_number, int):
                    page_number = page_number + 1
                elif isinstance(page_number, str) and page_number.isdigit():
                    page_number = int(page_number) + 1
                page_info = f" *(Trang {page_number})*" if page_number not in (None, "") else ''
                content_preview = source.get('content', '')[:100] + '...' if len(source.get('content', '')) > 100 else source.get('content', '')
                
                full_answer += f"\n {idx + 1}.{file_name_info}{page_info}: \"{content_preview}\" \n"
        
        # Lưu câu trả lời
        DatabaseService.add_message(conversation_id, 'assistant', full_answer)
        
        return JsonResponse({
            'success': True,
            'answer': result['answer'],
            'full_answer': full_answer,
            'sources': sources
        })
        
    except Exception as e:
        print(f"Error in ask_question: {e}")
        
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


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
            'timestamp': q.get_timestamp_local().strftime('%H:%M %d/%m/%Y')
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


@require_http_methods(["GET"])
def check_status(request):
    """Kiểm tra trạng thái service"""
    conversation_id = request.GET.get('conversation_id')
    doc_info = rag_service.get_document_info() if hasattr(rag_service, 'get_document_info') else {}
    
    # RAG service giờ trả về list trong 'file_names' và 'file_types'
    return JsonResponse({
        'has_document': rag_service.vector_store is not None,
        'model_loaded': rag_service.llm is not None,
        'conversation_id': conversation_id,
        'current_files': doc_info.get('file_names', []), # Trả về mảng
        'current_file_types': doc_info.get('file_types', []) # Trả về mảng
    })