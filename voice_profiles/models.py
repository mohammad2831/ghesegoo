import uuid
import os
from django.db import models

def user_directory_path(instance, filename):
    # استخراج پسوند فایل اصلی (مثلاً wav یا mp3)
    ext = filename.split('.')[-1]
    
    # به جای uuid تصادفی، مستقیماً از آیدی صوتی کاربر استفاده می‌کنیم
    new_filename = f"{instance.external_audio_id}.{ext}"
    
    # مسیر نهایی با همان ساختار پوشه‌بندی دقیق شما
    return f"users/user_{instance.external_user_id}/{new_filename}"

class VoiceProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('processing', 'در حال پردازش'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    )

    # استفاده از UUID برای کلید اصلی در میکروسرویس‌ها امنیت بالاتری دارد
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ارتباط با سرور اصلی پرداخت/کاربران
    external_user_id = models.IntegerField(db_index=True, help_text="آیدی کاربر در سرور اصلی")
    external_audio_id = models.BigIntegerField(unique=True)
    
    # فایل صوتی و وضعیت آن
    audio_file = models.FileField(upload_to=user_directory_path, help_text="فایل صوتی خام کاربر")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
   
    
    # ثبت لاگ و دلایل خطا برای سیستم پشتیبانی یا نمایش به کاربر در سرور اصلی
    rejection_reason = models.TextField(null=True, blank=True)
    
    # زمان‌بندی‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "پروفایل صوتی"
        verbose_name_plural = "پروفایل‌های صوتی"
        indexes = [
            models.Index(fields=['external_user_id', 'status']),
        ]

    def __str__(self):
        return f"Profile {self.id} (User: {self.external_user_id}) - {self.get_status_display()}"