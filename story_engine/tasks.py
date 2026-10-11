import logging
from celery import shared_task
import os
import requests

# نام مدل عکس شما به ImageProfile تغییر کرد
from .models import GeneratedStory 
from image_profiles.models import ImageProfile
from .text_generation import generate_story_text  

from django.core.files.base import ContentFile
from .audio_generation import ChatterboxService
from voice_profiles.models import VoiceProfile

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_story_text_task(self, story_id):

    # ۱. استخراج رکورد داستان
    try:
        story = GeneratedStory.objects.get(id=story_id)
    except GeneratedStory.DoesNotExist:
        return f"Story {story_id} not found."

    story.status = 'generating_text'
    story.save()

    # ۲. استخراج متن تحلیل عکس از دیتابیس با مدل ImageProfile
    try:
        image_record = ImageProfile.objects.get(image_id=story.image_id)
        image_context = image_record.ai_analysis_text
    except ImageProfile.DoesNotExist:
        story.status = 'failed'
        story.error_message = f"عکس شماره {story.image_id} در دیتابیس (ImageProfile) یافت نشد."
        story.save()
        return "Failed: Invalid Image ID"

    # ۳. مدیریت پرامپت خالی کاربر
    user_prompt = story.user_prompt if story.user_prompt else "داستانی آموزنده و زیبا"

    # ۴. فراخوانی تابع تولید متن (ارتباط با LLM)
    story_text = generate_story_text(image_context, user_prompt)

    # ۵. مدیریت خطا در صورت قطعی سرور فردوسی
    if story_text is None:
        logger.warning(f"LLM Error for story {story_id}. Retrying...")
        try:
            raise self.retry(countdown=20)
        except self.MaxRetriesExceededError:
            story.status = 'failed'
            story.error_message = "خطا در ارتباط با مدل زبانی پس از ۳ بار تلاش."
            story.save()
            return "Task failed at LLM generation."

    # ۶. ذخیره موفقیت‌آمیز متن
    story.generated_text = story_text
    story.status = 'text_generated' 
    story.save()
    logger.info(f"✅ Text generated for story {story_id}")

    # ۷. فراخوانی تسک دوم (تولید صوت) - در مرحله بعد از کامنت خارج می‌شود
    generate_story_audio_task.delay(story_id)
    
    return f"Text generation finished. Audio task queued for story {story_id}."


@shared_task(bind=True, max_retries=2)
def generate_story_audio_task(self, story_id):
    try:
        story = GeneratedStory.objects.get(id=story_id)
    except GeneratedStory.DoesNotExist:
        return "Story not found."

    story.status = 'generating_audio'
    story.save()
    
    # تنظیمات وب‌هوک (آدرس و هدرها در ابتدای تسک تعریف می‌شوند تا در همه بخش‌ها در دسترس باشند)
    webhook_url = "http://storyteller-api:8000/api/webhook/story-ready/" 
    headers = {
        # "X-API-Key": "YOUR_SECRET_KEY" # اگر سرور اصلی نیاز به توکن دارد، اینجا فعال کنید
    }

    # ۱. پیدا کردن مسیر فایل رفرنس
    try:
        voice_profile = VoiceProfile.objects.get(
            external_user_id=story.external_user_id,
            external_audio_id=story.external_audio_id,
            status='approved'
        )
        ref_audio_path = voice_profile.audio_file.path
        
    except VoiceProfile.DoesNotExist:
        ref_audio_path = f"/app/users/user_{story.external_user_id}/{story.external_audio_id}.wav"
        logger.warning(f"VoiceProfile DB record missing. Using fallback path: {ref_audio_path}")

    # ۲. بررسی امنیتی: فایل رفرنس وجود دارد؟
    if not os.path.exists(ref_audio_path):
        error_msg = f"فایل صدای کاربر پیدا نشد: {ref_audio_path}"
        logger.error(error_msg)
        
        story.status = 'failed'
        story.error_message = error_msg
        story.save()
        
        # 🔴 ارسال وب‌هوک ارور به سرور اصلی
        try:
            requests.post(
                webhook_url, 
                data={"external_user_id": story.external_user_id, "status": "failed", "error_message": "فایل صدای الگو پیدا نشد."}, 
                headers=headers, 
                timeout=10
            )
        except Exception as e:
            logger.error(f"Failed to send error webhook: {e}")
            
        return "Task failed: Reference audio missing"

    # ۳. فراخوانی چترباکس
    tts_service = ChatterboxService()
    is_success, audio_binary_or_error = tts_service.generate_audio(story.generated_text, ref_audio_path)

    if not is_success:
        logger.warning(f"TTS Error: {audio_binary_or_error}. Retrying...")
        try:
            raise self.retry(countdown=60) # تاخیر برای آزاد شدن VRAM
        except self.MaxRetriesExceededError:
            story.status = 'failed'
            story.error_message = f"خطای TTS: {audio_binary_or_error}"
            story.save()
            
            # 🔴 ارسال وب‌هوک ارور به سرور اصلی (وقتی تلاش مجدد تمام شد)
            try:
                requests.post(
                    webhook_url, 
                    data={"external_user_id": story.external_user_id, "status": "failed", "error_message": "تولید صدا با خطا مواجه شد."}, 
                    headers=headers, 
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to send error webhook: {e}")
                
            return "Task failed at TTS."

    # ذخیره فایل نهایی
    file_name = f"story_{story.external_user_id}_{story.id}.wav"
    story.generated_audio.save(file_name, ContentFile(audio_binary_or_error), save=True)
    
    story.status = 'completed'
    story.save()
    logger.info(f"🎙️ Audio successfully generated for story {story_id}")

    # ==========================================
    # ۴. ارسال وب‌هوک موفقیت‌آمیز به سرور اصلی
    # ==========================================
    payload = {
        "external_user_id": story.external_user_id,
        "generated_text": story.generated_text,
        "status": "success"
    }
    
    try:
        # باز کردن فایل صوتی ذخیره شده برای ارسال
        with open(story.generated_audio.path, 'rb') as audio_file:
            files = {
                'audio_file': (f"{story.id}.wav", audio_file, 'audio/wav')
            }
            
            logger.info("Sending success webhook to main server...")
            response = requests.post(webhook_url, data=payload, files=files, headers=headers, timeout=30)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Webhook delivered successfully: {response.status_code}")
            else:
                logger.error(f"⚠️ Webhook failed with status {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"❌ Failed to send webhook: {str(e)}")

    return f"Pipeline completed for {story_id}"