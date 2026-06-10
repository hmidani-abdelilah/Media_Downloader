# path_ffmpeg.py
# path_ffmpeg.py

import subprocess  
import os 
import platform 
from utils import resource_path  
from functools import lru_cache

CURRENT_PLATFORM = platform.system() 
FFMPEG_TIMEOUT = 5

@lru_cache(maxsize=1)
def scan_entire_c_drive():
    """بحث شامل في كامل القرص C عن ملف ffmpeg.exe (الحل الأخير)"""
    print("Searching for ffmpeg.exe on C: drive... Please wait.")
    # تجنب الفحص الذاتي أو الغوص في مجلدات النظام الثقيلة لربح الوقت
    for root, dirs, files in os.walk("C:\\"):
        if "ffmpeg.exe" in files:
            found_path = os.path.join(root, "ffmpeg.exe")
            print(f"Success! Found ffmpeg via deep scan at: {found_path}")
            return [found_path,root]
    return None

def ffmpeg_find_path():
    """تبحث عن مسار ffmpeg وتعيد المسار الشغال أو None"""
    if CURRENT_PLATFORM == "Windows": 
        # 1. التحقق من المسار المحلي داخل مجلد البرنامج
        local_path = resource_path(os.path.join("ffmpeg", "bin", "ffmpeg.exe"))
        if os.path.exists(local_path):  
            return local_path 
        
        # 2. التحقق إذا كان معرفاً في متغيرات البيئة PATH للنظام
        try:
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  timeout=FFMPEG_TIMEOUT)
            if res.returncode == 0:
                return "ffmpeg"  
        except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        PermissionError,
        OSError,) as e:
            #print(f"Error on func ffmpeg_find_path is {e} old is pass")
            pass
        # 3. التحقق من المسار الافتراضي الشائع في القرص C
        common_path = r"C:\ffmpeg\bin\ffmpeg.exe"
        if os.path.exists(common_path):
            return common_path
        
            
        # 4. الحل الأخير: البحث التلقائي في كامل الهارد ديسك C
        deep_found_path = scan_entire_c_drive()
        if deep_found_path:
            #print(deep_found_path[1])
            try:
                res0 = subprocess.run([deep_found_path[0], "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  timeout=FFMPEG_TIMEOUT)
                #print(f"tested path prob {deep_found_path[1]+"\\ffprobe.exe"}")
                res1 = subprocess.run([deep_found_path[1]+"\\ffprobe.exe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  timeout=FFMPEG_TIMEOUT)
                if res0.returncode == 0 and res1.returncode == 0:
                    #print("passsssssssssssssssssssssssssed")
                    return deep_found_path[0]
            except:
                #print("currapted exe ffmpeg ffprob..................")
                return deep_found_path[0]
            
        #print("ERROR: ffmpeg.exe could not be found anywhere on this system.")
        return None
    else:
        # لأنظمة لينكس وماك الاعتماد الافتراضي على PATH
        return "ffmpeg"  
