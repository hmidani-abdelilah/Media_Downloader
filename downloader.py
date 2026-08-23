# downloader.py
import time
import subprocess
import yt_dlp as youtube_dl #  استيراد مكتبة yt_dlp لتحميل الفيديوهات من يوتيوب ومنصات أخرى
import os # استيراد مكتبة التعامل مع نظام الملفات
import threading # استيراد مكتبة threading لدعم العمليات المتعددة
import re # استيراد مكتبة التعبيرات النمطية للتعامل مع النصوص
import urllib.parse
from utils import resource_path # استيراد الدالة resource_path من ملف utils
from path_ffmpeg import ffmpeg_find_path # استيراد دالة تحديد مسار ffmpeg من ملف path_ffmpeg
from convert import compress_video, get_gpu_encoders, is_encoder_supported # استيراد دوال الضغط والترميزات من ملف convert
# تحديد مسار ffmpeg من داخل bin
# مجلد ffmpeg
ffmpeg_path = ffmpeg_find_path()
# تحديد مسار aria2c من داخل مجلد aria2
ARIA2C_PATH = resource_path("aria2/aria2c.exe")
#cookies_path = resource_path("www.youtube.com_cookies.txt")  # أو المسار الذي تضع فيه الكوكيز

DEFAULT_SUBTITLE_LANGUAGES = ("ar", "fr", "en")
YOUTUBE_SUBTITLE_DELAY = 60
YTDLP_JS_RUNTIMES = ("deno", "node", "quickjs")

SUBTITLE_LANGUAGE_ALIASES = {
    "arabic": "ar",
    "العربية": "ar",
    "عربي": "ar",
    "french": "fr",
    "français": "fr",
    "francais": "fr",
    "الفرنسية": "fr",
    "فرنسي": "fr",
    "english": "en",
    "الإنجليزية": "en",
    "الانجليزية": "en",
    "إنجليزي": "en",
    "انجليزي": "en",
}

# متغير تحكم لإيقاف التحميل
stop_event = threading.Event()

# -------------- دوال التحكم في الإيقاف --------------
def reset_stop_event():
    """إعادة تعيين حدث الإيقاف"""
    stop_event.clear()

# -------------- دوال التحكم في الإيقاف --------------
def stop_download():
    """تعيين حدث الإيقاف لإيقاف التحميل الحالي"""
    stop_event.set()


# -------------- دوال مساعدة --------------
def get_js_runtime_options():
    """تفعيل محركات JavaScript التي يدعمها yt-dlp."""
    return {
        runtime: {}
        for runtime in YTDLP_JS_RUNTIMES
    }


def is_youtube_url(url):
    """التحقق من أن الرابط تابع لـ YouTube."""
    try:
        hostname = (
            urllib.parse.urlparse(str(url)).hostname or ""
        ).casefold()
    except Exception:
        return False

    return (
        hostname == "youtu.be"
        or hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
        or hostname == "youtube-nocookie.com"
        or hostname.endswith(".youtube-nocookie.com")
    )


def get_format(quality, file_type):
    """
    تحديد صيغة التحميل بناءً على الجودة ونوع الملف
    
    Args:
        quality: الجودة المطلوبة (Low (360), Medium (720), High (1080), Ultra (1440))
        file_type: نوع الملف (mp3 أو mp4)

    Returns:
        الصيغة المناسبة لاستخدامها في yt_dlp
    """
    # تحويل الجودة إلى ارتفاع بكسل
    quality_map = {
        'low': '360',
        'low (360)': '360',
        'medium': '720',
        'medium (720)': '720',
        'high': '1080',
        'high (1080)': '1080',
        'ultra': '1440',
        'ultra (1440)': '1440',
    }
    quality_key = str(quality).strip().lower()
    quality_value = quality_map.get(quality_key, '720')
    
    # تحديد الصيغة بناءً على نوع الملف
    if file_type == 'mp3':
        # تحميل أفضل صوت فقط
        return f'bestaudio[ext=m4a]/best[height<={quality_value}]'
    else:
        # تحميل فيديو وصوت ودمجهما
        return f'bv*[height<={quality_value}]+ba/best'

# -------------- جلب معلومات الفيديو --------------
def get_videos_info(url,cookies_path="\U0001F36A",ffmpeg_path=ffmpeg_path):
    """
    جلب معلومات الفيديوهات (العنوان والرابط) من الرابط المدخل (فيديو أو قائمة تشغيل)

    Args:
                 url: رابط الفيديو أو قائمة التشغيل
        cookies_path: استخدام cookies لحل مشاكل الفيديوهات المحمية 
        ffmpeg_path: مسار اذات ffmpeg من مجلد جانبي ان وجد والى فمن النظام
    Returns:
        dict يحتوي على قائمة الفيديوهات والعنوان إذا كانت قائمة تشغيل
    """
    # إعداد خيارات yt_dlp
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "socket_timeout": 30,
        "js_runtimes": get_js_runtime_options(),
        # Explicitly verify SSL (should be default, but verify)
    }

    # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path != "ffmpeg":
        # تحديد مسار ffmpeg في الخيارات
        ydl_opts['ffmpeg_location'] = ffmpeg_path
        
    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":

        if os.path.exists(cookies_path):
            # # إضافة مسار ملف الكوكيز إلى الخيارات
            # ydl_opts['cookiefile'] = cookies_path
            # #ydl_opts['nocheckcertificate'] = True  # تجاهل التحقق من الشهادة إذا كان هناك مشاكل مع الكوكيز
            # # pass "--extractor-args youtubetab:skip=authcheck" to skip this check
            # #ydl_opts['extractor_args'] = {'youtube': {'skip': 'authcheck'}}
            # ydl_opts['extractor_args'] = {'youtube': {'player_client': ['default', 'web_embedded']}}
            # # Correction de 'js_runtimes' en dictionnaire
            # ydl_opts['js_runtimes'] = {'node': {'path': None}}

            # # 'remote_components' reste une liste (C'est correct !)
            # ydl_opts['remote_components'] = ['ejs:github']
            
            # # 1. FORCER LES CLIENTS WEB COMPATIBLES AVEC LES COOKIES
            # 1. Ajout du chemin du fichier de cookies
            ydl_opts['cookiefile'] = cookies_path
            
            # 2. Configuration groupée de TOUS les extractor_args (Sans écrasement)
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['default', 'web_embedded']
                },
                'youtubetab': {
                    'skip': ['authcheck']  # Équivalent correct de --extractor-args youtubetab:skip=authcheck
                }
            }
            
            # Optionnel : Ignorer la vérification des certificats SSL si nécessaire
            # ydl_opts['nocheckcertificate'] = True


            

    # جلب معلومات الفيديو باستخدام yt_dlp
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات دون تحميل الفيديو
            info = ydl.extract_info(url, download=False)
            videos = []
            playlist_title = None
            
            # إذا كان الرابط لقائمة تشغيل، نحفظ عنوان القائمة
            if "entries" in info:

                playlist_title = info.get("title", "playlist")
                # روابط الفيديوهات داخل قائمة التشغيل
                for entry in info["entries"]:
                    # تحقق من وجود البيانات قبل الإضافة
                    if not entry:
                        continue

                    title = entry.get("title", "No Title")
                    video_url = None
                    is_playlist_item = False

                    # Prefer explicit webpage_url if provided by extractor
                    if entry.get("webpage_url"):
                        video_url = entry.get("webpage_url")
                    # Some extractors provide a full URL in 'url'
                    elif entry.get("url"):
                        u = entry.get("url")
                        if isinstance(u, str):
                            # If it's already an absolute URL
                            if u.startswith("http"):
                                video_url = u
                            # Relative YouTube paths like '/playlist?list=...'
                            elif u.startswith("/") or u.startswith("playlist") or "list=" in u:
                                # ensure leading slash for proper join
                                path = u if u.startswith("/") else "/" + u
                                video_url = urllib.parse.urljoin("https://www.youtube.com", path)
                            # If it's a video id (e.g. YouTube 11-char id)
                            elif re.match(r'^[A-Za-z0-9_-]{11}$', u):
                                video_url = f"https://www.youtube.com/watch?v={u}"
                            else:
                                # fallback: attempt to join with youtube domain
                                video_url = urllib.parse.urljoin("https://www.youtube.com", u)
                    # If only 'id' exists, try to build a YouTube watch URL (common case)
                    elif entry.get("id"):
                        eid = entry.get("id")
                        if isinstance(eid, str) and re.match(r'^[A-Za-z0-9_-]{11}$', eid):
                            video_url = f"https://www.youtube.com/watch?v={eid}"
                        else:
                            # If id is not a plain video id, try to use it as-is
                            video_url = entry.get("id")

                    # As a last resort, try to construct something reasonable or skip
                    if not video_url:
                        continue

                    # Mark only non-video playlist entries for channel playlist pages
                    if entry.get("id") and not re.match(r'^[A-Za-z0-9_-]{11}$', str(entry.get("id"))) and video_url and "playlist?list=" in video_url:
                        is_playlist_item = True

                    item = {
                        "title": title,
                        "url": video_url
                    }
                    if is_playlist_item:
                        item["sub_dir_title"] = title
                        item["item_type"] = "playlist"

                    videos.append(item)
            else:
                # رابط لفيديو فردي
                videos.append({
                    "title": info.get("title", "No Title"),
                    "url": url
                })
            
            # إرجاع المعلومات المطلوبة
            channel_title = info.get("uploader") or info.get("channel") or info.get("uploader_id") or info.get("channel_id")
            if isinstance(channel_title, str):
                channel_title = channel_title.strip()
            else:
                channel_title = None

            return {
                "videos": videos,
                "playlist_title": playlist_title,
                "channel_title": channel_title
            }
    # التعامل مع أخطاء استخراج المعلومات
    except Exception as e:
        raise Exception(f"Error fetching video info: {str(e)}")

# -------------- تنظيف اسم الملف --------------
def sanitize_filename(filename):
    """
    تنظيف اسم الملف من الأحرف غير المسموح بها في أسماء المجلدات

    Args:
        filename: اسم الملف الأصلي

    Returns:
        اسم الملف بعد التنظيف
    """
    # إزالة الأحرف غير المسموح بها
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # إزالة المسافات المتكررة
    filename = re.sub(r'\s+', " ", filename)
    # تقليص طول الاسم إذا كان طويلاً جداً
    if len(filename) > 100:
        filename = filename[:97] + "..."
        # إرجاع الاسم المنظف
    return filename.strip()

# -------------- تنظيف مسار الدليل --------------
def sanitize_path(path):
    """
    تنظيف مسار دليل متعدد المستويات مع الحفاظ على بنية المجلد.
    """
    if not path:
        return ""
    parts = re.split(r'[\\/]+', str(path))
    sanitized_parts = [sanitize_filename(part) for part in parts if part]
    return os.path.join(*sanitized_parts) if sanitized_parts else ""


def _normalize_subtitle_language(language):
    """تطبيع رمز/اسم لغة الترجمة للمطابقة."""
    normalized = str(language).strip().replace("_", "-").casefold()
    return SUBTITLE_LANGUAGE_ALIASES.get(normalized, normalized)


def parse_subtitle_languages(subtitle_languages):
    """
    تحويل الإدخال إلى قائمة لغات دون تكرار.

    الإدخال الفارغ يعني العربية والفرنسية والإنجليزية.
    يمكن فصل أكثر من لغة بفاصلة أو فاصلة منقوطة.
    """
    value = "" if subtitle_languages is None else str(subtitle_languages).strip()
    raw_languages = (
        re.split(r"[,;]+", value)
        if value
        else DEFAULT_SUBTITLE_LANGUAGES
    )

    languages = []
    for language in raw_languages:
        normalized = _normalize_subtitle_language(language)
        if normalized and normalized not in languages:
            languages.append(normalized)

    return languages or list(DEFAULT_SUBTITLE_LANGUAGES)


def resolve_subtitle_languages(
    subtitle_languages,
    manual_subtitles,
    automatic_captions
):
    """مطابقة اللغات المطلوبة مع رموز yt-dlp المتاحة."""
    requested_languages = parse_subtitle_languages(subtitle_languages)
    manual_subtitles = manual_subtitles or {}
    automatic_captions = automatic_captions or {}
    available_languages = list(dict.fromkeys(
        list(manual_subtitles.keys()) + list(automatic_captions.keys())
    ))

    selected_languages = []
    missing_languages = []

    for requested_language in requested_languages:
        normalized_requested = _normalize_subtitle_language(
            requested_language
        )

        matched_language = next(
            (
                available_language
                for available_language in available_languages
                if _normalize_subtitle_language(available_language)
                == normalized_requested
            ),
            None
        )

        # نطابق البدائل (fr-FR مثلًا) فقط عند طلب رمز عام
        # مثل fr. أما pt-BR فلا ينبغي استبداله بـ pt-PT.
        if matched_language is None and "-" not in normalized_requested:
            requested_base = normalized_requested.split("-", 1)[0]
            matched_language = next(
                (
                    available_language
                    for available_language in available_languages
                    if _normalize_subtitle_language(
                        available_language
                    ).split("-", 1)[0] == requested_base
                ),
                None
            )

        if matched_language is None:
            missing_languages.append(requested_language)
        elif matched_language not in selected_languages:
            selected_languages.append(matched_language)

    return selected_languages, missing_languages

# ==============================================================
# أدوات القص ومعالجة الترجمة
# ==============================================================

def parse_media_time(value):
    """
    تحويل الوقت إلى ثوانٍ.

    أمثلة:
        90          -> 90 ثانية
        1:30        -> 90 ثانية
        01:30:00    -> 5400 ثانية
        1h30m       -> 5400 ثانية
        1h30m20s    -> 5420 ثانية
    """
    value = str(value).strip()

    if not value:
        raise ValueError("قيمة الوقت فارغة")

    # رقم فقط = ثواني
    if re.fullmatch(r'\d+(?:\.\d+)?', value):
        return float(value)

    # MM:SS
    if re.fullmatch(r'\d+:\d{1,2}', value):
        minutes, seconds = map(int, value.split(':'))
        if seconds >= 60:
            raise ValueError(f"صيغة الوقت غير صحيحة: {value}")
        return minutes * 60 + seconds

    # HH:MM:SS
    if re.fullmatch(r'\d+:\d{1,2}:\d{1,2}', value):
        hours, minutes, seconds = map(int, value.split(':'))
        if minutes >= 60 or seconds >= 60:
            raise ValueError(f"صيغة الوقت غير صحيحة: {value}")
        return hours * 3600 + minutes * 60 + seconds

    # 1h30m20s
    pattern = re.compile(
        r'^(?:(\d+(?:\.\d+)?)h)?'
        r'(?:(\d+(?:\.\d+)?)m)?'
        r'(?:(\d+(?:\.\d+)?)s)?$',
        re.IGNORECASE
    )
    match = pattern.fullmatch(value)

    if match and any(match.groups()):
        hours = float(match.group(1) or 0)
        minutes = float(match.group(2) or 0)
        seconds = float(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"صيغة الوقت غير مدعومة: {value}")


def _ffprobe_path(ffmpeg_location):
    """تحديد مسار ffprobe انطلاقًا من مسار ffmpeg عند الحاجة."""
    if not ffmpeg_location or ffmpeg_location == "ffmpeg":
        return "ffprobe"

    if os.path.isfile(ffmpeg_location):
        candidate = os.path.join(
            os.path.dirname(ffmpeg_location),
            "ffprobe.exe" if os.name == "nt" else "ffprobe"
        )
        if os.path.exists(candidate):
            return candidate

    if os.path.isdir(ffmpeg_location):
        candidate = os.path.join(
            ffmpeg_location,
            "ffprobe.exe" if os.name == "nt" else "ffprobe"
        )
        if os.path.exists(candidate):
            return candidate

    return "ffprobe"


def get_media_duration(file_path, ffmpeg_location="ffmpeg"):
    """الحصول على مدة ملف فيديو/صوت بالثواني."""
    result = subprocess.run(
        [
            _ffprobe_path(ffmpeg_location),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        raise Exception(
            f"تعذر معرفة مدة الملف:\n{result.stderr}"
        )

    try:
        return float(result.stdout.strip())
    except Exception:
        raise Exception("تعذر قراءة مدة الملف")


def format_subtitle_timestamp(seconds, vtt=False):
    """تحويل الثواني إلى توقيت SRT أو WebVTT."""
    seconds = max(0.0, float(seconds))

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole_seconds = int(seconds % 60)
    milliseconds = int(round(
        (seconds - int(seconds)) * 1000
    ))

    if milliseconds >= 1000:
        whole_seconds += 1
        milliseconds = 0

    if whole_seconds >= 60:
        whole_seconds = 0
        minutes += 1

    if minutes >= 60:
        minutes = 0
        hours += 1

    separator = "." if vtt else ","

    return (
        f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}"
        f"{separator}{milliseconds:03d}"
    )


def parse_subtitle_timestamp(value):
    """تحويل توقيت SRT/VTT إلى ثوانٍ."""
    value = value.strip().replace(",", ".")
    parts = value.split(":")

    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"توقيت ترجمة غير صالح: {value}")


def shift_subtitle_file(subtitle_path, cut_start, cut_end):
    """
    تعديل توقيت SRT/VTT ليتوافق مع المقطع المقصوص.

    يتم:
    - حذف الترجمة الواقعة بالكامل خارج المقطع.
    - قص أي subtitle يتقاطع مع حدود المقطع.
    - طرح cut_start من كل التوقيتات.
    """
    if not os.path.isfile(subtitle_path):
        return False

    extension = os.path.splitext(subtitle_path)[1].lower()
    if extension not in (".srt", ".vtt"):
        return False

    is_vtt = extension == ".vtt"

    with open(
        subtitle_path,
        "r",
        encoding="utf-8-sig"
    ) as f:
        content = f.read()

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n{2,}", content.strip())

    timestamp_pattern = re.compile(
        r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})"
        r"\s*-->\s*"
        r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})"
    )

    new_blocks = []

    for block in blocks:
        match = timestamp_pattern.search(block)

        # WEBVTT header
        if not match:
            if is_vtt and block.strip().upper().startswith("WEBVTT"):
                new_blocks.append(block)
            elif not is_vtt:
                # SRT may contain numeric cue IDs or other non-timestamp blocks.
                # We only keep them if they belong to a cue; standalone blocks
                # are harmless to preserve.
                if block.strip():
                    new_blocks.append(block)
            continue

        original_start = parse_subtitle_timestamp(
            match.group("start")
        )
        original_end = parse_subtitle_timestamp(
            match.group("end")
        )

        # لا يوجد تقاطع مع المقطع
        if original_end <= cut_start or original_start >= cut_end:
            continue

        clipped_start = max(original_start, cut_start)
        clipped_end = min(original_end, cut_end)

        if clipped_end <= clipped_start:
            continue

        new_start = clipped_start - cut_start
        new_end = clipped_end - cut_start

        replacement = (
            f"{format_subtitle_timestamp(new_start, is_vtt)}"
            f" --> "
            f"{format_subtitle_timestamp(new_end, is_vtt)}"
        )

        new_block = timestamp_pattern.sub(
            replacement,
            block,
            count=1
        )

        new_blocks.append(new_block)

    new_content = "\n\n".join(new_blocks)

    if is_vtt and not new_content.startswith("WEBVTT"):
        new_content = "WEBVTT\n\n" + new_content

    with open(
        subtitle_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(new_content.rstrip() + "\n")

    return True


def find_subtitle_files(media_file, directory):
    """العثور على SRT/VTT التابعة لملف الوسائط."""
    if not os.path.isdir(directory):
        return []

    media_base = os.path.splitext(
        os.path.basename(media_file)
    )[0]

    result = []

    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".srt", ".vtt"):
            continue

        subtitle_base = os.path.splitext(filename)[0]

        if subtitle_base.startswith(media_base + "."):
            result.append(full_path)

    return sorted(result)


def process_cut_subtitles(
    subtitle_files,
    cut_start,
    cut_end
):
    """تعديل جميع ملفات الترجمة بعد القص."""
    for subtitle_file in subtitle_files:
        try:
            shift_subtitle_file(
                subtitle_file,
                cut_start,
                cut_end
            )
        except Exception as e:
            print(
                f"Subtitle processing failed for "
                f"{subtitle_file}: {e}"
            )


def cut_downloaded_media(
    input_file,
    start_time,
    end_time="-1",
    ffmpeg_path="ffmpeg",
    file_type=None,
    stop_event=None
):
    """
    قص فيديو أو صوت بعد انتهاء yt-dlp.

    الرقم فقط يعني ثواني:
        90 = 90 ثانية

    end_time='-1' يعني نهاية الملف.
    """
    if not input_file or not os.path.isfile(input_file):
        raise Exception(
            f"Cannot find downloaded file to cut: {input_file}"
        )

    start = parse_media_time(start_time)

    if start < 0:
        raise ValueError(
            "وقت البداية لا يمكن أن يكون سالبًا"
        )

    if str(end_time).strip() == "-1":
        end = get_media_duration(
            input_file,
            ffmpeg_path
        )
    else:
        end = parse_media_time(end_time)

    if end <= start:
        raise ValueError(
            f"وقت النهاية ({end_time}) يجب أن يكون "
            f"أكبر من وقت البداية ({start_time})"
        )

    duration = end - start

    if stop_event and stop_event.is_set():
        raise Exception("Download stopped by user")

    ffmpeg_exe = ffmpeg_path or "ffmpeg"

    directory = os.path.dirname(
        os.path.abspath(input_file)
    )
    filename = os.path.basename(input_file)
    base, ext = os.path.splitext(filename)

    output_file = os.path.join(
        directory,
        f"{base}_cut{ext}"
    )

    audio_types = {
        "mp3", "aac", "flac", "wav", "opus",
        "alac", "m4a", "ogg"
    }

    is_audio = (
        str(file_type).lower() in audio_types
        or ext.lower().lstrip(".") in audio_types
    )

    if is_audio:
        cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start),
            "-i", input_file,
            "-t", str(duration),
            "-vn",
        ]

        ext_lower = ext.lower()

        if ext_lower == ".mp3":
            cmd += ["-c:a", "libmp3lame", "-q:a", "2"]
        elif ext_lower == ".wav":
            cmd += ["-c:a", "pcm_s16le"]
        elif ext_lower == ".flac":
            cmd += ["-c:a", "flac"]
        elif ext_lower in (".m4a", ".aac"):
            cmd += ["-c:a", "aac", "-b:a", "192k"]
        elif ext_lower == ".ogg":
            cmd += ["-c:a", "libvorbis", "-q:a", "4"]
        elif ext_lower == ".opus":
            cmd += ["-c:a", "libopus", "-b:a", "192k"]
        else:
            cmd += ["-c:a", "copy"]

    else:
        cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start),
            "-i", input_file,
            "-t", str(duration),
            "-map", "0:v:0?",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-movflags", "+faststart",
        ]

    cmd.append(output_file)

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        raise Exception(
            f"فشل قص الملف:\n{result.stderr}"
        )

    if not os.path.isfile(output_file):
        raise Exception(
            "FFmpeg انتهى بدون إنشاء الملف المقصوص."
        )

    return output_file, start, end



# -------------- ضغط الفيديو بعد التحميل --------------
def compress_downloaded_video(
    downloaded_path,
    file_type,
    final_download_dir,
    encoder='libx264',
    crf=23,
    preset='medium',
    copy_codec=False,
    stop_event=None,
    progress_hook=None,
) -> str:
    """Compress a downloaded video file after yt-dlp finishes.

    This helper keeps the compression logic separate from download logic so the
    UI can show compression state and the stop event can cancel ffmpeg.
    """
    video_containers = {'mp4', 'mkv', 'avi', 'flv', 'webm', 'mov'}
    if file_type not in video_containers:
        return downloaded_path

    base_name = os.path.splitext(os.path.basename(downloaded_path))[0]
    out_ext = file_type
    out_file = os.path.join(final_download_dir, f"compressed_{base_name}.{out_ext}")
    final_encoder = encoder

    if out_ext == 'webm':
        webm_encoders = ['libaom-av1', 'libvpx-vp9', 'libvpx']
        found = None
        for e in webm_encoders:
            try:
                if is_encoder_supported(e):
                    found = e
                    break
            except Exception:
                continue
        if found:
            final_encoder = found
        else:
            if is_encoder_supported('libx264'):
                #print('No WebM encoder available; switching compressed output to MP4 using libx264')
                out_file = os.path.join(final_download_dir, f"compressed_{base_name}.mp4")
                final_encoder = 'libx264'
            else:
                raise Exception('No WebM encoder (libvpx/libaom) available. Install one or choose MP4/MKV output.')

    if progress_hook:
        progress_hook({'status': 'compressing'})

    compress_video(
        downloaded_path,
        out_file,
        encoder=final_encoder,
        crf=crf,
        preset=preset,
        copy_codec=copy_codec,
        stop_event=stop_event,
    )
    return out_file

# تابع التحميل الرئيسي مع دعم GPU
# -------------- تحميل الفيديو --------------
def download_video(url, download_dir, quality, file_type, download_subtitles, progress_hook=None, playlist_title=None,ffmpeg_path=ffmpeg_path, use_aria2=False , cookies_path="\U0001F36A" , encoder='libx264', crf=23, preset='medium', copy_codec=False, cut_enabled=False, cut_start='0', cut_end='-1', subtitle_languages=None):
    """

    تحميل فيديو من يوتيوب باستخدام yt-dlp و Aria2 (اختياري) و cookies (إختياري)

    

    Args:

        url: رابط الفيديو

        download_dir: مجلد التحميل

        quality: جودة الفيديو ('Low (360)', 'Medium (720)', 'High (1080)', 'Ultra (1440)')

        file_type: نوع الملف ('mp3', 'mp4', 'mkv', 'avi', 'flv', 'webm', 'opus', 'aac', 'flac', 'wav', 'alac', 'm4a', 'ogg')

        download_subtitles: هل يجب تحميل الترجمة

        progress_hook: دالة لتتبع التقدم

        playlist_title: عنوان قائمة التشغيل (إن وجد)

        ffmpeg_path: مسار اذات ffmpeg من مجلد جانبي ان وجد والى فمن النظام

        use_aria2: هل سيتم استخدام Aria2 كأداة تحميل خارجية (اختياري)

        cookies_path: استخدام cookies لحل مشاكل الفيديوهات المحمية 

        cut_enabled: تفعيل قص الفيديو/الصوت بعد التحميل
        
        cut_start: بداية القص (الرقم فقط = ثواني)
        
        cut_end: نهاية القص (-1 = نهاية الملف)
        
        subtitle_languages: لغات الترجمة مفصولة بفواصل، والفارغ يعني ar,fr,en

    """
    
    # إعادة تعيين حدث الإيقاف قبل بدء التحميل
    reset_stop_event()
    
    # دالة للتحقق من حالة الإيقاف
    def custom_progress_hook(d):
        # التحقق من حالة الإيقاف
        if stop_event.is_set():
            raise Exception("Download stopped by user")
        # استدعاء دالة التقدم الأصلية إذا كانت موجودة
        if progress_hook:
            # تمرير حالة التقدم إلى الدالة الأصلية
            progress_hook(d)
    
    # إنشاء مجلد لقائمة التشغيل إذا تم تحديدها
    final_download_dir = download_dir
    if playlist_title:
        sanitized_playlist_title = sanitize_path(playlist_title)
        if sanitized_playlist_title:
            playlist_dir = os.path.join(download_dir, sanitized_playlist_title)
            if not os.path.exists(playlist_dir):
                os.makedirs(playlist_dir, exist_ok=True)
            final_download_dir = playlist_dir
    
    # إعداد خيارات yt_dlp
    options = {
        'format': get_format(quality, file_type),
        'outtmpl': os.path.join(final_download_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'progress_hooks': [custom_progress_hook],
        'js_runtimes': get_js_runtime_options(),
    }

    # ✅ التحقق من ffmpeg المحلي
    if ffmpeg_path != "ffmpeg" :
        options['ffmpeg_location'] = ffmpeg_path
        
    # ✅ إضافة الكوكيز إن وجد
    if cookies_path != "\U0001F36A":
        if os.path.exists(cookies_path):
            options['cookiefile'] = cookies_path
    
    # إعدادات Aria2c
    # إذا كان سيتم استخدام Aria2 كأداة تنزيل خارجية
    if use_aria2:
        # إعدادات التحميل المتقدمة لـ Aria2
        downloader_args = ['--min-split-size=1M', 
                            '--max-connection-per-server=16', 
                            '--max-concurrent-downloads=16', 
                            '--split=16'
                            ]
        # تحديد مسار aria2c إذا كان موجوداً في المجلد الجانبي
        if os.path.exists(ARIA2C_PATH):
            options['external_downloader'] = ARIA2C_PATH # استخدام Aria2 كأداة تحميل خارجية من مسارملف مجاور

            options['external_downloader_args'] = downloader_args
        else:
            options['external_downloader'] = 'aria2c'  # استخدام Aria2 كأداة تحميل خارجية

            options['external_downloader_args'] = downloader_args
    
    # إعدادات ما بعد المعالجة بناءً على نوع الملف
    if file_type == 'mp3':
        # تحويل إلى MP3 بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False

    elif file_type == 'mp4':
        # دمج الفيديو والصوت إلى صيغة MP4
        options['merge_output_format'] = 'mp4'
    
    elif file_type == 'mkv':
        # دمج الفيديو والصوت إلى صيغة MKV
        options['merge_output_format'] = 'mkv'

    ##
    elif file_type == 'avi':
        # دمج الفيديو والصوت إلى صيغة AVI
        # mkv هو الحاوية التي تدعم معظم الترميزات، بينما avi قد يواجه مشاكل توافق مع بعض الترميزات الحديثة، لذا نستخدم mkv كحاوية وسيتم تحويلها لاحقاً إلى avi
        options['merge_output_format'] = 'mkv'
        options['postprocessors'] = [{
                                        'key': 'FFmpegVideoConvertor',
                                        'preferedformat': 'avi',  # avi 
                                        }]
        # إعدادات ترميز الفيديو لملفات AVI (لتحسين التوافق)
        options['postprocessor_args'] = [
                                            '-c:v', 'libx264',   # كودك حديث
                                            '-crf', '18',        # جودة عالية (كلما قل الرقم زادت الجودة)
                                            '-preset', 'slow',   # ضغط أفضل
                                        ]

    ##
    elif file_type == 'flv':
        # دمج الفيديو والصوت إلى صيغة FLV
        options['merge_output_format'] = 'mkv'
        options['postprocessors'] = [{
                                        'key': 'FFmpegVideoConvertor',
                                        'preferedformat': 'flv', # flv
                                        }]
        # إعدادات ترميز الفيديو لملفات FLV (لتحسين التوافق)
        options['postprocessor_args'] = [
                                            '-c:v', 'libx264',   # كودك حديث
                                            '-crf', '18',        # جودة عالية (كلما قل الرقم زادت الجودة)
                                            '-preset', 'slow',   # ضغط أفضل
                                        ]
        
    elif file_type == 'webm':
        # دمج الفيديو والصوت إلى صيغة WEBM
        options['merge_output_format'] = 'webm'
    
    elif file_type == 'opus':
        # تحويل إلى OPUS بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False   

    elif file_type == 'aac':
        # تحويل إلى AAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'aac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'flac':
        # تحويل إلى FLAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'flac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'wav':
        # تحويل إلى WAV بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'alac':
        # تحويل إلى ALAC بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'alac',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False
    
    elif file_type == 'm4a':
        # دمج الفيديو والصوت إلى صيغة M4A
        options['merge_output_format'] = 'm4a'
    
    elif file_type == 'ogg':
        # تحويل إلى OGG بعد التحميل
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'vorbis',
            'preferredquality': '192',
        }]
        # حذف الملف الأصلي بعد التحويل
        #options['keepvideo'] = False   

    
    

    # ============================================================
    # إعدادات الترجمة
    # ============================================================


    if download_subtitles:
        requested_languages = parse_subtitle_languages(
            subtitle_languages
        )

        # نبقي هذه الخيارات كخطة بديلة إذا فشل الفحص الأولي.
        options['writesubtitles'] = True
        options['writeautomaticsub'] = True
        options['subtitleslangs'] = requested_languages
        options['subtitlesformat'] = 'srt/best'
        # YouTube يفرض قيدًا شديدًا على الترجمات الآلية المترجمة.
        # مهلة 60 ثانية هي الحل الموصى به لتفادي HTTP 429.
        if is_youtube_url(url):
            options['sleep_interval_subtitles'] = YOUTUBE_SUBTITLE_DELAY
        # فشل لغة واحدة لا يلغي باقي الترجمات أو الفيديو.
        options['ignoreerrors'] = True

        try:
            info_opts = {
                'quiet': True,
                'skip_download': True,
                # بعض مستخرجات yt-dlp لا تجلب هذه البيانات
                # ما لم تكن أعلام الترجمة مفعلة.
                'writesubtitles': True,
                'writeautomaticsub': True,
                'js_runtimes': get_js_runtime_options(),
            }

            if ffmpeg_path != "ffmpeg":
                info_opts['ffmpeg_location'] = ffmpeg_path

            if cookies_path != "\U0001F36A" and os.path.exists(cookies_path):
                info_opts['cookiefile'] = cookies_path

            with youtube_dl.YoutubeDL(info_opts) as ydl:
                subtitle_info = ydl.extract_info(url, download=False)

            manual_subs = subtitle_info.get('subtitles') or {}
            automatic_subs = subtitle_info.get('automatic_captions') or {}
            selected_languages, missing_languages = resolve_subtitle_languages(
                subtitle_languages,
                manual_subs,
                automatic_subs
            )

            if selected_languages:
                if missing_languages:
                    print(
                        "⚠️ لغات الترجمة غير المتاحة: "
                        + ", ".join(missing_languages)
                    )

                # yt-dlp يحمّل اليدوية والتلقائية في نفس العملية،
                # ويفضّل الترجمة اليدوية عند توفر النوعين للرمز نفسه.
                options['subtitleslangs'] = selected_languages
            else:
                print(
                    "⚠️ لا توجد ترجمة مطابقة للغات: "
                    + ", ".join(requested_languages)
                )

        except Exception as e:
            print(f"⚠️ تعذر تجهيز الترجمة: {e}")



    try:
        # بدء التحميل
        with youtube_dl.YoutubeDL(options) as ydl:
            #ydl.download([url])

            # extract_info تقوم بجلب البيانات وتحميل الملف في نفس الوقت
            # سجل وقت البدء حتى نتمكن من اكتشاف الملف الفعلي عند الانتهاء
            start_time = time.time()
            info = ydl.extract_info(url, download=True)

            if not info:
                raise youtube_dl.DownloadError(
                    "yt-dlp did not return media information"
                )

            # حاول استخراج اسم الملف المتوقع أولًا
            expected_path = ydl.prepare_filename(info)

            # إذا لم يوجد الملف في المسار المتوقع (قد غُيّر الامتداد أثناء المعالجة اللاحقة)،
            # فابحث عن أحدث ملف تم إنشاؤه/تعديله في مجلد التحميل
            downloaded_path = None
            if os.path.exists(expected_path):
                downloaded_path = expected_path
            else:
                # جمع الملفات العادية في مجلد التحميل
                try:
                    candidates = [os.path.join(final_download_dir, f) for f in os.listdir(final_download_dir)]
                    candidates = [p for p in candidates if os.path.isfile(p)]
                    # لا تعتبر ملفات الترجمة/الوصف/الأجزاء المؤقتة ملف الوسائط النهائي.
                    ignored_exts = {
                        '.part', '.srt', '.vtt', '.ass', '.lrc',
                        '.json', '.description', '.jpg', '.jpeg',
                        '.png', '.webp'
                    }

                    candidates = [
                        p for p in candidates
                        if os.path.splitext(p)[1].lower()
                        not in ignored_exts
                    ]
                    # احتفظ بالملفات الأحدث من وقت البدء - مع هامش صغير
                    recent = [
                        p for p in candidates
                        if os.path.getmtime(p) >= start_time - 2
                    ]
                    # فضّل الامتداد المتوقع لنوع الملف إن أمكن.
                    preferred_exts = {
                        'mp3': {'.mp3'},
                        'mp4': {'.mp4'},
                        'mkv': {'.mkv'},
                        'avi': {'.avi'},
                        'flv': {'.flv'},
                        'webm': {'.webm'},
                        'opus': {'.opus', '.webm'},
                        'aac': {'.aac', '.m4a'},
                        'flac': {'.flac'},
                        'wav': {'.wav'},
                        'alac': {'.m4a'},
                        'm4a': {'.m4a'},
                        'ogg': {'.ogg', '.oga'},
                    }

                    preferred = [
                            p for p in recent
                            if os.path.splitext(p)[1].lower()
                            in preferred_exts.get(file_type, set())
                        ]

                    if recent:
                        pool = preferred or recent
                        downloaded_path = max(pool, key=os.path.getmtime)
                except Exception:
                    downloaded_path = None

            # أخيراً، احتفظ بالمسار المتوقع إذا لم نعثر على أي ملف آخر
            if not downloaded_path:
                downloaded_path = expected_path

            print(f"File downloaded path: \n {downloaded_path}\n")

                        # ========================================================
            # قص الفيديو/الصوت + مزامنة الترجمة
            # يجب أن يتم القص قبل الضغط النهائي.
            # ========================================================
            if cut_enabled:
                if os.path.exists(downloaded_path):
                    try:
                        print(
                            f"✂️ Cutting: {cut_start} -> {cut_end}"
                        )

                        subtitle_files = []
                        if download_subtitles:
                            subtitle_files = find_subtitle_files(
                                downloaded_path,
                                final_download_dir
                            )

                        cut_file, actual_start, actual_end = cut_downloaded_media(
                            downloaded_path,
                            cut_start,
                            cut_end,
                            ffmpeg_path=ffmpeg_path,
                            file_type=file_type,
                            stop_event=stop_event
                        )

                        if subtitle_files:
                            print(
                                "📝 Adjusting subtitle timestamps..."
                            )
                            process_cut_subtitles(
                                subtitle_files,
                                actual_start,
                                actual_end
                            )

                        if (
                            os.path.exists(cut_file)
                            and cut_file != downloaded_path
                        ):
                            try:
                                os.remove(downloaded_path)
                            except Exception as e:
                                print(
                                    f"⚠️ تعذر حذف الملف الأصلي بعد القص: {e}"
                                )

                        downloaded_path = cut_file

                        print(
                            f"✅ Cut completed: {downloaded_path}"
                        )

                    except Exception as e:
                        # لا نحذف الملف الأصلي إذا فشل القص.
                        print(
                            f"❌ Cut failed: {e}"
                        )
                else:
                    raise Exception(
                        f"Cannot find downloaded file to cut: "
                        f"{downloaded_path}"
                    )

            # بعد التحميل، ضغط الفيديو إذا كان فيديو فعليًا ولم يطلب المستخدم نسخ الترميز
            if file_type not in ('mp3', 'opus', 'aac', 'flac', 'wav', 'alac', 'm4a', 'ogg') and not copy_codec:
                if os.path.exists(downloaded_path):                    
                    try:
                        downloaded_path = compress_downloaded_video(
                            downloaded_path,
                            file_type,
                            final_download_dir,
                            encoder=encoder,
                            crf=crf,
                            preset=preset,
                            copy_codec=copy_codec,
                            stop_event=stop_event,
                            progress_hook=progress_hook,
                        )
                    except Exception as e:
                        err_msg = str(e)
                        print(f"Compression failed: {err_msg}")
                        raise
                else:
                    # إذا لم نتمكن من تحديد الملف، اطرح تحذيراً بدلًا من محاولة ضغط ملف غير موجود
                    raise Exception(f"Cannot find downloaded file to compress: {downloaded_path}")
    except youtube_dl.DownloadError as e:
        # التعامل مع أخطاء التحميل
        raise Exception(f"Error downloading video: {str(e)}")
    # التعامل مع إيقاف التحميل من قبل المستخدم
    except Exception as e:
        # التعامل مع إيقاف التحميل من قبل المستخدم
        if "Download stopped by user" in str(e):
            raise Exception("Download stopped by user")
        # التعامل مع أي أخطاء غير متوقعة أخرى
        raise Exception(f"Unexpected error: {str(e)}")
