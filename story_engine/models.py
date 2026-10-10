import uuid
from django.db import models

class GeneratedStory(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تولید'),
        ('generating_text', 'در حال تولید متن داستان'),
        ('text_generated', 'متن آماده شد (در صف تولید صوت)'),
        ('generating_audio', 'در حال تبدیل متن به صوت'),
        ('completed', 'تکمیل شده'),
        ('failed', 'خطا در تولید'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_user_id = models.IntegerField(db_index=True)
    image_id = models.IntegerField(help_text="شناسه عکس انتخاب شده (۱ تا ۱۲)")
    user_prompt = models.TextField(null=True, blank=True, help_text="متن اختیاری کاربر")
    
    generated_text = models.TextField(null=True, blank=True, help_text="داستان تولید شده توسط مدل زبانی")
    generated_audio = models.FileField(upload_to='generated_stories/audio/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Story {self.id} | User: {self.external_user_id} | Status: {self.get_status_display()}"