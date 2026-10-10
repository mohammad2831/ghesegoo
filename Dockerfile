# استفاده از ایمیج رسمی PyTorch حاوی درایورهای CUDA
FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# مسیر کش مدل‌های هانگینگ‌فیس
ENV HF_HOME=/app/hf_cache

WORKDIR /app

# نصب ابزارهای سیستمی برای پردازش صوت و بیلد پکیج‌ها
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل نیازمندی‌ها (شما باید requirements هر دو پروژه را در این فایل ادغام کنید)
COPY requirements.txt /app/

# نصب PyTorch با پشتیبانی CUDA (طبق تنظیمات قبلی شما)
RUN pip install --no-cache-dir torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل پروژه
COPY . /app/

# ساخت پوشه‌های ضروری در صورت عدم وجود
RUN mkdir -p /app/media/outputs
RUN mkdir -p /app/hf_cache

EXPOSE 8000