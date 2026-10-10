# api_gateway/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from voice_profiles.tasks import validate_voice_profile_task # ایمپورت تسک
from story_engine.tasks import generate_story_text_task

from .permissions import IsMainServer
from .serializers import GatewayProfileUploadSerializer, GatewayImageSelectionSerializer, StoryRequestSerializer

# فراخوانی مدل‌ها و تسک‌ها از اپلیکیشن‌های پردازشی
from voice_profiles.models import VoiceProfile
from image_profiles.models import ImageProfile
from story_engine.models import GeneratedStory
#from image_analysis.tasks import process_image_profile_task
#from voice_profiles.tasks import process_voice_profile_task
#from voice_conversion.models import ConversionJob
#from voice_conversion.tasks import process_voice_conversion_task

from django.db import transaction 


class ImageSelectionGatewayView(APIView):
    """ دریافت شناسه تصویر انتخاب شده توسط کاربر """
    
    permission_classes = [IsMainServer]
    # نیازی به پارسرهای فایل (MultiPartParser) نیست چون فقط یک عدد دریافت می‌کنیم

    def post(self, request):
        serializer = GatewayImageSelectionSerializer(data=request.data)
        
        if serializer.is_valid():
            ext_user_id = serializer.validated_data['external_user_id']
            img_id = serializer.validated_data['image_id']
     
            
            return Response({
                "message": "شناسه تصویر با موفقیت دریافت و ثبت شد.",
                "selected_image_id": img_id
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ProfileUploadGatewayView(APIView):
    """Receive user base audio and push to verification queue"""
    permission_classes = [IsMainServer]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = GatewayProfileUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            ext_user_id = serializer.validated_data['external_user_id']
            ext_audio_id = serializer.validated_data['external_audio_id']
            audio = serializer.validated_data['audio_file']

            # ۱. بررسی اینکه آیا این آیدی صوتی از قبل در دیتابیس هوش مصنوعی وجود دارد یا خیر
            existing_profile = VoiceProfile.objects.filter(external_audio_id=ext_audio_id).first()

            if existing_profile:
                # اگر فایل قبلا تایید شده است، نیازی به اعتبارسنجی و ذخیره مجدد نیست
                if existing_profile.status == 'approved':
                    return Response({
                        "message": "این صوت قبلاً تایید شده است و نیازی به اعتبارسنجی مجدد ندارد.",
                        "profile_id": str(existing_profile.id),
                        "status": "already_approved"
                    }, status=status.HTTP_200_OK)
                
                # اگر فایل هنوز در صف بررسی است
                elif existing_profile.status == 'pending':
                    return Response({
                        "message": "این صوت در حال حاضر در صف پردازش قرار دارد.",
                        "profile_id": str(existing_profile.id),
                        "status": "processing"
                    }, status=status.HTTP_202_ACCEPTED)
                
                # اگر فایل قبلی به دلیل کیفیت پایین رد شده بود، فایل جدید را جایگزین می‌کنیم
                else:
                    existing_profile.audio_file = audio
                    existing_profile.status = 'pending'
                    existing_profile.save()
                    validate_voice_profile_task.delay(existing_profile.id)
                    
                    return Response({
                        "message": "فایل جدید جایگزین نمونه رد شده قبلی شد و به صف بررسی رفت.",
                        "profile_id": str(existing_profile.id),
                        "status": "re_evaluating"
                    }, status=status.HTTP_202_ACCEPTED)

            # ۲. اگر آیدی کاملاً جدید بود، رکورد جدید می‌سازیم
            profile = VoiceProfile.objects.create(
                external_user_id=ext_user_id,
                external_audio_id=ext_audio_id, # فیلد جدید اضافه شده در مدل
                audio_file=audio,
                status='pending'
            )
            
            # ارسال به صف ورکر سلری برای بررسی نویز، طول و کیفیت
            validate_voice_profile_task.delay(profile.id)

            return Response({
                "message": "فایل صوتی با موفقیت دریافت و در سیستم ذخیره شد.",
                "profile_id": str(profile.id),
                "saved_path": profile.audio_file.name
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoryGenerationGatewayView(APIView):
    """ دریافت اطلاعات برای شروع تولید داستان و تبدیل به صدا """
    
    permission_classes = [IsMainServer]

    def post(self, request):
        serializer = StoryRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            ext_user_id = serializer.validated_data['external_user_id']
            img_id = serializer.validated_data['image_id']
            user_text = serializer.validated_data.get('user_text', '')

            # ساخت رکورد در دیتابیس
            story_record = GeneratedStory.objects.create(
                external_user_id=ext_user_id,
                image_id=img_id,
                user_prompt=user_text,
                status='pending'
            )

            # تغییر مهم: شلیک تسک به سلری، فقط پس از تایید نهایی ذخیره در دیتابیس
            transaction.on_commit(
                lambda: generate_story_text_task.delay(str(story_record.id))
            )

            # پاسخ فوری به سرور اصلی جانگو
            return Response({
                "message": "درخواست دریافت شد.",
                "story_id": str(story_record.id)
            }, status=status.HTTP_202_ACCEPTED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)