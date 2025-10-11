#aria2_check.py

import subprocess  # استيراد مكتبة subprocess لتشغيل أوامر النظام من داخل بايثون
from utils import resource_path  # استيراد الدالة resource_path من ملف utils
import os 

ARIA2C_PATH = resource_path("aria2/aria2c.exe")  # تحديد مسار aria2c في المجلد المحلي

def check_aria2_installed():
    # أولاً، تحقق مما إذا كان الملف في المسار المحدد موجودًا
    if os.path.exists(ARIA2C_PATH):
        try:
            # محاولة تشغيل 'aria2c --version' من المسار المحلي
            result = subprocess.run([ARIA2C_PATH, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                return True  # aria2c من المسار المحلي يعمل بشكل صحيح
            else:
                return False  # لم يعمل aria2c من المسار المحلي (قد تكون هناك مشكلة)
        except Exception:
            # في حال حدوث أي استثناء أثناء تشغيل aria2c من المسار المحدد
            return False
    #else:
        #print("aria2c غير موجود في المسار المحلي. التحقق من النظام...")

    # إذا لم يكن موجودًا في المسار المحلي، تحقق إذا كان مثبتًا في النظام
    try:
        # محاولة تشغيل Aria2 من سطر الأوامر للتحقق من وجوده
        # محاولة تشغيل 'aria2c --version' من النظام
        result = subprocess.run(["aria2c", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            return True  # aria2c مثبت في النظام ويعمل بشكل صحيح
        else:
            return False  # aria2c غير مثبت أو يوجد خطأ في النظام
    except FileNotFoundError:
        # إذا لم يتم العثور على 'aria2c' في PATH
        return False  # aria2c غير مثبت في النظام أو غير موجود في PATH
    except Exception:
        # التقاط أي استثناءات أخرى قد تحدث
        return False



