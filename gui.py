# ملف gui.py: يحتوي على الفئة الرئيسية لتطبيق تحميل فيديوهات يوتيوب مع واجهة مستخدم رسومية باستخدام مكتبة customtkinter
import sys # لإعادة توجيه الإخراج إلى UTF-8 في حالة عدم دعم sys.stdout أو sys.stderr للكتابة الثنائية
import io # لإنشاء تدفقات نصية ثنائية لتوجيه الإخراج إلى UTF-8
import re # للتعامل مع التعبيرات العادية (غير مستخدم حاليا، لكن قد يكون مفيد في المستقبل لتحليل الروابط أو المدخلات)
import urllib.parse # لتحليل الروابط (غير مستخدم حاليا، لكن قد يكون مفيد في المستقبل لتحليل الروابط أو المدخلات)

# تأكد من أن sys.stdout و sys.stderr يدعمان الكتابة الثنائية (binary) وإلا قم بإنشاء تدفقات نصية ثنائية مع ترميز UTF-8
if sys.stdout is None or not hasattr(sys.stdout, 'buffer'):
    # On crée un flux binaire, puis on l'enveloppe pour le texte
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')

if sys.stderr is None or not hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')

# الآن يمكننا استيراد باقي المكتبات بعد التأكد من أن sys.stdout و sys.stderr يدعمان الكتابة الثنائية
from ssl import Options # للتعامل مع خيارات SSL (غير مستخدم حاليا، لكن قد يكون مفيد في المستقبل لتحسين الأمان عند تحميل الفيديوهات)

import customtkinter as ctk  # استيراد مكتبة واجهة المستخدم المخصصة
from PIL import Image, ImageTk # لتضمين أيقونة للتطبيق مهما كان نوع نظام التشغيل
import tkinter as tk  # استيراد مكتبة tkinter لإنشاء قائمة السياق
from customtkinter import filedialog  # لفتح مربع حوار اختيار الملفات
import CTkFileDialog  # لفتح مربع حوار اختيار المجلدات
from CTkFileDialog.Constants import HOME # مسار مجلد المستخدم الافتراضي
from CTkMessagebox import CTkMessagebox  # لعرض رسائل منبثقة للمستخدم 
from CTkMenuBar import * #  استيراد مكتبة القوائم الافقية 
from downloader import download_video, get_videos_info, get_gpu_encoders, stop_download # استيراد وظائف التحميل
from ffmpeg_check import check_ffmpeg_installed  # للتحقق من تثبيت FFmpeg
from aria2_check import check_aria2_installed # للتحقق من تثبيت Aria2c
import threading  # للتنفيذ المتزامن للمهام
import json  # للتعامل مع ملفات اللغة
import os  # للتعامل مع نظام الملفات
import sys  # للوصول إلى معلومات النظام
from utils import resource_path # لمعالجة مسارات الملفات بشكل صحيح
import subprocess # لتنفيذ أوامر النظام لتحديث الحزم
import ctypes # دوال من نظام التشغيل (Windows API)

from notification import Notifier # لإرسال إشعارات عند اكتمال التحميل   

# from pystray import Icon, Menu, MenuItem # System Tray
import platform # للحصول على معلومات حول نظام التشغيل
from tkinterdnd2 import TkinterDnD, DND_TEXT # لدعم سحب وإفلات الروابط في حقل الإدخال


# pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe
# pyinstaller --onedir --windowed --add-data "languages;languages" --add-data "asset/Icon.ico;asset" --add-data "aria2;aria2" --add-data "ffmpeg;ffmpeg" --icon "asset/Icon.ico" -n MediaDownloader app.py
# pyinstaller --onedir --windowed --collect-all typeguard --collect-all CTkFileDialog --add-data=languages;languages --add-data=asset/Icon.ico;asset  --icon=asset/Icon.ico -n MediaDownloader app.py

# الفئة الرئيسية لتطبيق تحميل فيديوهات يوتيوب مع واجهة مستخدم رسومية
class YouTubeDownloaderApp:
    """
    فئة رئيسية لتطبيق تحميل فيديوهات يوتيوب مع واجهة مستخدم رسومية
    """
    def __init__(self, root, lang_code="en"):
        """
        دالة الإنشاء التي تقوم بتهيئة التطبيق
        
        المعلمات:
            root: نافذة الجذر في Tkinter
            lang_code: رمز اللغة المستخدمة (الافتراضي: الإنجليزية)
        """
        self.root = root # تعيين نافذة الجذر
        self.lang = self.load_language(lang_code) # تحميل ملف اللغة المناسب
        self.lang_code = lang_code # تعيين رمز اللغة الحالي
        self.save_dir = os.path.expanduser("~")  # مجلد المستخدم الافتراضي كمسار حفظ
        self.cookiefile_dir = "\U0001F36A" # مسار ملف cookies 
        self.current_download_thread = None  # خيط التنزيل الحالي
        self.is_downloading = False  # مؤشر على حالة التنزيل

        # Initialize the menu bar
        # --- UI ELEMENTS ---
        # إنشاء شريط القائمة العلوي باستخدام CTkMenuBar من مكتبة customtkinter
        self.menu_bar = CTkMenuBar(master=self.root)
        # Add top-level buttons to the menu bar
        # إضافة زر "خيارات" إلى شريط القائمة وربطه بدالة show_options (غير موجودة حاليا، لكن يمكن إضافتها لاحقا لعرض إعدادات التطبيق)
        self.file_button = self.menu_bar.add_cascade(self.lang.get("options", "Options")) # إضافة زر "خيارات" إلى شريط القائمة
        #self.edit_button = self.menu_bar.add_cascade("Edit")
        # اضافة زر "مساعدة" إلى شريط القائمة وربطه بدالة show_help لعرض رسالة مساعدة للمستخدم
        self.menu_bar.add_cascade(self.lang.get("help", "Help"), command=self.show_help) # إضافة زر "مساعدة" إلى شريط القائمة وربطه بدالة show_help
        
        
        # Create dropdown content
        # إنشاء قائمة منسدلة (Dropdown menu) مرتبطة بزر "خيارات" لعرض خيارات إضافية مثل "التحقق من التحديثات" و "الخروج"
        self.dropdown = CustomDropdownMenu(widget=self.file_button)
        self.dropdown.add_option(option=self.lang.get("check_updates", "Check for Updates"), command=self.run_update)
        self.dropdown.add_separator()
        self.dropdown.add_option(option=self.lang.get("exit", "Exit"), command=self.root.destroy)
        # ربط المفاتيح لتكبير الشاشة والخروج من ملء الشاشة
        self.root.bind("<F11>", self.toggle_fullscreen) # ربط مفتاح F11 لتبديل وضع ملء الشاشة
        self.root.bind("<Escape>", self.exit_fullscreen) # ربط مفتاح Escape للخروج من وضع ملء الشاشة
        
        # تعيين أيقونة التطبيق بناءً على نظام التشغيل لضمان ظهور الأيقونة بشكل صحيح في شريط المهام وقائمة التطبيقات
        if platform.system() == "Windows" :
            # وضع الايقونة في شريط المهام windows 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("media.downloader.app")
            # windows os exe 
            icon_path = self.resource_path(os.path.join("asset", "Icon.ico")) # الحصول على المسار الصحيح للأيقونة
            self.root.iconbitmap(icon_path) # تعيين الأيقونة لنافذة التطبيق (خاص بنظام Windows)
        else:
            # تحميل أيقونة التطبيق من المسار الصحيح
            base_dir = os.path.dirname(os.path.abspath(__file__)) # الحصول على الدليل الأساسي للتطبيق   
            icon_image = Image.open(os.path.join(base_dir,"asset", "Icon.png")) # فتح صورة الأيقونة
            icon_tk = ImageTk.PhotoImage(icon_image) # تحويل الصورة إلى تنسيق يمكن لـ Tkinter استخدامه
            # تعيين الأيقونة لنافذة التطبيق
            self.root.wm_iconphoto(True, icon_tk) # تعيين الأيقونة لنافذة التطبيق (متوافق مع معظم أنظمة التشغيل)

        
        
        # تهيئة متغيرات اللغة والحالة
        self.lang = self.load_language(lang_code) # تحميل ملف اللغة المناسب
        self.lang_code = lang_code # تعيين رمز اللغة الحالي
        self.save_dir = os.path.expanduser("~")  # مجلد المستخدم الافتراضي كمسار حفظ
        self.cookiefile_dir = "\U0001F36A" # مسار ملف cookies 
        self.current_download_thread = None  # خيط التنزيل الحالي
        self.is_downloading = False  # مؤشر على حالة التنزيل
        self.warning_shutdown = None  # حالة رسالة التحذير لإغلاق الحاسوب بعد التحميل

        # إنشاء عناصر واجهة المستخدم
        self.create_widgets()

        # Bind close window event to custom handler
        # ربط حدث إغلاق النافذة بدالة مخصصة للتعامل مع إغلاق التطبيق بشكل صحيح خاصة أثناء وجود عملية تحميل جارية
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    # دالة لإرسال إشعار عند اكتمال التحميل بناءً على نظام التشغيل المستخدم
    def notification(self):
        system = platform.system()

        if system == "Windows":
            from winotify import Notification # Notifications حقيقية ديال Windows pip install winotify
            def show():
                icon_path = os.path.abspath("asset/Icon.ico")
                toast = Notification(
                    app_id="Media Downloader",
                    title="Download Complete",
                    msg="Your video is ready!",
                    icon=icon_path
                )
                toast.show()
            threading.Thread(target=show).start()

        elif system == "Linux" or system == "Darwin": # دعم نظام ماك و لينكس    
            import subprocess
            # test notify-send is insttaled or not
            try:
                # التحقق من وجود الأمر notify-send في النظام عن طريق محاولة تشغيله مع خيار --version لالتقاط أي أخطاء إذا لم يكن مثبتًا
                subprocess.run(["notify-send", "--version"], check=True, capture_output=True)
                notify_send_installed = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                notify_send_installed = False
                # print("Erreur : notify-send n'est pas installé. 'sudo apt install libnotify-bin'")
                # return
            # إذا كان notify-send مثبتًا، استخدمه لإرسال إشعار بسيط. إذا لم يكن مثبتًا، استخدم desktop-notifier كبديل لإرسال إشعار أكثر تعقيدًا.
            if notify_send_installed:
                import subprocess
                import time
                # استخدام notify-send لإرسال إشعار بسيط عند اكتمال التحميل، مع تحديث تدريجي لشريط التقدم في الإشعار لإظهار تقدم التحميل بشكل أكثر تفاعلية. يتم تحديث شريط التقدم من 0% إلى 100% في خطوات من 10% مع تأخير بسيط بين كل تحديث لإعطاء إحساس بالتقدم.
                for i in range(0, 101, 10):
                    subprocess.run([
                        "notify-send",
                        "Download Complete",
                        "Your video is ready!",
                        "-i", os.path.abspath("asset/Icon.png"),
                        "-h", f"int:value:{i}",
                        "-r", "9999"  # replace نفس notification
                    ])
                    time.sleep(0.3)
            else:
                # إذا لم يكن notify-send مثبتًا، استخدم مكتبة desktop-notifier لإرسال إشعار أكثر تعقيدًا عند اكتمال التحميل، مع تضمين صوت الإشعار ومستوى الإلحاح لتوفير تجربة إشعار أفضل للمستخدم.
                import asyncio # لإدارة الإشعارات بشكل غير متزامن باستخدام مكتبة desktop-notifier التي تعتمد على asyncio لإرسال الإشعارات بشكل فعال دون حظر واجهة المستخدم أثناء انتظار إرسال الإشعار.
                from desktop_notifier import DesktopNotifier, Urgency, DEFAULT_SOUND
                notifier = DesktopNotifier(app_name="Media Downloader")
                async def main():
                    await notifier.send(
                        title="Download Complete",
                        message="Your video is ready!",
                        sound=DEFAULT_SOUND,
                        urgency=Urgency.Normal
                        )

                asyncio.run(main())

    # دالة لعرض رسالة مساعدة للمستخدم تحتوي على تعليمات حول كيفية استخدام التطبيق وخيارات التشفير والجودة والسرعة المتاحة، بالإضافة إلى رابط لمزيد من المعلومات على صفحة GitHub الخاصة بالتطبيق.
    def show_help(self):
        """
        عرض رسالة مساعدة للمستخدم
        """
        # help_message = self.lang.get("help_message", "To use this application, enter the media URL, select your desired options, and click the Download button.\nGPU Encoding [ libx264: CPU-based H.264 encoder; best compatibility and quality-to-size ratio but high CPU usage\nlibx265: CPU-based HEVC (H.265) encoder; '50%' better compression than x264 but much slower to encode\nhevc_vaapi: Linux hardware-accelerated HEVC encoder for Intel/AMD GPUs; extremely fast with low CPU impact\nh264_vaapi: Linux hardware-accelerated H.264 encoder for Intel/AMD GPUs; standard for fast Linux video processing\nhevc_qsv: Intel Quick Sync HEVC encoder for Windows/Linux; optimized for Intel iGPUs to provide fast 4K encoding\nh264_qsv: Intel Quick Sync H.264 encoder; high-speed hardware encoding for Intel systems with good stability ] \n[ CRF : Constant Rate Factor between 0-51 \n CRF 0: Lossless (huge files) \n CRF 18: Visually transparent (indistinguishable from source) \n CRF 23: Default (great balance) \n CRF 28: Good for web/mobile (small files, slight quality loss) \n CRF 30-35: You will start seeing 'blocking' (pixelated squares) in dark areas or fast-moving scenes. Fine details (like hair or grass) will look blurry \n CRF 40+: The video becomes very 'muddy.' Colors might look washed out, and the image will look significantly worse than the original  ]\n[ ultrafast: Minimal compression, largest file size, nearly zero CPU impact; best for instant local recording \n superfast: Very low compression, large file size, extremely fast encoding for older hardware \n veryfast: Good balance for live streaming; low CPU usage with acceptable file size \n faster: Slightly better compression than veryfast; ideal for fast downloads on mid-range CPUs \n fast: Slightly better than medium; a good trade-off between encoding speed and file weight \n medium (default): The standard balance; recommended for most general video encoding tasks \n slow: High compression, smaller file size, requires significant CPU power; best for high-quality archiving \n slower: Very high compression, tiny file size, very slow encoding; used for professional master files \n veryslow: Maximum compression, smallest possible file size, extremely slow; only for perfectionists with powerful CPUs ] For more information, visit our GitHub page.\nhttps://github.com/hmidani-abdelilah/Media_Downloader")
        # CTkMessagebox(title=self.lang.get("help", "Help"), message=help_message, icon="info") # عرض رسالة منبثقة للمساعدة
        help_message = self.lang.get("help_message", 
                                        "To use this application, enter the media URL, select your options, and click Download.\n\n"
                                        "--- ENCODERS ---\n"
                                        "• libx264: CPU-based H.264; Best compatibility/quality.\n"
                                        "• libx265: CPU-based HEVC; 50% better compression (slower).\n"
                                        "• hevc_vaapi: Linux hardware HEVC (Intel/AMD); Very fast.\n"
                                        "• h264_vaapi: Linux hardware H.264 (Intel/AMD); Very fast.\n"
                                        "• hevc_qsv: Intel Quick Sync HEVC; Optimized for Intel iGPUs.\n"
                                        "• h264_qsv: Intel Quick Sync H.264; Fast and stable.\n\n"
                                        "--- QUALITY (CRF: 0-51) ---\n"
                                        "• 0: Lossless (Huge files).\n"
                                        "• 18: Visually transparent (High quality).\n"
                                        "• 23: Default (Great balance).\n"
                                        "• 28: Acceptable (Small files, mobile use).\n"
                                        "• 30-35: Visible pixelation (Blurry details).\n"
                                        "• 40+: Very poor quality (Muddy image).\n\n"
                                        "--- PRESETS (Speed vs Compression) ---\n"
                                        "• ultrafast/superfast: Instant encoding, very large files.\n"
                                        "• veryfast/faster: Good for live streaming or mid-range CPUs.\n"
                                        "• medium: Default standard balance.\n"
                                        "• slow/slower: High compression, small files (Needs high CPU).\n"
                                        "• veryslow: Best compression, extremely slow.\n\n"
                                        "For more info: https://github.com/hmidani-abdelilah/Media_Downloader"
                                            )

        CTkMessagebox(title=self.lang.get("help", "Help"), message=help_message, icon="info")
   

    # دالة تحديت الوضع تلقائي ان كانت system 
    def sync_appearance(self):
        # مزامنة وضع المظهر تلقائيًا إذا كان المستخدم قد اختار "System" في قائمة إعدادات المظهر، بحيث يتغير مظهر التطبيق تلقائيًا ليتناسب مع إعدادات النظام (فاتح أو داكن) دون الحاجة إلى إعادة تشغيل التطبيق.
        current_app_mode = ctk.get_appearance_mode().lower()
        if self.appearance_mode_menu.get().lower() != "system" and current_app_mode is not None:
            pass
        elif current_app_mode != self.appearance_mode_menu.get().lower():
            ctk.set_appearance_mode("system")
        # جدولة التحقق التالي بعد 1000 مللي ثانية (1 ثانية) لضمان استمرار مزامنة المظهر مع إعدادات النظام بشكل دوري
        self.root.after(1000, self.sync_appearance)

    # دالة لمعالجة مسارات الملفات بشكل صحيح
    def resource_path(self, relative_path):
        """
        معالجة مسارات الملفات بشكل صحيح سواء عند التشغيل العادي أو عند التجميع إلى ملف تنفيذي
        
        المعلمات:
            relative_path: المسار النسبي للملف المطلوب
            
        الإرجاع:
            المسار المطلق للملف
        """
        try:
            base_path = sys._MEIPASS  # في حالة التشغيل من ملف تنفيذي مجمع
        except Exception:
            base_path = os.path.abspath(".")  # في حالة التشغيل العادي
        return os.path.join(base_path, relative_path)    #full_path = os.path.join(base_path, relative_path)

    # دالة لتحميل ملف اللغة المناسب
    def load_language(self, lang_code):
        """
        تحميل ملف اللغة المناسب
        
        المعلمات:
            lang_code: رمز اللغة المطلوبة
            
        الإرجاع:
            قاموس يحتوي على ترجمات النصوص
        """
        try:
            # فتح ملف اللغة وتحميل البيانات
            with open(self.resource_path(f"languages/{lang_code}.json"), "r", encoding="utf-8") as f:
                lang_data = json.load(f) # تحميل بيانات اللغة من الملف
            return lang_data # إرجاع بيانات اللغة
        except FileNotFoundError:
            #File not found: languages/{lang_code}.json
            # استخدام اللغة الإنجليزية كلغة افتراضية في حالة عدم وجود ملف اللغة المطلوبة
            try:
                # فتح ملف اللغة الإنجليزية وتحميل البيانات
                with open(self.resource_path("languages/en.json"), "r", encoding="utf-8") as f:
                    return json.load(f) # إرجاع بيانات اللغة الإنجليزية
            except:
                return {}  # إرجاع قاموس فارغ في حالة عدم وجود أي ملف لغة

    # دالة لمعالجة روابط يوتيوب واستخراج الرابط المناسب بناءً على ما إذا كانت تحتوي على قائمة تشغيل أم لا، مع تقديم خيار للمستخدم لاختيار ما يريد تحميله (فيديو واحد أو قائمة تشغيل كاملة)
    def process_youtube_url(self,url):
        """
        فحص ما إذا كانت رابط يوتيوب يحتوي على قائمة تشغيل.
        المستخدم يختار بين تحميل فيدو منفرد او  قائمة تشغيل كاملة
        ترجع الرابط المطلوب

        المعلمات:
            url: الرابط المطلوب
        
        Checks if a YouTube URL contains a playlist.
        Prompts the user to choose between downloading the single video or the entire playlist.
        Returns the appropriate clean URL.
        """
        # Parse the provided URL لتحليل الرابط المقدم واستخراج مكوناته المختلفة مثل المسار والمعلمات
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Check if 'list' is one of the URL parameters
        if 'list' in query_params:
            # Prompt the user with CTkMessagebox
            msg = CTkMessagebox(
                title="Playlist Detected", 
                message="This link contains a playlist. What do you want to download?",
                icon="question", 
                option_1="Single Video", 
                option_2="Entire Playlist",
                option_3="Cancel"
            )
            response = msg.get()
            
            if response == "Single Video":
                # Extract just the video part to ignore the playlist
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                    return f"https://www.youtube.com/watch?v={video_id}"
                elif "youtu.be" in parsed_url.netloc:
                    # Handle shortened youtu.be links
                    return f"https://youtu.be{parsed_url.path}"
                else:
                    return url # Fallback
                    
            elif response == "Entire Playlist":
                # Extract just the playlist ID and build a clean playlist link
                #playlist_id = query_params['list'][0]
                #return f"https://www.youtube.com/playlist?list={playlist_id}"
                return url
                
            else:
                # The user pressed Cancel or closed the message box
                return None

        # If it's just a normal video without a playlist, return the original URL
        return url

    # دالة لإنشاء عناصر واجهة المستخدم الرسومية 
    def create_widgets(self):
        """
        إنشاء وتنظيم عناصر واجهة المستخدم الرسومية
        """
        # Loading Frame (Hidden by default)
        # إنشاء إطار تحميل (Loading Frame) يحتوي على رسالة للمستخدم وشريط تقدم، ويتم إخفاؤه افتراضيًا ويظهر فقط أثناء تحديث الحزم أو أثناء عمليات التحميل التي تستغرق وقتًا طويلاً لإعلام المستخدم بأن التطبيق يعمل على مهمة ما.
        self.loading_frame = ctk.CTkFrame(self.root) # إنشاء إطار تحميل (Loading Frame) يحتوي على رسالة للمستخدم وشريط تقدم، ويتم إخفاؤه افتراضيًا ويظهر فقط أثناء تحديث الحزم أو أثناء عمليات التحميل التي تستغرق وقتًا طويلاً لإعلام المستخدم بأن التطبيق يعمل على مهمة ما.
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Updating dependencies, please wait...") # رسالة للمستخدم تظهر أثناء تحديث الحزم أو أثناء عمليات التحميل التي تستغرق وقتًا طويلاً لإعلام المستخدم بأن التطبيق يعمل على مهمة ما.
        self.loading_label.pack(pady=5)
        self.current_package_label = ctk.CTkLabel(self.loading_frame, text="") # رسالة تظهر اسم الحزمة الحالية التي يتم تحديثها أثناء عملية تحديث الحزم، لتوفير معلومات أكثر تفصيلاً للمستخدم حول تقدم التحديث. يتم تحديث نص هذه الرسالة ديناميكيًا أثناء عملية التحديث لعرض اسم الحزمة التي يتم تثبيتها أو تحديثها حاليًا.
        self.current_package_label.pack(pady=2)
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, orientation="horizontal", mode="determinate") # شريط تقدم أفقي بنمط محدد (determinate) لعرض تقدم عملية تحديث الحزم أو التحميل، حيث يتم تحديث قيمة هذا الشريط ديناميكيًا لتمثيل نسبة التقدم في العملية الجارية. يتم إخفاء هذا الإطار افتراضيًا ويظهر فقط أثناء عمليات التحديث أو التحميل التي تستغرق وقتًا طويلاً لإعلام المستخدم بأن التطبيق يعمل على مهمة ما.
        self.progress_bar.set(0) # تعيين قيمة شريط التقدم إلى 0 في البداية، مما يعني أن العملية لم تبدأ بعد. سيتم تحديث هذه القيمة ديناميكيًا أثناء عملية التحديث أو التحميل لتمثيل نسبة التقدم في العملية الجارية.
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.loading_frame.pack_forget() # إخفاء الإطار افتراضيًا
        
        # إنشاء الإطارات الرئيسية
        self.top_frame = ctk.CTkFrame(self.root) # إطار علوي لإعدادات المظهر واللغة
        self.top_frame.pack(fill="x", padx=10, pady=5) # تعبئة العرض بالكامل مع حواف
        
        self.main_frame = ctk.CTkFrame(self.root) # الإطار الرئيسي لبقية عناصر الواجهة
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5) # تعبئة العرض والارتفاع بالكامل مع حواف
        
        # ===== قسم إعدادات المظهر في الأعلى =====
        self.appearance_mode_label = ctk.CTkLabel(self.top_frame, text=self.lang.get("appearance_mode", "Theme:")) # تسمية إعدادات المظهر
        self.appearance_mode_label.pack(side="left", padx=5) # تعبئة على اليسار مع حواف
        
        # قائمة منبثقة لاختيار وضع المظهر (فاتح/داكن/نظام)     
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode_event
        ) # إنشاء قائمة منبثقة لاختيار وضع المظهر (فاتح/داكن/نظام) وربطها بدالة change_appearance_mode_event لتغيير مظهر التطبيق بناءً على اختيار المستخدم
        self.appearance_mode_menu.set(ctk.get_appearance_mode().capitalize()) # تعيين القيمة الافتراضية لقائمة وضع المظهر بناءً على الوضع الحالي للتطبيق (System, Light, Dark) مع تحويلها إلى صيغة تبدأ بحرف كبير لتتناسب مع خيارات القائمة
        self.appearance_mode_menu.pack(side="left", padx=5) # تعبئة على اليسار مع حواف
        
       
        # ===== قسم إعدادات اللغة =====
        self.language_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["en", "ar", "fr"],  # اللغات المدعومة: الإنجليزية والعربية والفرنسية
            command=self.change_language
        ) # إنشاء قائمة منبثقة لاختيار اللغة وربطها بدالة change_language لتغيير لغة التطبيق بناءً على اختيار المستخدم
        self.language_menu.set(self.lang_code) # تعيين اللغة الافتراضية
        self.language_menu.pack(side="right", padx=5) # تعبئة على اليمين مع حواف
        
        # تسمية إعدادات اللغة
        
        self.language_label = ctk.CTkLabel(self.top_frame, text=self.lang.get("language", "Language:")) # تسمية إعدادات اللغة
        self.language_label.pack(side="right", padx=5) # تعبئة على اليمين مع حواف
        
        # ===== عنوان التطبيق =====
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text=self.lang.get("title", "Media Downloader"), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=10) # تعبئة مع حواف عمودية
        
        # ===== قسم إدخال رابط الفيديو =====
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=20, pady=5)
        # حقل إدخال رابط الفيديو
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            justify='center', 
            placeholder_text=self.lang.get("enter_url", "Enter Media URL"), 
            width=400
        )
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True) # تعبئة على اليسار مع حواف وتوسيع
        # Enable drag-and-drop for URLs (TkinterDnD2)
        # محاولة تمكين ميزة السحب والإفلات للروابط في حقل الإدخال باستخدام مكتبة TkinterDnD2، بحيث يمكن للمستخدم سحب رابط الفيديو مباشرة إلى الحقل بدلاً من نسخه ولصقه، مما يسهل عملية إدخال الروابط ويجعلها أكثر تفاعلية وسهولة في الاستخدام.
        try:
            native_entry = self.url_entry._entry
            native_entry.drop_target_register(DND_TEXT)
            native_entry.dnd_bind('<<Drop>>', self.handle_drop)
        except Exception:
            pass

        
        # إنشاء قائمة منبثقة (Popup menu) بدون حافة علوية
        self.menu = tk.Menu(self.url_frame, tearoff=0)

        # إضافة عنصر "قص" إلى القائمة وربطه بالدالة copy_to_clipboard
        self.menu.add_command(label=self.lang.get("cut", "Cut"),command=self.copy_to_clipboard)  # إضافة أمر "قص" للقائمة
        # إضافة عنصر "لصق" إلى القائمة وربطه بالدالة paste
        self.menu.add_command(label=self.lang.get("paste", "Paste"), command=self.paste)  # إضافة أمر "لصق" للقائمة
        # إضافة عنصر "مسح" الى القائمة و ربطه بالدالة clear_url
        self.menu.add_command(label=self.lang.get("clear", "clear"),command=self.clear_url)   # إضافة أمر "مسح" للقائمة
        # ربط حدث النقر بزر الفأرة الأيمن (الزر رقم 3) بالحقل لعرض القائمة
        self.url_entry.bind("<Button-3>", self.show_menu)

       # زر المسح
        self.clear_button = ctk.CTkButton(
            self.url_frame,
            text=self.lang.get("clear", "Clear"),
            command=self.clear_url
        )
        self.clear_button.pack(side="right", padx=5) # تعبئة على اليمين مع حواف
        
        # ===== قسم الإعدادات =====
        self.settings_frame = ctk.CTkFrame(self.main_frame) # إطار لإعدادات التحميل
        self.settings_frame.pack(fill="x", padx=20, pady=10) # تعبئة العرض بالكامل مع حواف
        
        # إعدادات نوع الملف
        self.filetype_label = ctk.CTkLabel(self.settings_frame, text="Format:") # تسمية إعدادات نوع الملف
        self.filetype_label.grid(row=0, column=0, padx=5, pady=5) # وضع في الشبكة
        
        self.file_type = ctk.StringVar(value="best") # متغير لتخزين نوع الملف المختار
        # قائمة منبثقة لاختيار نوع الملف
        self.type_menu = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=["best","mp4", "mkv" , "avi", "flv" , "webm" , "mp3", "aac", "flac", "wav", "opus", "alac", "m4a", "ogg"],  # أنواع الملفات المتاحة
            variable=self.file_type
        )
        self.type_menu.grid(row=0, column=1, padx=5, pady=5) # وضع في الشبكة
        
        # إعدادات الجودة
        self.quality_label = ctk.CTkLabel(self.settings_frame, text="Quality:")
        self.quality_label.grid(row=0, column=2, padx=5, pady=5)
        
        self.quality = ctk.StringVar(value="medium") # متغير لتخزين مستوى الجودة المختار
        # قائمة منبثقة لاختيار مستوى الجودة
        self.quality_menu = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=["low", "medium", "high"],  # مستويات الجودة المتاحة
            variable=self.quality
        )
        self.quality_menu.grid(row=0, column=3, padx=5, pady=5)
        
        # خيار تحميل الترجمة
        self.subtitles = ctk.BooleanVar(value=False)
        # مربع اختيار لتحميل الترجمة
        self.sub_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("download_subtitles", "Download Subtitles"), 
            variable=self.subtitles
        )
        self.sub_checkbox.grid(row=0, column=4, padx=5, pady=5)
        
        # خيار تحميل بادات Aria2c
        self.aria2c = ctk.BooleanVar(value=False)
        # مربع اختيار لتحميل باستخدام Aria2c
        self.aria2_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("use_aria2", "Download with aria2"), 
            variable=self.aria2c
        )
        self.aria2_checkbox.grid(row=0, column=5, padx=5, pady=5)

        # اغلاق البرنامج بعد اكتمال التحميل 
        self.close_after_download = ctk.BooleanVar(value=False)
        self.close_after_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("close_after_download", "Close after download"), 
            variable=self.close_after_download
        )
        self.close_after_checkbox.grid(row=0, column=6, padx=5, pady=5)

        # اطفاء الحاسوب بعد اكتمال التحميل 
        self.shutdown_after_download = ctk.BooleanVar(value=False)
        self.shutdown_after_download_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("shutdown_after_download", "Shutdown after download"), 
            variable=self.shutdown_after_download
        )
        self.shutdown_after_download_checkbox.grid(row=0, column=7, padx=5, pady=5)

        # ===== قسم اختيار مجلد الحفظ =====
        self.directory_frame = ctk.CTkFrame(self.main_frame)
        self.directory_frame.pack(fill="x", padx=20, pady=5)
        # تسمية مجلد الحفظ الحالي
        self.directory_label = ctk.CTkLabel(self.directory_frame, text=f"Directory: {self.save_dir}")
        self.directory_label.pack(side="left", padx=5, fill="x", expand=True)
        # زر لاختيار مجلد الحفظ
        self.select_button = ctk.CTkButton(
            self.directory_frame, 
            text=self.lang.get("select_directory", "Select Directory"), 
            command=self.select_directory
        )
        self.select_button.pack(side="right", padx=5)

        # ===== قسم اختيار ملف COOKIES =====
        self.cookies_frame = ctk.CTkFrame(self.main_frame)
        self.cookies_frame.pack(fill="x", padx=20, pady=5)
        # تسمية ملف COOKIES الحالي
        self.cookiefile_label = ctk.CTkLabel(self.cookies_frame, text=f"File PATH: {self.cookiefile_dir}")
        self.cookiefile_label.pack(side="left", padx=5, fill="x", expand=True)
        # زر لاختيار ملف COOKIES
        self.select_cookies_button = ctk.CTkButton(
            self.cookies_frame, 
            text=self.lang.get("select_file", "Select Cookies File"), 
            command=self.select_file
        )
        self.select_cookies_button.pack(side="right", padx=5)

        # ----------------- دعم GPU -----------------
        self.gpu_fram = ctk.CTkFrame(self.main_frame)
        self.gpu_fram.pack(fill="x",padx=20, pady=5)
        # 
        self.gpu_label = ctk.CTkLabel(self.gpu_fram, text=self.lang.get("gpu_encoding", "GPU Encoding GPU/CPU :")) # تسمية إعدادات ترميز GPU
        self.gpu_label.grid(row=1, column=0, padx=10, pady=10, sticky="NSEW")
        # متغير لتخزين مشفر الفيديو المختار
        self.encoder_var = ctk.StringVar()
        # قائمة منبثقة لاختيار مشفر الفيديو
        self.encoder_combo = ctk.CTkComboBox(self.gpu_fram, values=get_gpu_encoders(), variable=self.encoder_var)
        self.encoder_combo.grid(row=1, column=1, padx=10, pady=10, sticky="NSEW")
        self.encoder_var.set("libx264")  # افتراضي

        # خيارات الضغط
        self.crf_label = ctk.CTkLabel(self.gpu_fram, text=self.lang.get("crf", "CRF (Quality 0-51):")) # تسمية إعدادات CRF
        self.crf_label.grid(row=1, column=2, padx=10, pady=10, sticky="NSEW") # وضع في الشبكة
 
        # حقل إدخال قيمة CRF   
        # قيمة CRF الافتراضية هي 23 (جودة متوسطة)
        self.crf_entry = ctk.CTkEntry(self.gpu_fram, width=100)
        self.crf_entry.insert(0, "23")
        self.crf_entry.grid(row=1, column=3, padx=10, pady=10, sticky="NSEW")
       
        # قائمة منبثقة لاختيار الإعداد المسبق (السرعة)
        self.preset_label = ctk.CTkLabel(self.gpu_fram, text=self.lang.get("preset", "Preset (speed):"))
        self.preset_label.grid(row=1, column=4, padx=10, pady=10, sticky="NSEW")
        self.preset_var = ctk.StringVar(value="medium") # متغير لتخزين الإعداد المسبق المختار
        
        # قائمة منبثقة لاختيار الإعداد المسبق (السرعة)
        self.preset_combo = ctk.CTkComboBox(self.gpu_fram, values=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"], variable=self.preset_var,state="readonly")
        self.preset_combo.grid(row=1, column=5, padx=10, pady=10, sticky="NSEW")
        #self.preset_var.set("medium")  # افتراضي
       
        # مربع اختيار لنسخ الترميز بدون ضغط
        self.copy_codec_var = ctk.BooleanVar(value=True)
        self.copy_codec_check = ctk.CTkCheckBox(self.gpu_fram, text=self.lang.get("copy_codec", "Copy Codec\n(No compression)"), variable=self.copy_codec_var)
        self.copy_codec_check.grid(row=0, column=3, padx=10, pady=10, sticky="NSEW")

        # Configure frame's internal grid to handle expansion
        #self.gpu_fram.grid_columnconfigure(0, weight=1)
        #self.gpu_fram.grid_rowconfigure(0, weight=1)
        #self.gpu_fram.grid_rowconfigure(1, weight=1)

        # ===== قسم عرض حالة التحميل والتقدم =====
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=20, pady=10)

        # تسمية حالة التحميل
        self.status_label = ctk.CTkLabel(self.status_frame, text="")
        self.status_label.pack(pady=5)

        # شريط تقدم التحميل
        self.progress = ctk.CTkProgressBar(self.status_frame, width=800)
        self.progress.set(0)  # تعيين قيمة البداية للتقدم
        self.progress.pack(pady=5)
        
        # ===== أزرار التحميل والإيقاف =====
        self.buttons_frame = ctk.CTkFrame(self.main_frame)
        self.buttons_frame.pack(fill="x", padx=20, pady=10)
       
        # زر بدء التحميل
        self.download_button = ctk.CTkButton(
            self.buttons_frame, 
            text=self.lang.get("download", "Download"), 
            command=self.start_download
        )
        self.download_button.pack(side="left", padx=5, expand=True, fill="x")
        
        # زر إيقاف التحميل الحالي
        self.stop_button = ctk.CTkButton(
            self.buttons_frame, 
            text=self.lang.get("stop_download", "Stop Download"), 
            command=self.stop_current_download,
            state="disabled"  # معطل في البداية حتى يبدأ التحميل
        )
        self.stop_button.pack(side="right", padx=5, expand=True, fill="x")

        #self.loading_frame.pack(pady=10, padx=20, fill="x")

    # دالة لتغيير مظهر التطبيق
    def change_appearance_mode_event(self, new_appearance_mode: str):
        """
        تغيير مظهر التطبيق (فاتح/داكن/نظام)
        
        المعلمات:
            new_appearance_mode: المظهر الجديد المحدد
        """
        ctk.set_appearance_mode(new_appearance_mode)

    # تفعيل وضع ملء الشاشة عند الضغط على زر "F11"
    def toggle_fullscreen(self, event=None):
        """
        تبديل وضع ملء الشاشة عند الضغط على زر "F11"
        
        المعلمات:
            event: الحدث الذي يسبب التبديل (اختياري)
        """
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
    
    # الخروج من وضع ملء الشاشة بالضغط على "Escape"
    def exit_fullscreen(self, event=None):
        """
        الخروج من وضع ملء الشاشة عند الضغط على "Escape"
        
        المعلمات:
            event: الحدث الذي يسبب الخروج (اختياري)
        """
        self.root.attributes("-fullscreen", False)
    


    # دالة لتغيير لغة التطبيق
    def change_language(self, lang_code: str):
        """
        تغيير لغة واجهة التطبيق
        
        المعلمات:
            lang_code: رمز اللغة الجديدة
        """
        self.lang_code = lang_code # تعيين رمز اللغة الجديد
        self.lang = self.load_language(lang_code) # تحميل ملف اللغة الجديد
        
        # تحديث نصوص جميع عناصر الواجهة بالترجمة الجديدة
        self.title_label.configure(text=self.lang.get("title", "Media Downloader",)) # تحديث عنوان التطبيق
        self.url_entry.configure(placeholder_text=self.lang.get("enter_url", "Enter Media URL")) # تحديث نص الحقل
        self.clear_button.configure(text=self.lang.get("clear", "Clear")) # تحديث نص زر المسح
        self.menu.entryconfig(0, label=self.lang.get("cut", "Cut")) # تحديث نص أمر "قص" في القائمة
        self.menu.entryconfig(1, label=self.lang.get("paste", "Paste")) # تحديث نص أمر "لصق" في القائمة
        self.menu.entryconfig(2, label=self.lang.get("clearing", "Clear")) # تحديث نص أمر "مسح" في القائمة
        self.download_button.configure(text=self.lang.get("download", "Download")) # تحديث نص زر التحميل
        self.sub_checkbox.configure(text=self.lang.get("download_subtitles", "Download Subtitles")) # تحديث نص مربع اختيار الترجمة
        self.aria2_checkbox.configure(text=self.lang.get("use_aria2", "Download with aria2")) # تحديث نص مربع اختيار Aria2c
        self.select_button.configure(text=self.lang.get("select_directory", "Select Directory")) # تحديث نص زر اختيار المجلد
        self.select_cookies_button.configure(text=self.lang.get("select_file", "Select Cookies File")) # تحديث نص زر اختيار ملف COOKIES
        self.stop_button.configure(text=self.lang.get("stop_download", "Stop Download")) # تحديث نص زر إيقاف التحميل
        self.close_after_checkbox.configure(text=self.lang.get("close_after_download", "Close after download")) # تحديث نص مربع اختيار إغلاق بعد التحميل
        self.shutdown_after_download_checkbox.configure(text=self.lang.get("shutdown_after_download", "Shutdown after download")) # تحديث نص مربع اختيار إيقاف التشغيل بعد التحميل
        self.copy_codec_check.configure(text=self.lang.get("copy_codec", "Copy Codec\n(No compression)")) # تحديث نص مربع اختيار نسخ الترميز بدون ضغط   
        self.gpu_label.configure(text=self.lang.get("gpu_encoding", "GPU Encoding GPU/CPU :")) # تحديث نص تسمية إعدادات ترميز GPU
        self.crf_label.configure(text=self.lang.get("crf", "CRF (Quality 0-51):")) # تحديث نص تسمية إعدادات CRF
        self.preset_label.configure(text=self.lang.get("preset", "Preset (speed):")) # تحديث نص تسمية إعدادات الإعداد المسبق (السرعة)
        self.filetype_label.configure(text=self.lang.get("format", "Format:")) # تحديث نص تسمية إعدادات نوع الملف
        self.quality_label.configure(text=self.lang.get("quality", "Quality:")) # تحديث نص تسمية إعدادات الجودة
        self.directory_label.configure(text=self.lang.get("directory", "Directory:") + f" {self.save_dir}") # تحديث نص تسمية إعدادات المجلد
        self.cookiefile_label.configure(text=self.lang.get("file_path", "File PATH:") + f" {self.cookiefile_dir}") # تحديث نص تسمية إعدادات ملف COOKIES
        self.appearance_mode_label.configure(text=self.lang.get("appearance_mode", "Theme:")) # تحديث نص تسمية إعدادات المظهر
        self.language_label.configure(text=self.lang.get("language", "Language:")) # تحديث نص تسمية إعدادات اللغة
        #self.file_button.configure(str(self.lang.get("options", "Options"))) # تحديث نص زر "خيارات" في شريط القائمة


    # دالة للحصول على الحزم المثبتة وإصداراتها في النظام
    def get_installed_packages(self):
        # تنفيذ أمر pip list للحصول على قائمة الحزم المثبتة بصيغة JSON
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        # تحليل النتيجة وتحويلها إلى قاموس يحتوي على أسماء الحزم وإصداراتها
        packages = json.loads(result.stdout)
        return {pkg["name"]: pkg["version"] for pkg in packages}


    # ==============================
    # قسم تحديث الحزم المطلوبة للتطبيق
    # ==============================

    # دالة لبدء عملية تحديث الحزم المطلوبة للتطبيق، حيث يتم إظهار إطار التحميل وتحديث واجهة المستخدم بشكل آمن أثناء عملية التحديث التي تتم في خيط منفصل لمنع تجميد واجهة المستخدم.
    def run_update(self):
        # إظهار إطار التحميل وإعادة تعيين مؤشرات التقدم والحالة
        self.loading_frame.pack(pady=20, fill="x", padx=20)
        self.progress_bar.set(0)
        self.current_package_label.configure(text="")

        # بدء خيط جديد لتحديث الحزم لمنع تجميد واجهة المستخدم
        threading.Thread(target=self.update_task, daemon=True).start()

    # دالة لتنفيذ مهمة تحديث الحزم المطلوبة للتطبيق
    def update_task(self):
        # الحزم التي سيتم تحديثها
        try:
            # الحصول على المسار الصحيح لملف requirements.txt
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # في حالة التشغيل من ملف تنفيذي، يتم تعديل المسار ليتناسب مع بنية الملفات في PyInstaller
            requirements_path = os.path.join(base_dir, "requirements.txt")

            # التحقق من وجود ملف requirements.txt في المسار المحدد
            if not os.path.exists(requirements_path):
                # إذا لم يتم العثور على الملف، رفع استثناء مع رسالة توضح المشكلة
                raise Exception("requirements.txt not found.")

            # قراءة الحزم المطلوبة من ملف requirements.txt
            with open(requirements_path, "r", encoding="utf-8") as f:
                # تصفية الحزم من الملف، مع تجاهل الأسطر الفارغة والأسطر التي تبدأ بتعليق (#)
                packages = [
                    line.strip()
                    for line in f.readlines()
                    if line.strip() and not line.startswith("#")
                ]
            # عدد الحزم المطلوبة للتحديث
            total_packages = len(packages)
            # إذا كان ملف requirements.txt فارغًا (لا يحتوي على أي حزم)، رفع استثناء مع رسالة توضح المشكلة
            if total_packages == 0:
                raise Exception("requirements.txt is empty.")

            # اصدارات الحزم المثبتة قبل التحديث
            before_update = self.get_installed_packages()
            upgraded = []
            # تحديث كل حزمة على حدة مع تحديث واجهة المستخدم بشكل آمن
            for index, package in enumerate(packages, start=1):
                # استخراج اسم الحزمة من السطر (مع تجاهل أي قيود للإصدار مثل == أو >=)
                pkg_name = package.split("==")[0].split(">=")[0].strip()

                # تحديث تسمية الحزمة الحالية في واجهة المستخدم
                self.root.after(
                    0,
                    lambda name=pkg_name, i=index: 
                    self.current_package_label.configure(
                        text=f"Updating: {name} ({i}/{total_packages})"
                    )
                )
                # تنفيذ أمر تحديث الحزمة باستخدام pip
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package, "--upgrade"],
                    capture_output=True,
                    text=True
                )
                # التحقق من نجاح عملية التحديث
                if result.returncode != 0:
                    raise Exception(result.stderr)
                # تحديث شريط التقدم في واجهة المستخدم بشكل آمن
                progress_value = index / total_packages
                self.root.after(0, self.progress_bar.set, progress_value)

            # الحصول على إصدارات الحزم المثبتة بعد التحديث
            after_update = self.get_installed_packages()
            # مقارنة الإصدارات قبل وبعد التحديث لتحديد الحزم التي تم تحديثها
            for pkg in packages:
                # استخراج اسم الحزمة من السطر (مع تجاهل أي قيود للإصدار مثل == أو >=)
                pkg_name = pkg.split("==")[0].split(">=")[0].strip()
                # الحصول على الإصدار القديم والجديد للحزمة من القواميس قبل وبعد التحديث
                old_version = before_update.get(pkg_name)
                new_version = after_update.get(pkg_name)
                # إذا تم تحديث الحزمة (الإصدار القديم مختلف عن الإصدار الجديد)، إضافة معلومات التحديث إلى القائمة
                if old_version and new_version and old_version != new_version:
                    # إضافة الحزمة المحدثة إلى قائمة الحزم المحدثة مع عرض الإصدار القديم والجديد
                    upgraded.append(f"{pkg_name}: {old_version} → {new_version}")
            # عرض نتائج التحديث في واجهة المستخدم بشكل آمن
            self.root.after(0, lambda: self.show_update_results(upgraded))
        # إذا حدث أي خطأ أثناء عملية التحديث، عرض رسالة خطأ في واجهة المستخدم بشكل آمن
        except Exception as e:
            # عرض رسالة خطأ في واجهة المستخدم مع تفاصيل الخطأ الذي حدث أثناء التحديث
            self.root.after(0, lambda: self.update_finished(f"error: {str(e)}"))

    # دالة لعرض نتائج تحديث الحزم في واجهة المستخدم
    def show_update_results(self, upgraded):
        # إعادة تعيين مؤشرات التقدم والحالة في واجهة المستخدم
        self.current_package_label.configure(text="")
        # تعيين شريط التقدم إلى 100% لإظهار اكتمال العملية
        self.progress_bar.set(1)
        # إخفاء إطار التحميل بعد الانتهاء من تحديث الحزم
        self.loading_frame.pack_forget()
        # إذا كانت هناك حزم تم تحديثها، عرض قائمة الحزم المحدثة مع خيار إعادة تشغيل التطبيق لتطبيق التغييرات
        if upgraded:
            # يوجد تحديثات
            message = "Updated Packages:\n\n" + "\n".join(upgraded)

            msg = CTkMessagebox(
                title=self.lang.get("update_complete", "Update Complete"),
                message=message + "\n\n" + self.lang.get("restart_application", "Restart application to apply changes."),
                icon="check",
                option_1=self.lang.get("restart_now", "Restart Now"),
                option_2=self.lang.get("later", "Later")
            )
            # إذا اختار المستخدم إعادة التشغيل الآن، يتم إعادة تشغيل التطبيق لتطبيق التغييرات. إذا اختار لاحقًا، لا يتم فعل أي شيء والسماح له بإعادة التشغيل يدويًا في وقت لاحق.
            if msg.get() == "Restart Now":
                # إعادة تشغيل التطبيق لتطبيق التغييرات
                self.root.destroy()
                # إعادة تشغيل التطبيق باستخدام نفس الأمر الذي تم تشغيله به
                os.execl(
                    sys.executable,
                    sys.executable,
                    *sys.argv
                )

        else:
            # لا يوجد أي تحديث
            CTkMessagebox(
                title=self.lang.get("up_to_date", "Up To Date"),
                message=self.lang.get("packages_up_to_date", "All packages are already up to date."),
                icon="info"
            )

    # دالة لإنهاء عملية التحديث وعرض رسالة في حالة حدوث خطأ أثناء التحديث
    def update_finished(self, status):
        self.progress_bar.stop()
        self.loading_frame.pack_forget()
        # إذا كان هناك خطأ أثناء التحديث، عرض رسالة خطأ للمستخدم. وإلا، عرض رسالة نجاح مع خيار إعادة تشغيل التطبيق لتطبيق التغييرات
        if "error" in status:
            # عرض رسالة خطأ في واجهة المستخدم مع تفاصيل الخطأ الذي حدث أثناء التحديث
            CTkMessagebox(
                title=self.lang.get("error", "Error"),
                message=self.lang.get("update_failed", "Update failed: ") + str(status),
                icon="cancel"
            )
        else:
            # عرض رسالة نجاح في واجهة المستخدم مع خيار إعادة تشغيل التطبيق لتطبيق التغييرات
            msg = CTkMessagebox(
                title=self.lang.get("finished", "Finished"),
                message=self.lang.get("update_reload", "Update complete! You must reload the application for changes to take effect."),
                icon="check",
                option_1=self.lang.get("close_app", "Close App")
            )
            # إذا اختار المستخدم إغلاق التطبيق، يتم إغلاق التطبيق. وإلا، لا يتم فعل أي شيء والسماح له بإعادة التشغيل يدويًا في وقت لاحق.
            if msg.get() == "Close App":
                self.root.destroy()

    
    # دالة للّصق من الحافظة إلى الحقل
    def paste(self):
        """
        Paste the text from the clipboard into the URL entry.
        لصق النص من الحافظة إلى حقل الرابط
        """
        try:
            url = self.url_frame.clipboard_get()         # محاولة الحصول على النص من الحافظة
            # Validate URL format
            # التحقق من أن النص في الحافظة يبدو كعنوان URL صالح (يبدأ بـ http:// أو https:// أو www.)
            if not url.startswith(('http://', 'https://', 'www.')):
                CTkMessagebox(title=self.lang.get("invalid", "Invalid"), message=self.lang.get("invalid_url_format", "Invalid URL format"))
                return
            self.url_entry.delete(0, ctk.END)
            self.url_entry.insert("end", url)
        except tk.TclError:
            return
                                              # إذا فشلت (لا يوجد شيء في الحافظة)، لا تفعل شيئًا
        self.url_entry.delete(0, ctk.END)              # مسح ما بداخل الحقل
        self.url_entry.insert("end", url)             # إدراج النص في نهاية حقل الإدخال

    # دالة للتعامل مع أحداث السحب والإفلات على حقل إدخال URL، حيث يتم قبول بيانات النص (DND_TEXT) ومحاولة إدراجها في الحقل، مع التعامل مع أي استثناءات قد تحدث أثناء العملية.
    def handle_drop(self, event):
        """
        Handle drop events onto the URL entry. Accepts DND_TEXT payloads.
        Tries to insert the dropped text into the entry, with fallback to placeholder if direct insertion fails.
         - يتم قبول بيانات النص (DND_TEXT) من حدث السحب والإفلات
         - يتم محاولة إدراج النص المسقط مباشرة في حقل الإدخال باستخدام delete و insert
         - إذا فشلت عملية الإدراج المباشر (قد يحدث في بعض الحالات أو أنظمة التشغيل)، يتم محاولة تعيين النص المسقط كنص نائب (placeholder) في حقل الإدخال كخطة بديلة لعرض الرابط للمستخدم
         - يتم التعامل مع أي استثناءات قد تحدث أثناء عملية الإدراج أو تعيين النص النائب، بحيث لا يتسبب أي خطأ في تعطيل التطبيق أو إحداث سلوك غير متوقع، ويتم ببساطة تجاهل الأخطاء في هذه الحالة
         - في النهاية، يتم إرجاع "break" لمنع معالجة الحدث بشكل إضافي من قبل النظام أو مكتبة TkinterDnD2، مما يضمن أن النص المسقط هو الوحيد الذي يتم التعامل معه ولا يتم تنفيذ أي إجراءات أخرى مرتبطة بالسحب والإفلات.
         - يتم أيضًا تضمين خطوة تنظيف النص المسقط من أي أحرف غير مرغوب فيها أو تنسيق غير متوقع (مثل إزالة الأقواس المحيطة التي قد تضيفها بعض أنظمة السحب والإفلات)، لضمان أن النص الذي يتم إدراجه أو عرضه كنص نائب هو نص URL نظيف وصالح قدر الإمكان.
         - لا يتم استخدام تعبيرات منتظمة معقدة للتحقق من صحة URL المسقط، بل يتم الاعتماد على التحقق البسيط من أن النص يبدأ بأنماط URL شائعة (http://، https://، www.)، مع عرض رسالة خطأ للمستخدم إذا لم يكن النص المسقط يبدو كعنوان URL صالح، مما يساعد في توجيه المستخدم لإدخال روابط صحيحة.
         - يتم التعامل مع النص المسقط كقيمة نصية فقط، دون محاولة تنفيذ أي عمليات أخرى عليه (مثل التحليل أو التحقق المتقدم)، للحفاظ على بساطة عملية السحب والإفلات والتركيز على إدراج النص في الحقل أو عرضه
        """
        data = getattr(event, "data", "")
        # Trim surrounding braces if present (TkinterDnD wraps text in {})
        if isinstance(data, str) and data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        data = data.strip() if isinstance(data, str) else ""
        if not data:
            return "break"
        try:
            # CTkEntry supports delete/insert like normal tk.Entry
            self.url_entry.delete(0, "end")
            # التحقق من أن النص المسقط يبدو كعنوان URL صالح (يبدأ بـ http:// أو https:// أو www.)
            if not data.startswith(('http://', 'https://', 'www.')):
                CTkMessagebox(title=self.lang.get("invalid", "Invalid"), message=self.lang.get("invalid_url_format", "Invalid URL format"))
                return "break"
            
            # محاولة إدراج النص المسقط مباشرة في حقل الإدخال
            self.url_entry.insert(0, data)
        except Exception:
            try:
                # Fallback: set placeholder text if direct insert fails
                # محاولة تعيين النص المسقط كنص نائب (placeholder) في حقل الإدخال كخطة بديلة لعرض الرابط للمستخدم
                self.url_entry.configure(placeholder_text=data)
            except Exception:
                pass
        # في النهاية، يتم إرجاع "break" لمنع معالجة الحدث بشكل إضافي من قبل النظام أو مكتبة TkinterDnD2، مما يضمن أن النص المسقط هو الوحيد الذي يتم التعامل معه ولا يتم تنفيذ أي إجراءات أخرى مرتبطة بالسحب والإفلات.
        return "break"
    
    # دالة قص الخانة الخاصة بالرابط 
    def copy_to_clipboard(self):
            # الحصول على النص من حقل الإدخال
            url = self.url_entry.get()

            # محاولة نسخ النص إلى الحافظة
            try:
                self.root.clipboard_clear()  # مسح الحافظة أولاً
                self.root.clipboard_append(url)  # نسخ النص إلى الحافظة
            except Exception:
                return
            self.url_entry.delete(0, ctk.END) # مسح ما بداخل الحقل
    
    # دالة لإظهار القائمة عند النقر بزر الفأرة الأيمن
    def show_menu(self,event):
        try:
            # عرض القائمة في موضع مؤشر الفأرة
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            # تحرير التحكم بالقائمة (ضروري أحيانًا لتجنب تجميد القائمة)
            self.menu.grab_release()

    # دالة لمسح حقل رابط URL وإعادة تعيين مؤشرات الحالة
    def clear_url(self):
        """
        مسح حقل رابط URL وإعادة تعيين مؤشرات الحالة
        """
        self.url_entry.delete(0, ctk.END) # مسح ما بداخل الحقل
        # إعادة تعيين حالة التحميل
        self.status_label.configure(text="") # مسح نص حالة التحميل
        self.progress.set(0) # إعادة تعيين شريط التقدم

    # دالة لفتح مربع حوار لاختيار مجلد حفظ الملفات
    def select_directory(self):
        """
        فتح مربع حوار لاختيار مجلد حفظ الملفات
        """
        selected = CTkFileDialog.askdirectory(autocomplete=True,initial_dir=HOME,style='Mini',title=self.lang.get("select_directory", "Select Directory")) # فتح مربع حوار لاختيار المجلد
        # تحديث مسار الحفظ إذا تم اختيار مجلد
        if selected:
            try:
                if not os.path.isdir(selected):
                    raise ValueError("Not a directory")
                if not os.access(selected, os.W_OK):
                    raise ValueError("Directory not writable")
                # Optional: Prevent selecting root or system dirs
                if selected in ['/', '/root', 'C:\\', 'C:\\Windows']:
                    raise ValueError("Invalid directory")
                self.save_dir = selected
                # schedule UI update on main thread
                self.directory_label.configure(text=self.lang.get("directory", "Directory:") + f" {self.save_dir}")
            except Exception as e:
                CTkMessagebox(title="Error", message=f"Invalid directory: {e}")

    # دالة لفتح مربع حوار لاختيار مجلف cookies
    def select_file(self):
        """
        تح مربع حوار لاختيار مجلف cookies  
        """
        selectedfile = CTkFileDialog.askopenfilename(style='Mini',
                                       title=self.lang.get("select_cookies_file_dialog", "Select your cookies.txt file"),
                                       autocomplete=True ,
                                       initial_dir=HOME,
                                       filetypes=[("Text files", "*.txt")]
                                       
                                       ) # فتح مربع حوار لاختيار الملف
        # تحديث مسار ملف cookies إذا تم اختيار ملف  
        if selectedfile:
            # Validate file
            # التحقق من أن الملف الذي تم اختياره هو ملف نصي (بامتداد .txt) وأنه لا يتجاوز حجم معين (مثلاً 5 ميجابايت) لمنع مشاكل الأداء أو الأخطاء أثناء التحميل، مع التعامل مع أي استثناءات قد تحدث أثناء عملية التحقق وعرض رسالة خطأ مناسبة للمستخدم إذا كان الملف غير صالح.
            try:
                if not os.path.isfile(selectedfile):
                    raise ValueError("Not a file")
                # التحقق من أن الملف له امتداد .txt
                if not selectedfile.lower().endswith('.txt'):
                    raise ValueError("File must be a .txt") 
                # التحقق من أن حجم الملف لا يتجاوز 5 ميجابايت
                if os.path.getsize(selectedfile) > 5_000_000:  # Max 5MB
                    raise ValueError("File too large")
                self.cookiefile_dir = selectedfile
                # schedule UI update on main thread
                # تحديث تسمية ملف COOKIES الحالي في واجهة المستخدم مع عرض المسار الجديد للملف الذي تم اختياره
                self.cookiefile_label.configure(text=self.lang.get("file_path", "File PATH:") + f" {self.cookiefile_dir}")

            except Exception as e:
                # عرض رسالة خطأ في واجهة المستخدم مع تفاصيل الخطأ الذي حدث أثناء التحقق من الملف الذي تم اختياره
                CTkMessagebox(title="Error", message=f"Invalid file: {e}")

    # دالة للتحقق من صحة الرابط المدخل ودعمه من قبل التطبيق، حيث يتم التحقق من أن الرابط يبدأ بأنماط URL شائعة (http://، https://، www.) وأنه يحتوي على نطاق صالح بعد التحليل باستخدام urllib.parse، مع التعامل مع أي استثناءات قد تحدث أثناء عملية التحقق وإرجاع False في حالة وجود أي خطأ.
    def validate_url(self, url):
        """
        التحقق من صحة الرابط المدخل ودعمه من قبل التطبيق
         - التحقق من أن الرابط يبدأ بـ http:// أو https:// أو www.
         - التحقق من أن الرابط يحتوي على نطاق صالح (netloc) بعد التحليل
         - لا يتم استخدام تعبيرات منتظمة معقدة لتجنب مشاكل الأداء، بل يتم الاعتماد على تحليل URL بسيط باستخدام urllib.parse
         - يتم التعامل مع أي استثناءات قد تحدث أثناء تحليل URL وإرجاع False في حالة وجود أي خطأ
        """
        # pattern = r'^https?://(www\.)?(youtube|youtu\.be|twitter|instagram|tiktok)'
        # return bool(re.match(pattern, url))
        try:
            normalized_url = url if "://" in url else f"https://{url}" # إضافة https:// إذا لم يكن موجودًا لتسهيل التحليل    
            parsed = urllib.parse.urlparse(normalized_url) # تحليل URL باستخدام urllib.parse للحصول على مكونات URL المختلفة (مثل scheme و netloc)   
            return parsed.scheme in ("http", "https") and bool(parsed.netloc) # التحقق من أن scheme هو http أو https وأن netloc (النطاق) غير فارغ، مما يشير إلى أن الرابط يبدو صالحًا
        except Exception:
            return False

    # دالة لبدء عملية تحميل الفيديو أو قائمة التشغيل
    def start_download(self):
        """
        بدء عملية تحميل الفيديو أو قائمة التشغيل
        """
        # التحقق من وجود FFmpeg المطلوب للتحويل
        ffmeg = check_ffmpeg_installed()

        # التحقق من وجود Aria2c المطلوب للتحويل
        aria2c = check_aria2_installed()

        # الحصول على رابط الفيديو من حقل الإدخال
        url = self.url_entry.get().strip()

        # التحقق من أن المستخدم قد أدخل رابطًا في حقل الإدخال        
        if not url:
            # إظهار تحذير إذا لم يتم إدخال رابط
            CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("please_enter_url", "Please enter a URL."), 
                icon="warning"
            )
            return
        # التحقق من صحة الرابط المدخل ودعمه من قبل التطبيق
        if not self.validate_url(url):
            # إظهار تحذير إذا كان الرابط غير صالح أو غير مدعوم
            CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("invalid_url", "Invalid URL or unsupported platform."), 
                icon="warning"
            )
            return
        # التحقق من تثبيت FFmpeg إذا لم يكن المستخدم قد اختار نسخ الترميز بدون ضغط
        elif not ffmeg:
             # إظهار خطأ إذا لم يتم تثبيت FFmpeg
             CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("please_install_ffmpeg", "Please install FFmpeg."), 
                icon="cancel"
            )
        # التحقق من تثبيت Aria2c إذا اختار المستخدم استخدامه
        elif self.aria2c.get() == True and not aria2c:
            # إظهار خطأ إذا لم يتم تثبيت Aria2c
            CTkMessagebox(
                title=self.lang.get("Warning Message!", "Error"),
                message=self.lang.get("please_install_Aria2c", "Please install Aria2."),
                icon="warning",
                option_1="Cancel",
                option_2="Retry"
            )
            return

        # تنبيه المستخدم اذا اختار إغلاق الحاسوب بعد التحميل دون اختيار إغلاق التطبيق
        if self.shutdown_after_download.get():
            # إظهار تحذير إذا اختار المستخدم إغلاق الحاسوب بعد التحميل دون اختيار إغلاق التطبيق
            self.warning_shutdown = CTkMessagebox(
                title=self.lang.get("warning", "Warning"),
                message=self.lang.get("shutdown_without_closing", "You have selected to shutdown the computer after download without selecting to close the application. This may cause the computer to shutdown while the application is still running. Do you want to proceed?"),
                icon="warning",
                option_1="Cancel",
                option_2="Proceed"
            )
            # إذا اختار المستخدم "إلغاء"، يتم إلغاء عملية التحميل والعودة إلى الواجهة الرئيسية دون بدء التحميل أو إغلاق الحاسوب، مما يسمح له بتعديل خياراته أو إعادة النظر في قراره قبل المتابعة.
            if self.warning_shutdown.get() == "Cancel":
                return  # إلغاء عملية التحميل إذا اختار المستخدم "إلغاء"
        new_url = self.process_youtube_url(url)
        # تعطيل زر التحميل وتفعيل زر الإيقاف أثناء عملية التحميل
        self.download_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.is_downloading = True

        # عرض حالة التحميل الأولية
        self.status_label.configure(text=self.lang.get("fetching_info", "Fetching videos info..."))

        # بدء خيط جديد للتحميل لمنع تجميد واجهة المستخدم
        self.current_download_thread = threading.Thread(target=self.prepare_and_download, args=(new_url,))
        self.current_download_thread.daemon = True  # الخيط ينتهي عند إنهاء البرنامج الرئيسي
        self.current_download_thread.start()
    
    # دالة للتعامل مع إغلاق النافذة (مثل الضغط على زر الإغلاق)، حيث يتم التحقق مما إذا كان هناك عملية تحميل جارية، وإذا كان الأمر كذلك، يتم طلب تأكيد من المستخدم قبل إغلاق النافذة، وإذا وافق المستخدم على الإغلاق، يتم استدعاء دالة إيقاف التحميل من مكتبة التحميل وإغلاق النافذة، أما إذا لم يكن هناك تحميل جاري، يتم إغلاق النافذة مباشرة.
    def on_closing(self):
        """
        التعامل مع إغلاق النافذة (مثل الضغط على زر الإغلاق)
        """
        # التحقق مما إذا كان هناك عملية تحميل جارية
        if self.is_downloading:
            # إذا كان هناك عملية تحميل جارية، نطلب تأكيد من المستخدم قبل الإغلاق
            self.msg = CTkMessagebox(title=self.lang.get("exit_prompt", "Exit?"), message=self.lang.get("ask_to_stop_download_on_exit", "A download is in progress. Are you sure you want to exit?"),
                            icon="question", option_1=self.lang.get("cancel", "Cancel"), option_2=self.lang.get("no", "No"), option_3=self.lang.get("yes", "Yes"))
            self.response = self.msg.get() # الحصول على استجابة المستخدم
            if self.response == "Yes":
                stop_download() # استدعاء دالة إيقاف التحميل من مكتبة التحميل
                # Wait for the thread to finish (with timeout)
                # إذا كان الخيط لا يزال يعمل بعد محاولة إيقاف التحميل، ننتظر لفترة قصيرة (مثلاً 2 ثانية) قبل إغلاق النافذة، لضمان أن عملية إيقاف التحميل قد تمت بشكل صحيح وتجنب إغلاق النافذة أثناء وجود عمليات غير مستقرة في الخلفية.   
                if self.current_download_thread and self.current_download_thread.is_alive():
                    self.current_download_thread.join(timeout=2)  # Wait max 2 seconds for the thread to finish
                self.root.destroy() # إغلاق النافذة
        else:
            self.root.destroy() # إغلاق النافذة إذا لم يكن هناك تحميل جاري             
            
    # دالة للتحقق من حالة خيط التحميل وإعادة تفعيل الواجهة عند الانتهاء
    def check_download_thread(self):
        """
        Checks the status of the download thread and re-enables the interface when finished.
        - يتم التحقق مما إذا كان خيط التحميل لا يزال يعمل باستخدام is_alive()
        """
        # إذا كان الخيط لا يزال يعمل، يتم جدولة التحقق مرة أخرى بعد فترة قصيرة (مثلاً 100 ميلي ثانية) باستخدام after()، مما يسمح لواجهة المستخدم بالبقاء مستجيبة أثناء عملية التحميل.
        if self.current_download_thread.is_alive():
            # إذا كان الخيط لا يزال يعمل، نتحقق مرة أخرى بعد 100 ميلي ثانية
            self.root.after(100, self.check_download_thread)
        else:
            # إذا انتهى الخيط، نعيد تفعيل زر التحميل وتعطيل زر الإيقاف
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.is_downloading = False
            if self.shutdown_after_download.get():
                self.root.after(30000, self.shutdown_computer)  # إغلاق الحاسوب بعد 30 ثانية
            elif self.close_after_download.get():
                self.root.after(30000, self.root.destroy)  # إغلاق التطبيق بعد 30 ثانية  
    # دالة لإغلاق الحاسوب بعد اكتمال التحميل
     # دالة لإغلاق الحاسوب بعد اكتمال التحميل
    # دالة لإغلاق الحاسوب بعد اكتمال التحميل
    def shutdown_computer(self):
        """
        إغلاق الحاسوب بعد اكتمال التحميل مع عداد تنازلي 30 ثانية (بدون تجميد)
        """
        if self.is_downloading:
            return
        
        if not self.shutdown_after_download.get():
            return
        
        self.shutdown_counter = 30
        
        # إنشاء نافذة مخصصة للعد التنازلي
        self.shutdown_win = ctk.CTkToplevel(self.root)
        self.shutdown_win.title(self.lang.get("shutdown", "Shutdown"))
        self.shutdown_win.geometry("420x180")
        self.shutdown_win.resizable(False, False)
        self.shutdown_win.transient(self.root)  
        self.shutdown_win.grab_set()            
        
        # توسيط النافذة
        self.shutdown_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        self.shutdown_win.geometry(f"+{x}+{y}")
        
        message_text = self.lang.get("shutdown_countdown", "The computer will shutdown in {0} seconds. Do you want to cancel the shutdown?").format(self.shutdown_counter)
        self.countdown_label = ctk.CTkLabel(
            self.shutdown_win, 
            text=message_text, 
            font=("Arial", 13, "bold"),
            wraplength=380
        )
        self.countdown_label.pack(pady=30, padx=20)
        
        btn_frame = ctk.CTkFrame(self.shutdown_win, fg_color="transparent")
        btn_frame.pack(pady=5)
        
        def cancel_action():
            self.shutdown_win.destroy()
            
        def proceed_action():
            self.shutdown_win.destroy()
            self.execute_shutdown()  # استدعاء دالة الإغلاق
            
        btn_cancel = ctk.CTkButton(
            btn_frame, 
            text=self.lang.get("cancel_shutdown", "Cancel Shutdown"), 
            command=cancel_action,
            fg_color="#d32f2f", 
            hover_color="#b71c1c"
        )
        btn_cancel.grid(row=0, column=0, padx=10)
        
        btn_proceed = ctk.CTkButton(
            btn_frame, 
            text=self.lang.get("proceed_shutdown", "Proceed with Shutdown"), 
            command=proceed_action
        )
        btn_proceed.grid(row=0, column=1, padx=10)
        
        self.shutdown_win.protocol("WM_DELETE_WINDOW", cancel_action)
        
        def update_countdown():
            if not self.shutdown_win.winfo_exists():
                return 
                
            if self.shutdown_counter > 0:
                self.shutdown_counter -= 1
                new_msg = self.lang.get("shutdown_countdown", "The computer will shutdown in {0} seconds. Do you want to cancel the shutdown?").format(self.shutdown_counter)
                self.countdown_label.configure(text=new_msg)
                self.shutdown_win.after(1000, update_countdown)
            else:
                self.shutdown_win.destroy()
                self.execute_shutdown()  # استدعاء دالة الإغلاق عند انتهاء الوقت
                
        self.shutdown_win.after(1000, update_countdown)

    # دالة لتنفيذ أمر إغلاق الحاسوب (تأكد أنها تبدأ بنفس مستوى محاذاة الدالة السابقة)
    def execute_shutdown(self):
        """
        تنفيذ أمر إغلاق الحاسوب بناءً على نظام التشغيل
        """
        try:
            if sys.platform == "win32":
                os.system("shutdown /s /t 1")  
            elif sys.platform == "darwin":
                os.system("sudo shutdown -h now")  
            else:
                os.system("shutdown -h now")  
        except Exception as e:
            # استيراد محلي لتفادي أي مشاكل
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(
                title=self.lang.get("error", "Error"),
                message=f"{self.lang.get('shutdown_error', 'Failed to shutdown the computer:')} {str(e)}",
                icon="cancel"
            )


    # دالة لإيقاف عملية التحميل الحالية
    def stop_current_download(self):
        """
        إيقاف عملية التحميل الحالية بعد تأكيد المستخدم
        """
        # التحقق من وجود عملية تحميل جارية
        if self.is_downloading:
            # طلب تأكيد من المستخدم قبل الإيقاف
            self.msg = CTkMessagebox(title=self.lang.get("exit_prompt", "Exit?"), message=self.lang.get("ask_to_stop_download", "Are you sure to stop the download?"),
                            icon="question", option_1=self.lang.get("cancel", "Cancel"), option_2=self.lang.get("no", "No"), option_3=self.lang.get("yes", "Yes"))
            self.response = self.msg.get() # الحصول على استجابة المستخدم
            if self.response == "Yes":
                # إيقاف التحميل وإعادة تعيين حالة التطبيق
                stop_download() # استدعاء دالة إيقاف التحميل من مكتبة التحميل
                self.status_label.configure(text=self.lang.get("download_stopped", "Download stopped."))
                
                # إعادة تفعيل زر التحميل وتعطيل زر الإيقاف
                self.download_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.is_downloading = False
    
    # دالة لتحضير وتحميل الفيديوهات من الرابط
    def prepare_and_download(self, url):
        """
        تحضير وتحميل الفيديوهات من الرابط (قد يكون فيديو واحد أو قائمة تشغيل)
        
        المعلمات:
                 url: رابط الفيديو أو قائمة التشغيل
        cookies_path: استخدام cookies لحل مشاكل الفيديوهات المحمية 
        """

         # التحقق من وجود مجلد الحفظ         
        try:
            # جلب معلومات الفيديوهات من الرابط
            result = get_videos_info(url,cookies_path=self.cookiefile_dir) # استدعاء دالة جلب معلومات الفيديوهات من مكتبة التحميل
            videos = result["videos"] # قائمة الفيديوهات المستخرجة
            playlist_title = result["playlist_title"] # عنوان قائمة التشغيل (إن وجدت)
            channel_title = result.get("channel_title")
            
            total = len(videos) # العدد الكلي للفيديوهات
            # التحقق من صحة قيمة CRF إذا لم يكن المستخدم قد اختار نسخ الترميز بدون ضغط
            if (not self.copy_codec_var.get() and (int(self.crf_entry.get()) < 0 or int(self.crf_entry.get()) > 51)):
                CTkMessagebox(
                    title=self.lang.get("error", "Error"), 
                    message=self.lang.get("crf_value_error", "CRF value must be between 0 and 51."), 
                    icon="warning"
                )
                self.download_button.configure(state="normal") # إعادة تفعيل زر التحميل
                self.stop_button.configure(state="disabled") # تعطيل زر الإيقاف
                self.is_downloading = False # تعيين حالة التحميل إلى غير نشطة
                return

            # التحقق من وجود فيديوهات في القائمة
            if total == 0:
                # إذا لم يتم العثور على فيديوهات
                self.status_label.configure(text=self.lang.get("no_videos_found", "No videos found")) # تحديث حالة التحميل
                # إظهار رسالة تحذير للمستخدم
                self.download_button.configure(state="normal") # إعادة تفعيل زر التحميل
                self.stop_button.configure(state="disabled") # تعطيل زر الإيقاف
                self.is_downloading = False # تعيين حالة التحميل إلى غير نشطة
                return
            
            # تحميل كل فيديو في القائمة
            for idx, video in enumerate(videos, start=1): # التكرار عبر الفيديوهات مع تعيين رقم لكل فيديو
                if not self.is_downloading:
                    # التحقق من عدم إيقاف التحميل
                    break
                
                # عرض معلومات التقدم: رقم الفيديو الحالي/العدد الكلي + عنوان الفيديو
                self.status_label.configure(
                    text=f"{idx}/{total} --> {video['title'][:70]}"
                )
                self.progress.set(0)  # إعادة تعيين شريط التقدم لكل فيديو
                
                try:
                    # تحميل الفيديو الحالي
                    playlist_folder = video.get('sub_dir_title') if video.get('item_type') == 'playlist' else playlist_title
                    if channel_title and playlist_folder:
                        playlist_folder = os.path.join(channel_title, playlist_folder)
                    elif channel_title and not playlist_folder:
                        playlist_folder = channel_title

                    self.download_single_video(video['url'], playlist_folder)
                except Exception as e:
                    if "Download stopped by user" in str(e):
                        break
                    self.status_label.configure(text=str(e))
                    # استمر مع الفيديو التالي في حالة حدوث خطأ
            
            # إظهار رسالة إتمام التحميل إذا تم بنجاح
            if self.is_downloading:
                self.status_label.configure(text=self.lang.get("all_downloaded", "All videos downloaded!"))
                CTkMessagebox(
                    title=self.lang.get("download_complete", "Download Complete"), 
                    message=self.lang.get("all_downloaded", "All videos downloaded!"), 
                    icon="check"
                )
                # إظهار إشعار سطح المكتب عند اكتمال التحميل
                notify = Notifier()
                notify.notification()
                
                if self.current_download_thread.is_alive():
                # كي لا تتجمد الواجهة أثناء الانتظار، نستخدم after للتحقق بشكل دوري من حالة الخيط
                    self.root.after(100, self.check_download_thread)

        except Exception as e:
            # التعامل مع الأخطاء العامة
            #'''self.status_label.configure(text=str(e))
            #CTkMessagebox(
            #    title=self.lang.get("error", "Error"), 
            #    message=str(e), 
            #    icon="cancel"
            #)'''
            #except Exception as e:
            error_message = str(e)
            self.status_label.configure(text=error_message) # تحديث حالة التحميل بالخطأ

            # ERROR: '/home/xq/password.txt' does not look like a Netscape format cookies file
            if "does not look like a Netscape format cookies file" in str(error_message):
                CTkMessagebox(
                    title=self.lang.get("error", "Error"),
                    message=self.lang.get("invalid_cookies_file", "The selected file is not a valid cookies.txt file. Please select a correct file."),
                    icon="cancel"
                )
                return

            # 👇 الكشف عن الفيديوهات الخاصة أو المحمية
            elif "Private video" in error_message or "Sign in" in error_message or "cookies" in error_message: # التحقق من وجود رسائل خاصة بالفيديو الخاص أو المحمي
                # طلب من المستخدم اختيار ملف cookies
                response = CTkMessagebox(
                    title=self.lang.get("private_video", "Private Video Detected"),
                    message=self.lang.get(
                        "private_video_msg",
                        "This video is private or requires login.\nPlease select a cookies file to continue."
                    ),
                    icon="warning",
                    option_1=self.lang.get("cancel", "Cancel"),
                    option_2=self.lang.get("select_file", "Select File")
                ).get()
                # إذا اختار المستخدم "Select File"، يتم فتح مربع حوار لاختيار ملف cookies، ويتم تحديث مسار ملف cookies في التطبيق، ثم يتم إعادة محاولة التحميل باستخدام الملف الجديد الذي تم اختياره， مما يسمح للمستخدم بالوصول إلى الفيديو الخاص أو المحمي إذا كان لديه ملف cookies صالح يحتوي على بيانات تسجيل الدخول اللازمة.    
                if response == self.lang.get("select_file", "Select File"):
                    file_event = threading.Event()
                    result = {"path": None}

                    # دالة لفتح مربع حوار لاختيار ملف cookies وتشغيلها في خيط منفصل لتجنب تجميد واجهة المستخدم
                    def choose_file():
                        result["path"] = CTkFileDialog.askopenfilename(
                            autocomplete=True,
                            style='Mini',
                            title=self.lang.get("select_cookies_file_dialog", "Select your cookies.txt file"),
                            initial_dir=HOME,
                            filetypes=[("Text files", "*.txt")]
                        )
                        file_event.set()

                    self.root.after(0, choose_file) # تشغيل دالة اختيار الملف في خيط منفصل باستخدام after لتجنب تجميد واجهة المستخدم
                    file_event.wait() # الانتظار حتى ينتهي المستخدم من اختيار الملف أو إلغاء العملية
                    selected_file = result.get("path") # الحصول على المسار الذي اختاره المستخدم

                    if selected_file: # إذا تم اختيار ملف
                        self.cookiefile_dir = selected_file
                        # update label on main thread as well
                        self.cookiefile_label.configure(text=self.lang.get("file_path", "File PATH:") + f" {self.cookiefile_dir}")
                        
                        # إعادة المحاولة بعد اختيار الملف
                        self.prepare_and_download(url)
                        return

                # في حال إلغاء المستخدم
                self.status_label.configure(
                    text=self.lang.get("download_cancelled", "Download cancelled by user.")
                )

            else:
                # 👇 التعامل مع باقي الأخطاء العادية
                CTkMessagebox(
                    title=self.lang.get("error", "Error"),
                    message=error_message,
                    icon="cancel"
                )
                
        finally:
            # إعادة تعيين حالة التطبيق بغض النظر عن نتيجة التحميل
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.is_downloading = False
    
    # دالة لتحميل فيديو واحد مع تتبع التقدم
    def download_single_video(self, url, playlist_title=None): # دالة لتحميل فيديو واحد مع تتبع التقدم
        """
        تحميل فيديو واحد مع تتبع التقدم
        
        المعلمات:
            url: رابط الفيديو المراد تحميله
            playlist_title: عنوان قائمة التشغيل (إن وجدت)
        """
        try:
            # دالة تتبع تقدم التحميل
            def progress_hook(d): 
                """
                دالة تتبع تقدم التحميل لتحديث شريط التقدم
                
                المعلمات:
                    d: معلومات التقدم من مكتبة التحميل
                """
                if d.get("status") == "downloading":
                    # حساب نسبة التقدم أثناء التحميل
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                    downloaded = d.get("downloaded_bytes", 0)
                    progress_value = downloaded / total
                    self.progress.set(progress_value)
                elif d.get("status") == "finished":
                    # اكتمال التحميل
                    self.progress.set(1.0)

            # تنفيذ عملية التحميل باستخدام الإعدادات المحددة
            download_video(
                url=url,
                download_dir=self.save_dir,
                quality=self.quality.get(),
                file_type=self.file_type.get(),
                download_subtitles=self.subtitles.get(),
                encoder = self.encoder_var.get(),
                crf = int(self.crf_entry.get()),
                preset = self.preset_var.get(),
                copy_codec = self.copy_codec_var.get(),
                progress_hook=progress_hook,
                playlist_title=playlist_title,
                use_aria2=self.aria2c.get(),
                cookies_path=self.cookiefile_dir
                )
        except Exception as e:
            raise e  # إعادة رفع الاستثناء للتعامل معه في الدالة الأعلى
