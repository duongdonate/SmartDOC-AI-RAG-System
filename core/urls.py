from django.urls import path
from . import views

urlpatterns = [
    # Page Views
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chat/', views.chat, name='chat'),
    path('chat/<int:conversation_id>/', views.chat, name='chat_with_id'),
    
    # Document API
    path('api/upload/', views.upload_pdf, name='upload_pdf'),
    path('api/load-document/', views.load_document, name='load_document'),
    path('api/clear-document/', views.clear_document, name='clear_document'),
    
    # Chat API
    path('api/ask/', views.ask_question, name='ask_question'),
    path('api/get-questions/', views.get_questions, name='get_questions'),
    path('api/add-question/', views.add_question, name='add_question'),
    path('api/clear-history/', views.clear_history, name='clear_history'),
    path('api/status/', views.check_status, name='check_status'),
    
    # Conversation API
    path('api/get-conversations/', views.get_conversations, name='get_conversations'),
    path('api/create-conversation/', views.create_conversation, name='create_conversation'),
    path('api/rename-conversation/', views.rename_conversation, name='rename_conversation'),
    path('api/delete-conversation/', views.delete_conversation, name='delete_conversation'),
    
    # User API
    path('api/get-user/', views.get_user, name='get_user'),
    path('api/update-user-name/', views.update_user_name, name='update_user_name'),
    
    # Chunk Config API
    path('api/get-chunk-config/', views.get_chunk_config, name='get_chunk_config'),
    path('api/update-chunk-config/', views.update_chunk_config, name='update_chunk_config'),
]