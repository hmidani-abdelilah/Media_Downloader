# ffmpeg_check.py

import subprocess  # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون
from utils import resource_path  # استيراد الدالة resource_path من ملف utils
import os # استيراد مكتبة التعامل مع نظام الملفات
import platform # استيراد مكتبة platform لمعرفة نظام التشغيل الحالي

ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")  # تحديد مسار ffmpeg في المجلد المحلي
current_platform = platform.system() # الحصول على نظام التشغيل الحالي

# دالة للتحقق مما إذا كان FFmpeg مثبتًا ويعمل بشكل صحيح
def check_ffmpeg_installed():
    if current_platform == "Windows": # التحقق إذا كان النظام ويندوز
        if os.path.exists(resource_path("ffmpeg/bin/ffmpeg.exe")) or os.path.exists("ffmpeg.exe"): # التحقق من وجود ffmpeg في المسار المحلي أو في PATH
            
            # محاولة تشغيل 'ffmpeg --help' من المسار المحلي
            result = subprocess.run([ffmpeg_path, '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # التحقق من نتيجة التشغيل
            if result.returncode == 0:
                return True  # FFmpeg من المسار المحلي يعمل بشكل صحيح
            else:
                # محاولة تشغيل 'ffmpeg.exe --help' من النظام (PATH)
                result = subprocess.run(["ffmpeg.exe", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # التحقق من نتيجة التشغيل
                if result.returncode == 0:
                    return True  # FFmpeg مثبت في النظام ويعمل بشكل صحيح
                else:
                    return False  # لم يعمل FFmpeg من المسار المحلي أو النظام (قد تكون هناك مشكلة)
    elif current_platform == "Linux" or current_platform == "Darwin":
        # محاولة تشغيل 'ffmpeg --help' من النظام
        try:
            result = subprocess.run(["ffmpeg", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                return True  # FFmpeg مثبت في النظام ويعمل بشكل صحيح
            else:
                return False  # FFmpeg غير مثبت أو يوجد خطأ في النظام
        except FileNotFoundError:
            # إذا لم يتم العثور على 'ffmpeg' في PATH
            return False  # FFmpeg غير مثبت في النظام أو غير موجود في PATH
        except Exception:
            # التقاط أي استثناءات أخرى قد تحدث
            return False
    else:       
        return False  # في حالة عدم تحقق أي من الشروط أعلاه، نعتبر FFmpeg غير مثبت
