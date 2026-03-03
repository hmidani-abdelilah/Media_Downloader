import customtkinter as ctk  # استيراد مكتبة واجهة المستخدم المخصصة
from PIL import Image, ImageTk # لتضمين أيقونة للتطبيق مهما كان نوع نظام التشغيل
import tkinter as tk  # استيراد مكتبة tkinter لإنشاء قائمة السياق
from customtkinter import filedialog  # لفتح مربع حوار اختيار الملفات
from CTkFileDialog import askdirectory , askopenfilename # لفتح مربع حوار اختيار المجلدات
from CTkFileDialog.Constants import HOME
from CTkMessagebox import CTkMessagebox  # لعرض رسائل منبثقة للمستخدم 
from CTkMenuBar import * #  استيراد مكتبة القوائم الافقية 
from downloader import download_video, get_videos_info, get_gpu_encoders, stop_download # استيراد وظائف التحميل
from ffmpeg_check import check_ffmpeg_installed  # للتحقق من تثبيت FFmpeg
from aria2_check import check_aria2_installed # للتحقق من تثبيت Aria2c
import threading  # للتنفيذ المتزامن للمهام
import json  # للتعامل مع ملفات اللغة
import os  # للتعامل مع نظام الملفات
import sys  # للوصول إلى معلومات النظام
from utils import resource_path
import subprocess

#pyinstaller --onefile --windowed --add-data=languages;languages --add-data=asset/Icon.ico;asset --add-data=aria2;aria2 --add-data=ffmpeg;ffmpeg --icon=asset/Icon.ico app.py -n MediaDownloader.exe

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
        
        # Initialize the menu bar
        # --- UI ELEMENTS ---
        self.menu_bar = CTkMenuBar(master=self.root)
        # Add top-level buttons
        self.file_button = self.menu_bar.add_cascade("Options")
        #self.edit_button = self.menu_bar.add_cascade("Edit")
        
        # Create dropdown content
        self.dropdown = CustomDropdownMenu(widget=self.file_button)
        self.dropdown.add_option(option="Check for Updates", command=self.run_update)
        self.dropdown.add_separator()
        self.dropdown.add_option(option="Exit", command=self.root.destroy)
        
        
        # تحميل أيقونة التطبيق من المسار الصحيح
        #icon_image = Image.open(os.path.join("asset", "Icon.ico")) # فتح صورة الأيقونة
        #icon_tk = ImageTk.PhotoImage(icon_image) # تحويل الصورة إلى تنسيق يمكن لـ Tkinter استخدامه
        # تعيين الأيقونة لنافذة التطبيق
        #self.root.wm_iconphoto(True, icon_tk)
        # windows os exe 
        #icon_path = self.resource_path(os.path.join("asset", "Icon.ico"))
        #self.root.iconbitmap(icon_path)
        
        # تهيئة متغيرات اللغة والحالة
        self.lang = self.load_language(lang_code) # تحميل ملف اللغة المناسب
        self.lang_code = lang_code # تعيين رمز اللغة الحالي
        self.save_dir = os.path.expanduser("~")  # مجلد المستخدم الافتراضي كمسار حفظ
        self.cookiefile_dir = "\U0001F36A" # مسار ملف cookies 
        self.current_download_thread = None  # خيط التنزيل الحالي
        self.is_downloading = False  # مؤشر على حالة التنزيل
    
        # إنشاء عناصر واجهة المستخدم
        self.create_widgets()

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

    # دالة لإنشاء عناصر واجهة المستخدم الرسومية 
    def create_widgets(self):
        """
        إنشاء وتنظيم عناصر واجهة المستخدم الرسومية
        """
        # Loading Frame (Hidden by default)
        self.loading_frame = ctk.CTkFrame(self.root)
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Updating dependencies, please wait...")
        self.loading_label.pack(pady=5)
        self.current_package_label = ctk.CTkLabel(self.loading_frame, text="")
        self.current_package_label.pack(pady=2)
        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, orientation="horizontal", mode="determinate")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        
        
        # إنشاء الإطارات الرئيسية
        self.top_frame = ctk.CTkFrame(self.root) # إطار علوي لإعدادات المظهر واللغة
        self.top_frame.pack(fill="x", padx=10, pady=5) # تعبئة العرض بالكامل مع حواف
        
        self.main_frame = ctk.CTkFrame(self.root) # الإطار الرئيسي لبقية عناصر الواجهة
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5) # تعبئة العرض والارتفاع بالكامل مع حواف
        
        # ===== قسم إعدادات المظهر في الأعلى =====
        self.appearance_mode_label = ctk.CTkLabel(self.top_frame, text="Theme:") # تسمية إعدادات المظهر
        self.appearance_mode_label.pack(side="left", padx=5) # تعبئة على اليسار مع حواف
        
         # قائمة منبثقة لاختيار وضع المظهر (فاتح/داكن/نظام)     
        
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_menu.pack(side="left", padx=5) # تعبئة على اليسار مع حواف
        
       
        # ===== قسم إعدادات اللغة =====
        self.language_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["en", "ar", "fr"],  # اللغات المدعومة: الإنجليزية والعربية والفرنسية
            command=self.change_language
        )
        self.language_menu.set(self.lang_code) # تعيين اللغة الافتراضية
        self.language_menu.pack(side="right", padx=5) # تعبئة على اليمين مع حواف
        
        # تسمية إعدادات اللغة
        
        self.language_label = ctk.CTkLabel(self.top_frame, text="Language:") # تسمية إعدادات اللغة
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
            placeholder_text=self.lang.get("enter_url", "Enter Media URL"), 
            width=400
        )
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True) # تعبئة على اليسار مع حواف وتوسيع

        
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
            values=["best","mp4", "mp3"],  # أنواع الملفات المتاحة
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
        self.gpu_label = ctk.CTkLabel(self.gpu_fram, text="Video Encoder (GPU/CPU):")
        self.gpu_label.grid(row=1, column=0, padx=10, pady=10, sticky="NSEW")
        # متغير لتخزين مشفر الفيديو المختار
        self.encoder_var = ctk.StringVar()
        # قائمة منبثقة لاختيار مشفر الفيديو
        self.encoder_combo = ctk.CTkComboBox(self.gpu_fram, values=get_gpu_encoders(), variable=self.encoder_var)
        self.encoder_combo.grid(row=1, column=1, padx=10, pady=10, sticky="NSEW")
        self.encoder_var.set("libx264")  # افتراضي

        # خيارات الضغط
        self.crf_label = ctk.CTkLabel(self.gpu_fram, text="CRF (Quality 0-51):") # تسمية إعدادات CRF
        self.crf_label.grid(row=1, column=2, padx=10, pady=10, sticky="NSEW") # وضع في الشبكة
 
        # حقل إدخال قيمة CRF   
        # قيمة CRF الافتراضية هي 23 (جودة متوسطة)
        self.crf_entry = ctk.CTkEntry(self.gpu_fram, width=100)
        self.crf_entry.insert(0, "23")
        self.crf_entry.grid(row=1, column=3, padx=10, pady=10, sticky="NSEW")
       
        # قائمة منبثقة لاختيار الإعداد المسبق (السرعة)
        self.preset_label = ctk.CTkLabel(self.gpu_fram, text="Preset (speed):")
        self.preset_label.grid(row=1, column=4, padx=10, pady=10, sticky="NSEW")
        self.preset_var = ctk.StringVar(value="medium") # متغير لتخزين الإعداد المسبق المختار
        
        # قائمة منبثقة لاختيار الإعداد المسبق (السرعة)
        self.preset_combo = ctk.CTkComboBox(self.gpu_fram, values=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"], variable=self.preset_var,state="readonly")
        self.preset_combo.grid(row=1, column=5, padx=10, pady=10, sticky="NSEW")
        #self.preset_var.set("medium")  # افتراضي
       
        # مربع اختيار لنسخ الترميز بدون ضغط
        self.copy_codec_var = ctk.BooleanVar(value=True)
        self.copy_codec_check = ctk.CTkCheckBox(self.gpu_fram, text="Copy Codec\n(No compression)", variable=self.copy_codec_var)
        self.copy_codec_check.grid(row=0, column=2, padx=10, pady=10, sticky="NSEW")

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
        self.root.after(0,self.title_label.configure(text=self.lang.get("title", "Media Downloader"))) # تحديث عنوان التطبيق
        self.url_entry.configure(placeholder_text=self.lang.get("enter_url", "Enter YouTube URL")) # تحديث نص الحقل
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

    def get_installed_packages(self):
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )

        packages = json.loads(result.stdout)
        return {pkg["name"]: pkg["version"] for pkg in packages}


    # ==============================
    # UPDATE DEPENDENCIES
    # ==============================

    def run_update(self):
        # Show loading UI (this runs in main thread already)
        self.loading_frame.pack(pady=20, fill="x", padx=20)
        self.progress_bar.set(0)
        self.current_package_label.configure(text="")

        # Run update in background thread
        threading.Thread(target=self.update_task, daemon=True).start()


    def update_task(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            requirements_path = os.path.join(base_dir, "requirements.txt")

            if not os.path.exists(requirements_path):
                raise Exception("requirements.txt not found.")

            # Read packages
            with open(requirements_path, "r", encoding="utf-8") as f:
                packages = [
                    line.strip()
                    for line in f.readlines()
                    if line.strip() and not line.startswith("#")
                ]

            total_packages = len(packages)
            if total_packages == 0:
                raise Exception("requirements.txt is empty.")

            # Versions before update
            before_update = self.get_installed_packages()
            upgraded = []

            for index, package in enumerate(packages, start=1):

                pkg_name = package.split("==")[0].split(">=")[0].strip()

                # SAFE UI UPDATE
                self.root.after(
                    0,
                    lambda name=pkg_name, i=index: 
                    self.current_package_label.configure(
                        text=f"Updating: {name} ({i}/{total_packages})"
                    )
                )

                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package, "--upgrade"],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    raise Exception(result.stderr)

                progress_value = index / total_packages
                self.root.after(0, self.progress_bar.set, progress_value)

            # Versions after update
            after_update = self.get_installed_packages()

            for pkg in packages:
                pkg_name = pkg.split("==")[0].split(">=")[0].strip()
                old_version = before_update.get(pkg_name)
                new_version = after_update.get(pkg_name)

                if old_version and new_version and old_version != new_version:
                    upgraded.append(f"{pkg_name}: {old_version} → {new_version}")

            self.root.after(0, lambda: self.show_update_results(upgraded))

        except Exception as e:
            self.root.after(0, lambda: self.update_finished(f"error: {str(e)}"))


    def show_update_results(self, upgraded):
        self.current_package_label.configure(text="")
        self.progress_bar.set(1)
        self.loading_frame.pack_forget()

        if upgraded:
            # يوجد تحديثات
            message = "Updated Packages:\n\n" + "\n".join(upgraded)

            msg = CTkMessagebox(
                title="Update Complete",
                message=message + "\n\nRestart application to apply changes.",
                icon="check",
                option_1="Restart Now",
                option_2="Later"
            )

            if msg.get() == "Restart Now":
                self.root.destroy()

        else:
            # لا يوجد أي تحديث
            CTkMessagebox(
                title="Up To Date",
                message="All packages are already up to date.",
                icon="info"
            )


    def update_finished(self, status):
        self.progress_bar.stop()
        self.loading_frame.pack_forget()

        if "error" in status:
            CTkMessagebox(
                title="Error",
                message=f"Update failed: {status}",
                icon="cancel"
            )
        else:
            msg = CTkMessagebox(
                title="Finished",
                message="Update complete! You must reload the application for changes to take effect.",
                icon="check",
                option_1="Close App"
            )

            if msg.get() == "Close App":
                self.root.destroy()

    
    # دالة للّصق من الحافظة إلى الحقل
    def paste(self):
        try:
            url = self.url_frame.clipboard_get()         # محاولة الحصول على النص من الحافظة
        except tk.TclError:
            return                                       # إذا فشلت (لا يوجد شيء في الحافظة)، لا تفعل شيئًا
        self.url_entry.delete(0, ctk.END)              # مسح ما بداخل الحقل
        self.url_entry.insert("end", url)             # إدراج النص في نهاية حقل الإدخال
    
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
        selected = askdirectory(autocomplete=True,initial_dir=HOME,style='Mini') # فتح مربع حوار لاختيار المجلد
        # تحديث مسار الحفظ إذا تم اختيار مجلد
        if selected:
            self.save_dir = selected
            # schedule UI update on main thread
            self.root.after(0, self.directory_label.configure, {"text": f"Directory: {self.save_dir}"})

    # دالة لفتح مربع حوار لاختيار مجلف cookies
    def select_file(self):
        """
        تح مربع حوار لاختيار مجلف cookies  
        """
        selectedfile = askopenfilename(autocomplete=True ,style='Mini',
                                       title="Select your cookies.txt file",
                                        initial_dir=HOME,
                                        filetypes=[("Text files", "*.txt")]
                                       
                                       ) # فتح مربع حوار لاختيار الملف
        # تحديث مسار ملف cookies إذا تم اختيار ملف  
        if selectedfile:
            self.cookiefile_dir = selectedfile
            # schedule UI update on main thread
            self.cookiefile_label.configure(text=f"Cookies file: {self.cookiefile_dir}")

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
                
        if not url:
            # إظهار تحذير إذا لم يتم إدخال رابط
            CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("please_enter_url", "Please enter a URL."), 
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
        elif self.aria2c.get() == True  and not aria2c:
             # إظهار خطأ إذا لم يتم تثبيت Aria2c
             CTkMessagebox(
                title=self.lang.get("Warning Message!", "Error"), 
                message=self.lang.get("please_install_Aria2c", "Please install Aria2."), 
                icon="warning", option_1="Cancel", option_2="Retry"
            )
        else:    
            # تعطيل زر التحميل وتفعيل زر الإيقاف أثناء عملية التحميل
            self.download_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.is_downloading = True
            
            # عرض حالة التحميل الأولية
            self.status_label.configure(text=self.lang.get("fetching_info", "Fetching videos info..."))
            
            # بدء خيط جديد للتحميل لمنع تجميد واجهة المستخدم
            self.current_download_thread = threading.Thread(target=self.prepare_and_download, args=(url,))
            self.current_download_thread.daemon = True  # الخيط ينتهي عند إنهاء البرنامج الرئيسي
            self.current_download_thread.start()
            if self.current_download_thread.is_alive():
                # كي لا تتجمد الواجهة أثناء الانتظار، نستخدم after للتحقق بشكل دوري من حالة الخيط
                self.root.after(100, self.check_download_thread)

    def check_download_thread(self):
        if self.current_download_thread.is_alive():
            # إذا كان الخيط لا يزال يعمل، نتحقق مرة أخرى بعد 100 ميلي ثانية
            self.root.after(100, self.check_download_thread)
        else:
            # إذا انتهى الخيط، نعيد تفعيل زر التحميل وتعطيل زر الإيقاف
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.is_downloading = False
            if self.shutdown_after_download.get():
                self.root.after(1000, self.shutdown_computer)  # إغلاق الحاسوب بعد 1 ثانية
            elif self.close_after_download.get():
                self.root.after(1000, self.root.destroy)  # إغلاق التطبيق بعد 1 ثانية  

    def shutdown_computer(self):
        """
        إغلاق الحاسوب بعد اكتمال التحميل
        """
        if sys.platform == "win32":
            os.system("shutdown /s /t 1")  # أمر إغلاق الحاسوب في ويندوز
        elif sys.platform == "darwin":
            os.system("sudo shutdown -h now")  # أمر إغلاق الحاسوب في ماك (قد يتطلب صلاحيات)
        else:
            os.system("shutdown -h now")  # أمر إغلاق الحاسوب في لينكس (قد يتطلب صلاحيات)   
             

    # دالة لإيقاف عملية التحميل الحالية
    def stop_current_download(self):
        """
        إيقاف عملية التحميل الحالية بعد تأكيد المستخدم
        """
        # التحقق من وجود عملية تحميل جارية
        if self.is_downloading:
            # طلب تأكيد من المستخدم قبل الإيقاف
            self.msg = CTkMessagebox(title="Exit?", message=self.lang.get("ask_to_stop_download", "Are you sure to stop the download?"),
                            icon="question", option_1="Cancel", option_2="No", option_3="Yes")
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
                    self.download_single_video(video['url'], playlist_title)
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
                    option_1="Cancel",
                    option_2="Select File"
                ).get()

                
                    
                if response == "Select File": # إذا اختار المستخدم تحديد ملف
                    # the dialog must run on the main thread; use Event to wait
                    file_event = threading.Event()
                    result = {"path": None}

                    def choose_file():
                        result["path"] = askopenfilename(
                            autocomplete=True,
                            style='Mini',
                            title="Select your cookies.txt file",
                            initial_dir=HOME,
                            filetypes=[("Text files", "*.txt")]
                        )
                        file_event.set()

                    self.root.after(0, choose_file)
                    file_event.wait()
                    selected_file = result.get("path")

                    if selected_file: # إذا تم اختيار ملف
                        self.cookiefile_dir = selected_file
                        # update label on main thread as well
                        self.cookiefile_label.configure(text=f"Cookies file: {self.cookiefile_dir}")
                        
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
