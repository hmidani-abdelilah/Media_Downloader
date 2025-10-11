# ffmpeg_check.py

import subprocess  # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون
from utils import resource_path  # استيراد الدالة resource_path من ملف utils
import os

ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")  # تحديد مسار ffmpeg في المجلد المحلي

def check_ffmpeg_installed():
    # أولاً، تحقق مما إذا كان الملف في المسار المحدد موجودًا
    if os.path.exists(ffmpeg_path):
        try:
            # محاولة تشغيل 'ffmpeg --help' من المسار المحلي
            result = subprocess.run([ffmpeg_path, '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                return True  # FFmpeg من المسار المحلي يعمل بشكل صحيح
            else:
                return False  # لم يعمل FFmpeg من المسار المحلي (قد تكون هناك مشكلة)
        except Exception:
            # في حال حدوث أي استثناء أثناء تشغيل FFmpeg من المسار المحدد
            return False
    else:

        # إذا لم يكن موجودًا في المسار المحلي، تحقق إذا كان مثبتًا في النظام
        try:
            # محاولة تشغيل 'ffmpeg --help' من النظام
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
