import subprocess
import os
import platform
from utils import resource_path  # استيراد الدالة resource_path من ملف utils

def check_ffmpeg_installed():
    current_platform = platform.system()
    # تأكد أن الدالة ترجع المسار الصحيح سواء كنت تشغل السكريبت أو بعد تحويله لـ EXE
    # ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")
    ffmpeg_path = os.path.join("ffmpeg", "bin", "ffmpeg.exe") # مثال للمسار
    print(ffmpeg_path)
    if current_platform == "Windows":
        # الحالة 1: البحث في المجلد المحلي أولاً
        if os.path.exists(ffmpeg_path):
            try:
                res = subprocess.run([ffmpeg_path, "-version"], capture_output=True)
                if res.returncode == 0: return True
            except: pass

        # الحالة 2: إذا لم يوجد محلياً أو فشل، نبحث في النظام (PATH)
        try:
            res = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            return res.returncode == 0
        except FileNotFoundError:
            return False

    # الأنظمة الأخرى (Linux / Mac)
    else:
        try:
            res = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            return res.returncode == 0
        except FileNotFoundError:
            return False
