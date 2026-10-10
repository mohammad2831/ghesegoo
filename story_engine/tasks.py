import logging
from celery import shared_task

# نام مدل عکس شما به ImageProfile تغییر کرد
from .models import GeneratedStory 
from image_profiles.models import ImageProfile
from .text_generation import generate_story_text  

from django.core.files.base import ContentFile
from .audio_generation import ChatterboxService

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

    # پیدا کردن مسیر فایل رفرنس 
    # (بسته به معماری شما، اگر رفرنس ثابت است مسیر آن را بدهید، اگر متغیر است از مدل کاربر بخوانید)
    ref_audio_path = "/path/to/your/project/audio_samples/sample_ref.wav"

    # فراخوانی سرویس چترباکس
    tts_service = ChatterboxService()
    is_success, audio_binary_or_error = tts_service.generate_audio(story.generated_text, ref_audio_path)

    if not is_success:
        logger.warning(f"TTS Error: {audio_binary_or_error}. Retrying...")
        try:
            raise self.retry(countdown=60) # تاخیر زیاد برای آزاد شدن VRAM
        except self.MaxRetriesExceededError:
            story.status = 'failed'
            story.error_message = f"خطای TTS: {audio_binary_or_error}"
            story.save()
            return "Task failed at TTS."

    # ذخیره فایل در دیتابیس (ContentFile بایت‌ها را تبدیل به فایل استاندارد جانگو می‌کند)
    file_name = f"story_{story.external_user_id}_{story.id}.wav"
    story.generated_audio.save(file_name, ContentFile(audio_binary_or_error), save=True)
    
    story.status = 'completed'
    story.save()
    logger.info(f"🎙️ Audio successfully generated for story {story_id}")

    return f"Pipeline completed for {story_id}"