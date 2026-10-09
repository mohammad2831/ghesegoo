import numpy as np
import librosa

class AudioValidator:

    def __init__(self, audio_path):
        self.audio_path = audio_path
        self.audio_array = None
        self.sr = None
        self.duration = None

    def load_audio(self):
        """بارگذاری فایل و محاسبه طول زمان اولیه"""
        self.audio_array, self.sr = librosa.load(self.audio_path, sr=None, mono=True)
        self.duration = len(self.audio_array) / self.sr

    def check_duration(self, min_duration=5.0, max_duration=30.0):
        if self.duration < min_duration:
            return False, f"Audio is too short (Duration = {self.duration:.1f}s < {min_duration}s)."
        if self.duration > max_duration:
            return False, f"Audio is too long (Duration = {self.duration:.1f}s > {max_duration}s)."
        return True, "Duration is optimal."

    def check_rms(self, min_rms_threshold=0.04):
        rms = np.sqrt(np.mean(self.audio_array**2))
        if rms < min_rms_threshold:
            return False, f"Audio overall energy is too low (RMS = {rms:.4f} < {min_rms_threshold})."
        return True, "RMS energy is sufficient."

    def check_peak(self, upper_threshold=0.99, lower_threshold=0.1):
        peak = np.max(np.abs(self.audio_array))
        if peak >= upper_threshold:
            return False, f"Audio is clipping/distorted (Peak = {peak:.3f} >= {upper_threshold})."
        if peak < lower_threshold:
            return False, f"Audio is too quiet (Peak = {peak:.3f} < {lower_threshold})."
        return True, "Peak level is optimal."

    def run_pipeline(self):
        """
        اجرای متوالی تمام تست‌ها.
        در صورت موفقیت تمام تست‌ها: (True, "پیام موفقیت", متادیتا) 
        در صورت شکست در هر مرحله: (False, "دلیل شکست", {})
        """
        try:
            self.load_audio()
        except Exception as e:
            return False, f"Error loading file: {str(e)}", {}

        # لیست توابعی که باید به ترتیب اجرا شوند
        validations = [
            self.check_duration,
            self.check_rms,
            self.check_peak
        ]

        for validation_func in validations:
            is_valid, message = validation_func()
            # اگر تستی رد شد، بلافاصله پردازش را متوقف کن و دلیل را برگردان
            if not is_valid:
                return False, message, {}

        # اگر همه تست‌ها پاس شد، اطلاعات مفید را برگردان
        metadata = {
            "duration": self.duration,
            "sample_rate": self.sr
        }
        return True, "Accepted: File passed all quality checks.", metadata