# استفاده از نسخه سبک و رسمی پایتون
FROM python:3.10-slim

# تنظیم متغیرهای محیطی برای جلوگیری از تولید فایل‌های اضافی پایتون و نمایش سریع لاگ‌ها
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ایجاد دایرکتوری کاری در کانتینر
WORKDIR /app

# نصب وابستگی‌های سیستمی مورد نیاز برای پردازش صوت (ضروری برای librosa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن فایل نیازمندی‌ها و نصب پکیج‌های پایتون
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# کپی کردن کل کدهای پروژه به داخل کانتینر
COPY . /app/