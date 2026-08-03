from django.db import models
from django.conf import settings

class ChatMessage(models.Model):
    SENDER_CHOICES = (
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant IA'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username} ({self.sender}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
