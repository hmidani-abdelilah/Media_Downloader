"""Reliable, reusable FFmpeg video-conversion helpers.
أدوات مساعدة موثوقة وقابلة لإعادة الاستخدام لتحويل الفيديو باستخدام FFmpeg.
"""

from __future__ import annotations # التحسين التلميحات النوعية في الإصدارات القديمة من بايثون

import os # استخدام مكتبة os للتعامل مع نظام التشغيل
import platform # استخدام مكتبة platform للحصول على معلومات حول النظام
import re # استخدام مكتبة re للتعامل مع التعبيرات النمطية
import shutil # استخدام مكتبة shutil للتعامل مع الملفات والمجلدات
import subprocess # استخدام مكتبة subprocess لتشغيل أوامر النظام
import time # استخدام مكتبة time للتعامل مع الوقت
import uuid # استخدام مكتبة uuid لإنشاء معرفات فريدة
from functools import lru_cache # استخدام lru_cache لتخزين نتائج الدوال وتحسين الأداء
from pathlib import Path # استخدام مكتبة pathlib للتعامل مع المسارات
import threading # استخدام مكتبة threading للتعامل مع الخيوط
from typing import Sequence # استخدام typing لتحديد أنواع البيانات المتسلسلة

from path_ffmpeg import ffmpeg_find_path # استيراد دالة ffmpeg_find_path من مكتبة path_ffmpeg للعثور على مسار FFmpeg


PROBE_TIMEOUT_SECONDS = 30 # الحد الأقصى للوقت المسموح به لاستدعاء FFmpeg للتحقق من الترميزات المدعومة
CPU_ENCODERS = ("libx264", "libx265") # الترميزات المدعومة على وحدة المعالجة المركزية (CPU) لتحويل الفيديو
HARDWARE_ENCODERS = (
    "h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv", "h264_amf",
    "hevc_amf", "h264_vaapi", "hevc_vaapi", "h264_videotoolbox",
    "hevc_videotoolbox",
) # الترميزات المدعومة على وحدات معالجة الرسومات (GPU) لتحويل الفيديو
WEBM_ENCODERS = ("libvpx", "libvpx-vp9", "libaom-av1") # الترميزات المدعومة لتنسيق WebM لتحويل الفيديو
ENCODER_PRIORITY = (
    "hevc_nvenc", "h264_nvenc", "hevc_qsv", "h264_qsv", "hevc_amf",
    "h264_amf", "hevc_videotoolbox", "h264_videotoolbox", "hevc_vaapi",
    "h264_vaapi", "libx265", "libx264",
) # ترتيب الأولوية للترميزات عند اختيار أفضل ترميز متاح لتحويل الفيديو
VALID_PRESETS = frozenset(
    {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
) # مجموعة من الإعدادات المسبقة الصالحة للتحويل، والتي تحدد سرعة وجودة التحويل
ENCODER_LINE = re.compile(r"^\s*V\S*\s+(\S+)", re.MULTILINE) # تعبير نمطي لاستخراج أسماء الترميزات من إخراج FFmpeg، حيث يبحث عن الأسطر التي تحتوي على معلومات الترميز ويستخرج اسم الترميز
NVENC_PRESETS = {
    "ultrafast": "p1", "superfast": "p2", "veryfast": "p3", "faster": "p4",
    "fast": "p5", "medium": "p5", "slow": "p6", "slower": "p7", "veryslow": "p7",
} # خريطة الإعدادات المسبقة الخاصة بـ NVENC، حيث يتم تحويل إعدادات السرعة إلى رموز NVENC المقابلة
AMF_PRESETS = {
    "ultrafast": "speed", "superfast": "speed", "veryfast": "speed", "faster": "balanced",
    "fast": "balanced", "medium": "balanced", "slow": "quality", "slower": "quality", "veryslow": "quality",
} # خريطة الإعدادات المسبقة الخاصة بـ AMF، حيث يتم تحويل إعدادات السرعة إلى رموز AMF المقابلة

# --------------------- استثناءات مخصصة ---------------------
class ConversionError(RuntimeError):
    """Raised when FFmpeg cannot complete a conversion."""

# --------------------- دوال مساعدة ---------------------

# دالة للحصول على مسار أو اسم أمر FFmpeg صالح
def get_ffmpeg_executable() -> str:
    """Return a valid FFmpeg executable path or command name."""
    configured_path = ffmpeg_find_path()
    if configured_path == "ffmpeg":
        return configured_path
    if configured_path and Path(configured_path).is_file():
        return configured_path

    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    raise ConversionError("FFmpeg not found. Install it or configure the correct path.")


@lru_cache(maxsize=4) # تخزين نتائج الدالة في ذاكرة التخزين المؤقت لتحسين الأداء عند استدعاء الدالة مرات متعددة بنفس المعلمات
# دالة للحصول على الترميزات المدعومة من FFmpeg  
def get_video_encoders(ffmpeg_executable: str | None = None) -> frozenset[str]:
    """Return cached, exact video encoder names advertised by FFmpeg."""
    executable = ffmpeg_executable or get_ffmpeg_executable()
    try:
        result = subprocess.run(
            [executable, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            check=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ConversionError(f"Failed to read FFmpeg encoders: {error}") from error
    return frozenset(ENCODER_LINE.findall(result.stdout))

# دالة للتحقق مما إذا كان الترميز المدخل مدعوم من قبل FFmpeg
def is_encoder_supported(encoder: str) -> bool:
    """Return whether *encoder* is an exact FFmpeg video-encoder name."""
    try:
        return encoder in get_video_encoders()
    except ConversionError:
        return False

# دالة للكشف عن نوع وحدة معالجة الرسومات (GPU) المتاحة
def detect_gpu() -> str:
    """Best-effort GPU detection; conversion still verifies FFmpeg support."""
    if platform.system() == "Darwin":
        return "Apple"
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS
        )
        if result.returncode == 0 and result.stdout.strip():
            return "NVIDIA"
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        encoders = get_video_encoders()
    except ConversionError:
        return "CPU"
    if {"h264_qsv", "hevc_qsv"}.intersection(encoders):
        return "Intel"
    if {"h264_amf", "hevc_amf"}.intersection(encoders):
        return "AMD"
    return "CPU"

# دالة لجلب الترميزات المدعومة من قبل وحدة المعالجة المركزية (CPU) ووحدات معالجة الرسومات (GPU) بالترتيب المفضل
def get_gpu_encoders() -> list[str]:
    """Return supported CPU and hardware encoder choices in priority order."""
    try:
        available = get_video_encoders()
    except ConversionError:
        return list(CPU_ENCODERS)
    known = set(CPU_ENCODERS).union(HARDWARE_ENCODERS)
    return [encoder for encoder in ENCODER_PRIORITY if encoder in available and encoder in known]

# دالة لاختيار أفضل ترميز متاح من FFmpeg، مع تفضيل الترميزات المدعومة من قبل وحدة معالجة الرسومات (GPU)
def choose_best_encoder() -> str:
    """Choose the best FFmpeg-advertised encoder, preferring hardware."""
    return next(iter(get_gpu_encoders()), "libx264")

# دالة للتحقق من صحة مسارات الملفات المدخلة والمخرجات
def _validate_paths(
    input_path: str | os.PathLike[str], output_path: str | os.PathLike[str]
) -> tuple[Path, Path]:
    input_file = Path(input_path).expanduser()
    output_file = Path(output_path).expanduser()
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file does not exist or is not a file: {input_file}")
    if not output_file.suffix:
        raise ValueError("Output file must have an extension like .mp4 or .mkv.")
    if input_file.resolve() == output_file.resolve():
        raise ValueError("Input and output files must be different.")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    return input_file, output_file

# دالة للتحقق من صحة إعدادات CRF والإعداد المسبق
def _validate_settings(crf: int, preset: str) -> None:
    if isinstance(crf, bool) or not isinstance(crf, int) or not 0 <= crf <= 51:
        raise ValueError("CRF value must be an integer between 0 and 51.")
    if preset not in VALID_PRESETS:
        raise ValueError(f"Invalid preset: {preset}")

# دالة لإنشاء مسار مؤقت لملف الإخراج أثناء عملية التحويل
def _temporary_output_path(output_file: Path) -> Path:
    return output_file.with_name(f".{output_file.stem}.{uuid.uuid4().hex}.tmp{output_file.suffix}")

# دالة للحصول على الوسائط المطلوبة لترميز الفيديو باستخدام VAAPI
def _encoder_input_arguments(encoder: str) -> list[str]:
    if not encoder.endswith("_vaapi"):
        return []
    device = os.environ.get("VAAPI_DEVICE", "/dev/dri/renderD128")
    if platform.system() != "Linux" or not Path(device).exists():
        raise ConversionError("VAAPI encoding requires a valid Linux device; set VAAPI_DEVICE if needed.")
    return ["-vaapi_device", device]

# دالة للحصول على الوسائط المطلوبة لضبط جودة الترميز بناءً على الترميز المحدد
def _encoder_quality_arguments(encoder: str, crf: int, preset: str) -> list[str]:
    if encoder in CPU_ENCODERS:
        return ["-crf", str(crf), "-preset", preset]
    if encoder in WEBM_ENCODERS:
        # For libvpx/libvpx-vp9/libaom-av1 use constant-quality mode with unlimited bitrate
        # Many of these encoders accept -crf and -b:v 0 to indicate CQ mode.
        return ["-crf", str(crf), "-b:v", "0", "-preset", preset]
    if encoder.endswith("_nvenc"):
        return ["-rc:v", "vbr", "-cq:v", str(crf), "-b:v", "0", "-preset", NVENC_PRESETS[preset]]
    if encoder.endswith("_qsv"):
        return ["-global_quality", str(crf)]
    if encoder.endswith("_amf"):
        return ["-rc", "cqp", "-qp_i", str(crf), "-qp_p", str(crf), "-quality", AMF_PRESETS[preset]]
    if encoder.endswith("_videotoolbox"):
        return ["-q:v", str(round((51 - crf) * 100 / 51))]
    if encoder.endswith("_vaapi"):
        return ["-vf", "format=nv12,hwupload", "-qp", str(crf)]
    raise ValueError(f"Video encoder not supported: {encoder}")

# دالة لبناء أمر FFmpeg لتحويل الفيديو بناءً على المعلمات المحددة
def _build_ffmpeg_command(
    executable: str,
    input_file: Path,
    output_file: Path,
    encoder: str | None,
    crf: int,
    preset: str,
    copy_codec: bool,
) -> list[str]:
    command = [executable, "-hide_banner", "-nostdin", "-y"]
    if not copy_codec:
        if encoder is None:
            raise ValueError("Encoder must be specified when not copying codecs.")
        command.extend(_encoder_input_arguments(encoder))
    command.extend(["-i", str(input_file)])
    if copy_codec:
        return [*command, "-c", "copy", str(output_file)]
    return [
        *command,
        "-c:v", encoder,
        *_encoder_quality_arguments(encoder, crf, preset),
        "-c:a", "copy",
        str(output_file),
    ]

# دالة لتشغيل أمر FFmpeg والتحقق من نجاح العملية، مع دعم الإلغاء والمهلة الزمنية
def _run_ffmpeg(command: Sequence[str], timeout: float | None, stop_event: threading.Event | None = None) -> None:
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as error:
        raise ConversionError("Failed to run FFmpeg: executable not found.") from error

    start_time = time.monotonic()
    while True:
        if stop_event is not None and stop_event.is_set():
            process.kill()
            stdout, stderr = process.communicate()
            raise ConversionError("Compression cancelled by user.")

        retcode = process.poll()
        if retcode is not None:
            stdout, stderr = process.communicate()
            if retcode != 0:
                details = (stderr or stdout or "خطأ غير معروف من FFmpeg").strip()
                raise ConversionError(details[-4000:])
            return

        if timeout is not None and time.monotonic() - start_time > timeout:
            process.kill()
            stdout, stderr = process.communicate()
            raise ConversionError("FFmpeg timeout before conversion completed.")

        time.sleep(0.1)

# دالة للحصول على ترميز بديل على وحدة المعالجة المركزية (CPU) في حالة فشل الترميز المحدد
def _cpu_fallback_encoder() -> str:
    available = get_video_encoders()
    for encoder in CPU_ENCODERS:
        if encoder in available:
            return encoder
    raise ConversionError("FFmpeg does not provide a CPU fallback encoder like libx264.")

# دالة لضغط الفيديو باستخدام FFmpeg مع دعم الترميزات المختلفة، والتحقق من صحة الإعدادات، وإدارة الملفات المؤقتة، والتعامل مع الأخطاء
def compress_video(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    encoder: str | None = None,
    crf: int = 23,
    preset: str = "medium",
    copy_codec: bool = False,
    timeout: float | None = None,
    stop_event: threading.Event | None = None,
) -> Path:
    """Convert a video atomically and return the final output path.

    If a selected hardware encoder cannot use its device or driver, the
    conversion is retried once with an available CPU encoder. Existing output
    is preserved unless an attempt succeeds completely.
    
    حوّل الفيديو بشكل كامل وأعد مسار الإخراج النهائي.

    إذا تعذّر على مُشفّر الأجهزة المُختار استخدام جهازه أو برنامج تشغيله，

    تُعاد محاولة التحويل مرة واحدة باستخدام مُشفّر وحدة المعالجة المركزية المُتاح.

    يُحفظ الإخراج الحالي ما لم تنجح المحاولة تمامًا.
    """
    _validate_settings(crf, preset)
    input_file, output_file = _validate_paths(input_path, output_path)
    executable = get_ffmpeg_executable()
    selected_encoder = None if copy_codec else (encoder or choose_best_encoder())
    if selected_encoder and not is_encoder_supported(selected_encoder):
        raise ValueError(f"Video encoder not available in FFmpeg: {selected_encoder}")

    temporary_output = _temporary_output_path(output_file)
    try:
        try:
            command = _build_ffmpeg_command(
                executable, input_file, temporary_output, selected_encoder, crf, preset, copy_codec
            )
            _run_ffmpeg(command, timeout, stop_event=stop_event)
        except ConversionError:
            if copy_codec or selected_encoder not in HARDWARE_ENCODERS:
                raise
            fallback_command = _build_ffmpeg_command(
                executable, input_file, temporary_output, _cpu_fallback_encoder(), crf, preset, False
            )
            _run_ffmpeg(fallback_command, timeout, stop_event=stop_event)
        os.replace(temporary_output, output_file)
    finally:
        temporary_output.unlink(missing_ok=True)
    return output_file
