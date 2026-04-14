from django.shortcuts import render
import pytz
from ..services.db_service import DatabaseService


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
    
    # Xử lý conversation
    if conversation_id:
        conversation = DatabaseService.get_conversation(conversation_id)
        print(f"Found conversation: {conversation}")
        if conversation:
            print(f"Conversation title: {conversation.title}")
            print(f"Conversation last question: {conversation.last_question}")
        else:
            print(f"Conversation with ID {conversation_id} NOT FOUND!")
            conversation = DatabaseService.create_conversation(user, "Cuộc trò chuyện mới")
            conversation_id = conversation.id
            print(f"Created new conversation with ID: {conversation_id}")
    else:
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
    
    # Lấy danh sách documents
    documents = DatabaseService.get_conversation_documents(conversation_id)
    documents_data = []
    for doc in documents:
        file_size_mb = doc.file_size / (1024 * 1024)
        size_str = f"{file_size_mb:.1f} MB" if file_size_mb > 1 else f"{doc.file_size / 1024:.0f} KB"
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