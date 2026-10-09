from django.db import models

class ImageProfile(models.Model):
    image_id = models.IntegerField(unique=True, help_text="شناسه عکس (از ۱ تا ۱۲)")
    ai_analysis_text = models.TextField(help_text="متن تحلیلی آماده برای استفاده در پرامپت")
    
    def __str__(self):
        return f"Image {self.image_id}"