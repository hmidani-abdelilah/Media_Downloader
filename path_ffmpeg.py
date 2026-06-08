# path_ffmpeg.py

import subprocess  
import os 
import platform 
from utils import resource_path  

current_platform = platform.system() 

def ffmpeg_find_path():
    if current_platform == "Windows": 
        # 1. تحديد المسار المحلي الصحيح داخل مجلد البرنامج
        local_path = resource_path(os.path.join("ffmpeg", "bin", "ffmpeg.exe"))
        
        # 2. التحقق إذا كان ffmpeg موجوداً في المسار المحلي
        if os.path.exists(local_path):  
            return local_path 
        
        # 3. إذا لم يكن محلياً، نتحقق إذا كان معرفاً في متغيرات البيئة PATH للنظام
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "ffmpeg"  
        except FileNotFoundError:
            # 4. مسار احتياطي في القرص C إذا فشلت الحلول السابقة
            fallback_path = r"C:\ffmpeg\bin\ffmpeg.exe"
            if os.path.exists(fallback_path):
                return fallback_path
            
            return None # لم يتم العثور عليه
    else:
        # لأنظمة لينكس وماك الاعتماد الافتراضي على PATH
        return "ffmpeg"  
