import logging
from celery import shared_task

# نام مدل عکس شما به ImageProfile تغییر کرد
from .models import GeneratedStory 
from image_profiles.models import ImageProfile
from .text_generation import generate_story_text  

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
    # generate_story_audio_task.delay(story_id)
    
    return f"Text generation finished. Audio task queued for story {story_id}."