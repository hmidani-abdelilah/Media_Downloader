import customtkinter as ctk  # استيراد مكتبة واجهة المستخدم المخصصة
from PIL import Image, ImageTk # لتضمين أيقونة للتطبيق مهما كان نوع نظام التشغيل
import tkinter as tk  # استيراد مكتبة tkinter لإنشاء قائمة السياق
from customtkinter import filedialog  # لفتح مربع حوار اختيار الملفات
from CTkMessagebox import CTkMessagebox  # لعرض رسائل منبثقة للمستخدم
from downloader import download_video, stop_download, reset_stop_event, get_videos_info  # استيراد وظائف التحميل
from ffmpeg_check import check_ffmpeg_installed  # للتحقق من تثبيت FFmpeg
from aria2_check import check_aria2_installed # للتحقق من تثبيت Aria2c
import threading  # للتنفيذ المتزامن للمهام
import json  # للتعامل مع ملفات اللغة
import os  # للتعامل مع نظام الملفات
import sys  # للوصول إلى معلومات النظام

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
        self.root = root
        
        # تحميل أيقونة التطبيق من المسار الصحيح
        #icon_image = Image.open(os.path.join("asset", "Icon.ico"))
        #icon_tk = ImageTk.PhotoImage(icon_image)
        #self.root.wm_iconphoto(True, icon_tk)
        icon_path = self.resource_path(os.path.join("asset", "Icon.ico"))
        self.root.iconbitmap(icon_path)
        
        # تهيئة متغيرات اللغة والحالة
        self.lang = self.load_language(lang_code)
        self.lang_code = lang_code
        self.save_dir = os.path.expanduser("~")  # مجلد المستخدم الافتراضي كمسار حفظ
        self.current_download_thread = None  # خيط التنزيل الحالي
        self.is_downloading = False  # مؤشر على حالة التنزيل
    
        # إنشاء عناصر واجهة المستخدم
        self.create_widgets()

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
        return os.path.join(base_path, relative_path)    

    def load_language(self, lang_code):
        """
        تحميل ملف اللغة المناسب
        
        المعلمات:
            lang_code: رمز اللغة المطلوبة
            
        الإرجاع:
            قاموس يحتوي على ترجمات النصوص
        """
        try:
            with open(self.resource_path(f"languages/{lang_code}.json"), "r", encoding="utf-8") as f:
                lang_data = json.load(f)
            return lang_data
        except FileNotFoundError:
            print(f"File not found: languages/{lang_code}.json")
            # استخدام اللغة الإنجليزية كلغة افتراضية في حالة عدم وجود ملف اللغة المطلوبة
            try:
                with open(self.resource_path("languages/en.json"), "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}  # إرجاع قاموس فارغ في حالة عدم وجود أي ملف لغة

    def create_widgets(self):
        """
        إنشاء وتنظيم عناصر واجهة المستخدم الرسومية
        """
        # إنشاء الإطارات الرئيسية
        self.top_frame = ctk.CTkFrame(self.root)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ===== قسم إعدادات المظهر في الأعلى =====
        self.appearance_mode_label = ctk.CTkLabel(self.top_frame, text="Theme:")
        self.appearance_mode_label.pack(side="left", padx=5)
        
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_menu.pack(side="left", padx=5)
        
       
        # ===== قسم إعدادات اللغة =====
        self.language_menu = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["en", "ar", "fr"],  # اللغات المدعومة: الإنجليزية والعربية والفرنسية
            command=self.change_language
        )
        self.language_menu.set(self.lang_code)
        self.language_menu.pack(side="right", padx=5)
        
        self.language_label = ctk.CTkLabel(self.top_frame, text="Language:")
        self.language_label.pack(side="right", padx=5)
        
        # ===== عنوان التطبيق =====
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text=self.lang.get("title", "Media Downloader"), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        # ===== قسم إدخال رابط الفيديو =====
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.pack(fill="x", padx=20, pady=5)
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame, 
            placeholder_text=self.lang.get("enter_url", "Enter Media URL"), 
            width=400
        )
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)

        
        # إنشاء قائمة منبثقة (Popup menu) بدون حافة علوية
        self.menu = tk.Menu(self.url_frame, tearoff=0)
        
        # إضافة عنصر "لصق" إلى القائمة وربطه بالدالة paste
        self.menu.add_command(label=self.lang.get("paste", "Paste"), command=self.paste)  # إضافة أمر "لصق" للقائمة
       
        # ربط حدث النقر بزر الفأرة الأيمن (الزر رقم 3) بالحقل لعرض القائمة
        self.url_entry.bind("<Button-3>", self.show_menu)

       # زر المسح
        self.clear_button = ctk.CTkButton(
            self.url_frame,
            text=self.lang.get("clear", "Clear"),
            command=self.clear_url
        )
        self.clear_button.pack(side="right", padx=5)
        
        # ===== قسم الإعدادات =====
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(fill="x", padx=20, pady=10)
        
        # إعدادات نوع الملف
        self.filetype_label = ctk.CTkLabel(self.settings_frame, text="Format:")
        self.filetype_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.file_type = ctk.StringVar(value="best")
        self.type_menu = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=["best","mp4", "mp3"],  # أنواع الملفات المتاحة
            variable=self.file_type
        )
        self.type_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # إعدادات الجودة
        self.quality_label = ctk.CTkLabel(self.settings_frame, text="Quality:")
        self.quality_label.grid(row=0, column=2, padx=5, pady=5)
        
        self.quality = ctk.StringVar(value="medium")
        self.quality_menu = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=["low", "medium", "high"],  # مستويات الجودة المتاحة
            variable=self.quality
        )
        self.quality_menu.grid(row=0, column=3, padx=5, pady=5)
        
        # خيار تحميل الترجمة
        self.subtitles = ctk.BooleanVar(value=False)
        self.sub_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("download_subtitles", "Download Subtitles"), 
            variable=self.subtitles
        )
        self.sub_checkbox.grid(row=0, column=4, padx=5, pady=5)
        
        # خيار تحميل بادات Aria2c
        self.aria2c = ctk.BooleanVar(value=False)
        self.aria2_checkbox = ctk.CTkCheckBox(
            self.settings_frame, 
            text=self.lang.get("use_aria2", "Download with aria2"), 
            variable=self.aria2c
        )
        self.aria2_checkbox.grid(row=0, column=5, padx=5, pady=5)

        # ===== قسم اختيار مجلد الحفظ =====
        self.directory_frame = ctk.CTkFrame(self.main_frame)
        self.directory_frame.pack(fill="x", padx=20, pady=5)
        
        self.directory_label = ctk.CTkLabel(self.directory_frame, text=f"Directory: {self.save_dir}")
        self.directory_label.pack(side="left", padx=5, fill="x", expand=True)
        
        self.select_button = ctk.CTkButton(
            self.directory_frame, 
            text=self.lang.get("select_directory", "Select Directory"), 
            command=self.select_directory
        )
        self.select_button.pack(side="right", padx=5)
        
        # ===== قسم عرض حالة التحميل والتقدم =====
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="")
        self.status_label.pack(pady=5)
        
        self.progress = ctk.CTkProgressBar(self.status_frame, width=400)
        self.progress.set(0)  # تعيين قيمة البداية للتقدم
        self.progress.pack(pady=5)
        
        # ===== أزرار التحميل والإيقاف =====
        self.buttons_frame = ctk.CTkFrame(self.main_frame)
        self.buttons_frame.pack(fill="x", padx=20, pady=10)
        
        self.download_button = ctk.CTkButton(
            self.buttons_frame, 
            text=self.lang.get("download", "Download"), 
            command=self.start_download
        )
        self.download_button.pack(side="left", padx=5, expand=True, fill="x")
        
        self.stop_button = ctk.CTkButton(
            self.buttons_frame, 
            text=self.lang.get("stop_download", "Stop Download"), 
            command=self.stop_current_download,
            state="disabled"  # معطل في البداية حتى يبدأ التحميل
        )
        self.stop_button.pack(side="right", padx=5, expand=True, fill="x")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """
        تغيير مظهر التطبيق (فاتح/داكن/نظام)
        
        المعلمات:
            new_appearance_mode: المظهر الجديد المحدد
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def change_language(self, lang_code: str):
        """
        تغيير لغة واجهة التطبيق
        
        المعلمات:
            lang_code: رمز اللغة الجديدة
        """
        self.lang_code = lang_code
        self.lang = self.load_language(lang_code)
        
        # تحديث نصوص جميع عناصر الواجهة بالترجمة الجديدة
        self.title_label.configure(text=self.lang.get("title", "YouTube Downloader"))
        self.url_entry.configure(placeholder_text=self.lang.get("enter_url", "Enter YouTube URL"))
        self.clear_button.configure(text=self.lang.get("clear", "Clear"))
        self.download_button.configure(text=self.lang.get("download", "Download"))
        self.sub_checkbox.configure(text=self.lang.get("download_subtitles", "Download Subtitles"))
        self.aria2_checkbox.configure(text=self.lang.get("use_aria2", "Download with aria2"))
        self.select_button.configure(text=self.lang.get("select_directory", "Select Directory"))
        self.stop_button.configure(text=self.lang.get("stop_download", "Stop Download"))

    # دالة للّصق من الحافظة إلى الحقل
    def paste(self):
        try:
            url = self.url_frame.clipboard_get()         # محاولة الحصول على النص من الحافظة
        except tk.TclError:
            return                                       # إذا فشلت (لا يوجد شيء في الحافظة)، لا تفعل شيئًا
        self.url_entry.delete(0, ctk.END)              # مسح ما بداخل الحقل
        self.url_entry.insert("end", url)             # إدراج النص في نهاية حقل الإدخال

    # دالة لإظهار القائمة عند النقر بزر الفأرة الأيمن
    def show_menu(self,event):
        try:
            # عرض القائمة في موضع مؤشر الفأرة
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            # تحرير التحكم بالقائمة (ضروري أحيانًا لتجنب تجميد القائمة)
            self.menu.grab_release()


    def clear_url(self):
        """
        مسح حقل رابط URL وإعادة تعيين مؤشرات الحالة
        """
        self.url_entry.delete(0, ctk.END)
        self.status_label.configure(text="")
        self.progress.set(0)

    def select_directory(self):
        """
        فتح مربع حوار لاختيار مجلد حفظ الملفات
        """
        selected = filedialog.askdirectory()
        if selected:
            self.save_dir = selected
            self.directory_label.configure(text=f"Directory: {self.save_dir}")

    def start_download(self):
        """
        بدء عملية تحميل الفيديو أو قائمة التشغيل
        """
        # التحقق من وجود FFmpeg المطلوب للتحويل
        ffmeg = check_ffmpeg_installed()

        # التحقق من وجود Aria2c المطلوب للتحويل
        aria2c = check_aria2_installed()

        url = self.url_entry.get().strip()
                
        if not url:
            # إظهار تحذير إذا لم يتم إدخال رابط
            CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("please_enter_url", "Please enter a URL."), 
                icon="warning"
            )
            return
        
        elif not ffmeg:
             # إظهار خطأ إذا لم يتم تثبيت FFmpeg
             CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=self.lang.get("please_install_ffmpeg", "Please install FFmpeg."), 
                icon="cancel"
            )
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

    def stop_current_download(self):
        """
        إيقاف عملية التحميل الحالية بعد تأكيد المستخدم
        """
        if self.is_downloading:
            # طلب تأكيد من المستخدم قبل الإيقاف
            self.msg = CTkMessagebox(title="Exit?", message=self.lang.get("ask_to_stop_download", "Are you sure to stop the download?"),
                            icon="question", option_1="Cancel", option_2="No", option_3="Yes")
            self.response = self.msg.get()
            if self.response == "Yes":
                # إيقاف التحميل وإعادة تعيين حالة التطبيق
                stop_download()
                self.status_label.configure(text=self.lang.get("download_stopped", "Download stopped."))
                
                # إعادة تفعيل زر التحميل وتعطيل زر الإيقاف
                self.download_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.is_downloading = False

    def prepare_and_download(self, url):
        """
        تحضير وتحميل الفيديوهات من الرابط (قد يكون فيديو واحد أو قائمة تشغيل)
        
        المعلمات:
            url: رابط الفيديو أو قائمة التشغيل
        """
        try:
            # جلب معلومات الفيديوهات من الرابط
            result = get_videos_info(url)
            videos = result["videos"]
            playlist_title = result["playlist_title"]
            
            total = len(videos)
            
            if total == 0:
                # إذا لم يتم العثور على فيديوهات
                self.status_label.configure(text=self.lang.get("no_videos_found", "No videos found"))
                self.download_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.is_downloading = False
                return
            
            # تحميل كل فيديو في القائمة
            for idx, video in enumerate(videos, start=1):
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
            self.status_label.configure(text=str(e))
            CTkMessagebox(
                title=self.lang.get("error", "Error"), 
                message=str(e), 
                icon="cancel"
            )
        finally:
            # إعادة تعيين حالة التطبيق بغض النظر عن نتيجة التحميل
            self.download_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.is_downloading = False

    def download_single_video(self, url, playlist_title=None):
        """
        تحميل فيديو واحد مع تتبع التقدم
        
        المعلمات:
            url: رابط الفيديو المراد تحميله
            playlist_title: عنوان قائمة التشغيل (إن وجدت)
        """
        try:
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
                progress_hook=progress_hook,
                playlist_title=playlist_title,
                use_aria2=self.aria2c.get()
            )
        except Exception as e:
            raise e  # إعادة رفع الاستثناء للتعامل معه في الدالة الأعلى
