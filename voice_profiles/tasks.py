import logging
from celery import shared_task
from .models import VoiceProfile
from .utils import AudioValidator
import requests

# فعال‌سازی لاگر برای چاپ پیام‌های رنگی و دقیق در سلری
logger = logging.getLogger(__name__)

@shared_task
def validate_voice_profile_task(profile_id):
    try:
        profile = VoiceProfile.objects.get(id=profile_id)
    except VoiceProfile.DoesNotExist:
        return f"Profile {profile_id} not found in DB."

    if not profile.audio_file:
        profile.status = 'rejected'
        profile.rejection_reason = "No physical file found on server."
        profile.save()
        return "Rejected: No file"

    # مسیر دقیق فایل روی هارد برای دیباگ چاپ می‌شود
    file_path = profile.audio_file.path
    logger.info(f"Attempting to process file at: {file_path}")

    validator = AudioValidator(file_path)
    is_valid, message, metadata = validator.run_pipeline()

    if is_valid:
        profile.status = 'approved'
        profile.duration_seconds = metadata.get('duration')
        profile.sample_rate = metadata.get('sample_rate')
        profile.save()
        
        logger.info(f"Profile {profile_id} Approved: {message}")
        
    else:
        profile.status = 'rejected'
        profile.rejection_reason = message
        
        # پاک کردن فایل فیزیکی در صورت رد شدن برای جلوگیری از پر شدن هارد
        profile.audio_file.delete(save=False)
        profile.save()
        
        logger.error(f"❌ Profile {profile_id} Rejected. Reason: {message}")

    # ==========================================
    # بخش ارسال Webhook به سرور اصلی جانگو
    # ==========================================
    
    # آدرس وب‌هوک را فعلاً به صورت یک متغیر فرضی قرار دادیم تا بعداً جایگزین کنید
    webhook_url = "http://storyteller-api:8000/api/webhooks/voice-verification/"
    
    webhook_payload = {
        "external_user_id": profile.external_user_id,
        "external_audio_id": profile.external_audio_id,
        "status": profile.status,
        "rejection_reason": profile.rejection_reason if not is_valid else None
    }
    
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {settings.AI_CORE_SECRET_TOKEN}" # در صورت نیاز به امنیت
    }

    try:
        # ارسال درخواست POST به سرور اصلی با تایم‌اوت ۵ ثانیه
        response = requests.post(webhook_url, json=webhook_payload, headers=headers, timeout=5.0)
        
        if response.status_code == 200:
            logger.info(f"Webhook successfully delivered for audio {profile.external_audio_id}")
        else:
            logger.warning(f"Webhook delivered but main server returned {response.status_code}: {response.text}")
            
    except requests.RequestException as e:
        # اگر سرور اصلی خاموش باشد یا شبکه قطع باشد، تسک کرش نمی‌کند و فقط لاگ می‌اندازد
        logger.error(f"Failed to send webhook to main server: {e}")

    # بازگرداندن پیام نهایی برای ثبت در نتیجه خود Celery
    if is_valid:
        return "Task finished: approved"
    else:
        return f"Task finished: rejected | Reason: {message}"