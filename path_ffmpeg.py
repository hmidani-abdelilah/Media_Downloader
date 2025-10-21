# path_ffmpeg.py

# تحديد مسار ffmpeg بناءً على نظام التشغيل
import subprocess  # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون
from utils import resource_path  # استيراد الدالة resource_path من ملف utils
import os # استيراد مكتبة التعامل مع نظام الملفات
import platform # استيراد مكتبة platform لمعرفة نظام التشغيل الحالي

current_platform = platform.system() # الحصول على نظام التشغيل الحالي
ffmpeg_path = resource_path("ffmpeg/bin/ffmpeg.exe")  # تحديد مسار ffmpeg في المجلد المحلي
def ffmpeg_find_path():
    if current_platform == "Windows": # التحقق إذا كان النظام ويندوز
        if os.path.exists(resource_path("ffmpeg/bin/ffmpeg.exe")):  # التحقق من وجود ffmpeg في المسار المحلي
            return resource_path("ffmpeg/bin/ffmpeg.exe") # تحديد مسار ffmpeg في المجلد المحلي 
        else:
            return "ffmpeg.exe"  # إذا لم يكن موجودًا في المجلد المحلي، نفترض أنه في PATH 
    else:
        return "ffmpeg"  # إذا لم يكن موجودًا في المجلد المحلي، نفترض أنه في PATH 