from django.db import models
from django.conf import settings

class HealthVideo(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='published_videos'
    )
    title = models.CharField(max_length=255, verbose_name="Titre de la capsule")
    description = models.TextField(blank=True, null=True, verbose_name="Légende & Hashtags")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Fichier vidéo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de réactions")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} par {self.author.username}"
