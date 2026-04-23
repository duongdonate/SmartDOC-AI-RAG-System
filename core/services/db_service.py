import os
import shutil
from django.conf import settings
from django.utils import timezone
from core.models import User, Conversation, Document, Message, QuestionHistory
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service quản lý database operations"""

    @staticmethod
    def check_first_question(conversation_id):
        """Kiểm tra nếu đây là câu hỏi đầu tiên của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            return conversation.total_messages == 0
        return False
    
    @staticmethod
    def set_name_conversation(conversation_id, name):
        """Đặt tên cho hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            conversation.title = name
            conversation.save()
            return True
        return False
    
    @staticmethod
    def get_or_create_user(name="User"):
        """Lấy hoặc tạo user (chỉ 1 user local)"""
        user, created = User.objects.get_or_create(
            id=1,  # Chỉ có 1 user với id=1
            defaults={'name': name}
        )
        if created:
            logger.info(f"Created new user: {name}")
        return user
    
    @staticmethod
    def create_conversation(user, title="New Conversation"):
        """Tạo đoạn hội thoại mới"""
        conversation = Conversation.objects.create(
            user=user,
            title=title,
            created_at=timezone.now(),
            last_updated=timezone.now()
        )
        logger.info(f"Created new conversation: {conversation.id} - {title}")
        return conversation
    
    @staticmethod
    def get_conversation(conversation_id):
        """Lấy thông tin hội thoại theo ID"""
        try:
            return Conversation.objects.get(id=conversation_id, is_active=True)
        except Conversation.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_conversations(user):
        """Lấy tất cả hội thoại của user"""
        return Conversation.objects.filter(user=user, is_active=True)
    
    @staticmethod
    def update_conversation_last_question(conversation_id, question):
        """Cập nhật câu hỏi cuối cùng của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            conversation.last_question = question
            conversation.last_updated = timezone.now()
            conversation.save()
            return True
        return False
    
    @staticmethod
    def increment_message_count(conversation_id):
        """Tăng số lượng tin nhắn trong hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            conversation.total_messages += 1
            conversation.last_updated = timezone.now()
            conversation.save()
            return True
        return False
    
    @staticmethod
    def add_message(conversation_id, role, content):
        """Thêm tin nhắn vào hội thoại"""
        check_first = DatabaseService.check_first_question(conversation_id);
        if(check_first):
            DatabaseService.set_name_conversation(conversation_id, content[:30])  

        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return None
        
        message = Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            timestamp=timezone.now()
        )
        
        # Cập nhật số lượng tin nhắn
        conversation.total_messages += 1
        conversation.last_updated = timezone.now()
        conversation.save()
        
        return message
    
    @staticmethod
    def get_conversation_messages(conversation_id):
        """Lấy tất cả tin nhắn của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            return Message.objects.filter(conversation=conversation)
        return []
    
    @staticmethod
    def save_document(conversation_id, file, file_name, file_size):
        """Lưu document vào thư mục và database"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Tạo thư mục cho conversation nếu chưa có
        conversation_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(conversation_id))
        os.makedirs(conversation_dir, exist_ok=True)
        
        # Đường dẫn file
        file_path = os.path.join(conversation_dir, file_name)
        
        # Lưu file
        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Tạo record trong database
        document = Document.objects.create(
            conversation=conversation,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            uploaded_at=timezone.now()
        )
        
        # Cập nhật số lượng tài liệu
        conversation.total_documents += 1
        conversation.save()
        
        logger.info(f"Saved document: {file_name} for conversation {conversation_id}")
        return document
    
    @staticmethod
    def get_conversation_documents(conversation_id):
        """Lấy tất cả document của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            return Document.objects.filter(conversation=conversation, is_active=True)
        return []
    
    @staticmethod
    def delete_document(document_id):
        """Xóa document khỏi hệ thống"""
        try:
            document = Document.objects.get(id=document_id)
            # Xóa file vật lý
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Cập nhật số lượng tài liệu
            conversation = document.conversation
            conversation.total_documents -= 1
            conversation.save()
            
            # Xóa record trong database
            document.delete()
            logger.info(f"Deleted document: {document.file_name}")
            return True
        except Document.DoesNotExist:
            return False
    
    @staticmethod
    def add_question_history(conversation_id, question):
        """Thêm câu hỏi vào lịch sử sidebar"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if not conversation:
            return None
        
        question_history = QuestionHistory.objects.create(
            conversation=conversation,
            question=question,
            timestamp=timezone.now()
        )
        return question_history
    
    @staticmethod
    def get_question_history(conversation_id, limit=20):
        """Lấy lịch sử câu hỏi cho sidebar"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            return QuestionHistory.objects.filter(conversation=conversation)[:limit]
        return []
    
    @staticmethod
    def clear_conversation_history(conversation_id):
        """Xóa lịch sử chat và câu hỏi của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            # Xóa tin nhắn
            Message.objects.filter(conversation=conversation).delete()
            # Xóa lịch sử câu hỏi
            QuestionHistory.objects.filter(conversation=conversation).delete()
            # Reset counters
            conversation.total_messages = 0
            conversation.last_question = None
            conversation.save()
            return True
        return False
    
    @staticmethod
    def clear_all_documents(conversation_id):
        """Xóa tất cả document của hội thoại"""
        conversation = DatabaseService.get_conversation(conversation_id)
        if conversation:
            documents = Document.objects.filter(conversation=conversation)
            for doc in documents:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
            documents.delete()
            conversation.total_documents = 0
            conversation.save()
            
            # Xóa thư mục nếu rỗng
            conversation_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(conversation_id))
            if os.path.exists(conversation_dir) and not os.listdir(conversation_dir):
                os.rmdir(conversation_dir)
            
            return True
        return False