from django.urls import path
from . import views

app_name = 'ia_assistant'

urlpatterns = [
    path('', views.ChatView.as_view(), name='chat'),
    path('api/chat/', views.AIChatApiView.as_view(), name='api_chat'),
    path('api/clear/', views.ClearHistoryApiView.as_view(), name='api_clear'),
]
