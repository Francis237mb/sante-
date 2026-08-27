from django.urls import path
from . import views

app_name = 'ia_assistant'

urlpatterns = [
    path('', views.ChatView.as_view(), name='chat'),
    path('c/<int:conversation_id>/', views.ChatView.as_view(), name='chat_conversation'),
    path('api/chat/', views.AIChatApiView.as_view(), name='api_chat'),
    path('api/new/', views.NewConversationApiView.as_view(), name='api_new'),
    path('api/delete/<int:conversation_id>/', views.DeleteConversationApiView.as_view(), name='api_delete'),
    path('api/clear/', views.ClearHistoryApiView.as_view(), name='api_clear'),
]
