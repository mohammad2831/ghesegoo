from django.contrib import admin
from .models import GeneratedStory

@admin.register(GeneratedStory)
class GeneratedStoryAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'external_user_id', 'image_id', 'status', 'has_audio', 'created_at_display')
    list_filter = ('status', 'image_id')
    search_fields = ('external_user_id', 'id')
    
    # جلوگیری از دستکاری دستی خروجی‌های هوش مصنوعی
    readonly_fields = ('id', 'generated_text', 'generated_audio', 'error_message', 'created_at', 'updated_at')

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'آیدی داستان'

    def has_audio(self, obj):
        return bool(obj.generated_audio)
    has_audio.boolean = True
    has_audio.short_description = 'صوت دارد؟'

    def created_at_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    created_at_display.short_description = 'تاریخ ایجاد'

    fieldsets = (
        ('اطلاعات درخواست کاربر', {
            'fields': ('id', 'external_user_id', 'image_id', 'user_prompt')
        }),
        ('وضعیت سیستم', {
            'fields': ('status', 'error_message', 'created_at', 'updated_at')
        }),
        ('خروجی مدل‌های هوش مصنوعی', {
            'fields': ('generated_text', 'generated_audio')
        }),
    )