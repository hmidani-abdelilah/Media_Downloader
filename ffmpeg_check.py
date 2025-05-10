# ffmpeg_check.py

import subprocess  # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون

def check_ffmpeg_installed():
    try:
        # محاولة تشغيل الأمر 'ffmpeg --help' للتحقق مما إذا كانت الأداة مثبتة
        result = subprocess.run(['ffmpeg', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # إذا كانت القيمة المرجعة (returncode) تساوي 0 فهذا يعني أن الأمر نجح
        if result.returncode == 0:
            return True  # FFmpeg مثبت
        else:
            return False  # FFmpeg غير مثبت (قد توجد مشكلة أخرى)
    except FileNotFoundError:
        # هذا الاستثناء يتم التقاطه إذا لم يتم العثور على الأمر 'ffmpeg' أساساً
        return False  # FFmpeg غير مثبت أو غير موجود في PATH
