import uuid
from django.db import models

class GeneratedStory(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تولید'),
        ('processing', 'در حال پردازش (متن و صوت)'),
        ('completed', 'تکمیل شده'),
        ('failed', 'خطا در تولید'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_user_id = models.IntegerField(db_index=True)
    image_id = models.IntegerField(help_text="شناسه عکس انتخاب شده (۱ تا ۱۲)")
    user_prompt = models.TextField(null=True, blank=True, help_text="متن اختیاری کاربر")
    # خروجی‌های هوش مصنوعی که در گام بعدی توسط سلری پر می‌شوند
    generated_text = models.TextField(null=True, blank=True, help_text="داستان تولید شده توسط مدل زبانی")
    generated_audio = models.FileField(upload_to='generated_stories/audio/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Story {self.id} - User: {self.external_user_id} - {self.status}"