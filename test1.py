import subprocess  
import os 
import platform 
from utils import resource_path  
from functools import lru_cache, wraps
import time 




CURRENT_PLATFORM = platform.system() 

FFMPEG_TIMEOUT = 5 

def calculate_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"Function '{func.__name__}' took {end - start:.6f} seconds")
        return result
    return wrapper



def monitor_and_clear_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Check if the function actually has a cache
        if hasattr(func, "cache_info"):
            print(f"--- [Cache Monitor: {func.__name__}] ---")
            print(f"Cache BEFORE execution : {func.cache_info()}")
            
            # 2. Clear the cache
            func.cache_clear()
            print("Cache has been cleared.")
            print(f"Cache BEFORE execution : {func.cache_info()}")
        else:
            print(f"Warning: {func.__name__} does not have an active cache decorator.")

        # 3. Execute the function and save the result
        result = func(*args, **kwargs)

        # 4. View the cache after execution
        if hasattr(func, "cache_info"):
            print(f"Cache AFTER execution  : {func.cache_info()}")
            print("-" * 40)
            
        return result
        
    return wrapper


@monitor_and_clear_cache
@lru_cache(maxsize=1)
@calculate_time
def scan_entire_c_drive():
    """بحث شامل في كامل القرص C عن ملف ffmpeg.exe (الحل الأخير)"""
    start=time.time
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
            print(f"Error on func ffmpeg_find_path is {e} old is pass")
            
        # 3. التحقق من المسار الافتراضي الشائع في القرص C
        common_path = r"C:\ffmpeg\bin\ffmpeg.exe"
        if os.path.exists(common_path):
            return common_path
        
            
        # 4. الحل الأخير: البحث التلقائي في كامل الهارد ديسك C
        deep_found_path = scan_entire_c_drive()
        if deep_found_path:
            print(deep_found_path[1])
            try:
                res0 = subprocess.run([deep_found_path[0], "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  timeout=FFMPEG_TIMEOUT)
                print(f"tested path prob {deep_found_path[1]+"\\ffprobe.exe"}")
                res1 = subprocess.run([deep_found_path[1]+"\\ffprobe.exe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  timeout=FFMPEG_TIMEOUT)
                if res0.returncode == 0 and res1.returncode == 0:
                    print("passsssssssssssssssssssssssssed")
                    return deep_found_path[0]
            except:
                print("currapted exe ffmpeg ffprob..................")
                return deep_found_path[0]
            
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

print(check_ffmpeg_installed())

#print(ffmpeg_find_path())

