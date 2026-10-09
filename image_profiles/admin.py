from django.contrib import admin
from .models import ImageProfile

@admin.register(ImageProfile)
class ImageProfileAdmin(admin.ModelAdmin):
    # ستون‌های نمایشی در لیست کلی (بدون پیش‌نمایش تصویر)
    list_display = ('id', 'image_id', 'ai_analysis_text')
    


    # جلوگیری از حذف دستی رکوردها توسط ادمین
    def has_delete_permission(self, request, obj=None):
        return False