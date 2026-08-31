import subprocess  
import os 
import platform 
from utils import resource_path  

CURRENT_PLATFORM = platform.system() 

def scan_entire_c_drive():
    """بحث شامل في كامل القرص C عن ملف ffmpeg.exe (الحل الأخير)"""
    print("Searching for ffmpeg.exe on C: drive... Please wait.")
    # تجنب الفحص الذاتي أو الغوص في مجلدات النظام الثقيلة لربح الوقت
    for root, dirs, files in os.walk("C:\\"):
        if "ffmpeg.exe" in files:
            found_path = os.path.join(root, "ffmpeg.exe")
            print(f"Success! Found ffmpeg via deep scan at: {found_path}")
            return found_path
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
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return "ffmpeg"  
        except FileNotFoundError:
            pass
            
        # 3. التحقق من المسار الافتراضي الشائع في القرص C
        common_path = r"C:\ffmpeg\bin\ffmpeg.exe"
        if os.path.exists(common_path):
            return common_path
            
        # 4. الحل الأخير: البحث التلقائي في كامل الهارد ديسك C
        deep_found_path = scan_entire_c_drive()
        if deep_found_path:
            return deep_found_path
            
        print("ERROR: ffmpeg.exe could not be found anywhere on this system.")
        return None
    else:
        # لأنظمة لينكس وماك الاعتماد الافتراضي على PATH
        return "ffmpeg"  

def check_ffmpeg_installed():
    """تتحقق من عمل ffmpeg بنسبة 100% وتعيد True أو False"""
    # استدعاء دالة البحث لجلب أفضل مسار متاح
    target_path = ffmpeg_find_path()
    
    if not target_path:
        return False
        
    try:
        # فحص المسار المستخرج للتأكد من أنه يعمل ويستجيب للأوامر
        res = subprocess.run([target_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False
