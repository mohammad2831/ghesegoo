from django.contrib import admin
from django.utils.html import format_html
from .models import VoiceProfile

@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    # ستون‌هایی که در لیست کلی نمایش داده می‌شوند
    list_display = ('id', 'external_user_id','external_audio_id', 'status', 'created_at')
    
    # فیلترهای نوار سمت راست
    list_filter = ('status', 'created_at')
    
    # فیلد جستجو (جستجو بر اساس آیدی کاربر سرور اصلی)
    search_fields = ('external_user_id', 'id')
    
    # فیلدهایی که ادمین نباید به صورت دستی تغییر دهد
    readonly_fields = ('id', 'created_at', 'updated_at','rejection_reason')
    
    # گروه‌بندی فیلدها در صفحه جزئیات هر رکورد
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('id', 'external_user_id', 'status')
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'updated_at')
        }),
    )

