# api_gateway/serializers.py
from rest_framework import serializers

class GatewayProfileUploadSerializer(serializers.Serializer):
    external_user_id = serializers.IntegerField(required=True, help_text="آیدی کاربر در سرور اصلی")
    audio_file = serializers.FileField(required=True, help_text="صوت مرجع کاربر برای ثبت پروفایل")
    external_audio_id = serializers.IntegerField(required=True, help_text="آیدی صوت در سرور اصلی")



class GatewayImageSelectionSerializer(serializers.Serializer):
    external_user_id = serializers.IntegerField(required=True, help_text="آیدی کاربر در سرور اصلی")
    image_id = serializers.IntegerField(required=True, help_text="شناسه یکتای این عکس از سمت سرور اصلی")
    #image_file = serializers.ImageField(required=True, help_text="تصویر ارسالی برای تحلیل چهره/کیفیت")



class StoryRequestSerializer(serializers.Serializer):
    external_user_id = serializers.IntegerField(required=True)
    external_audio_id = serializers.IntegerField(required=True)
    image_id = serializers.IntegerField(required=True)
    
    # تغییر required=False و اجازه دادن به مقادیر خالی
    user_text = serializers.CharField(
        max_length=300, 
        required=False, 
        allow_blank=True, 
        allow_null=True, 
        help_text="متن کوتاه و اختیاری ارسالی کاربر"
    )