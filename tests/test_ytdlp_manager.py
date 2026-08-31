import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import ytdlp_manager
from ytdlp_manager import YtDlpManager, default_config_dir


MINIMAL_API = """
class YoutubeDL:
    pass

class DownloadError(Exception):
    pass
"""


def make_package(parent: Path, version: str, import_body: str = MINIMAL_API) -> Path:
    package = parent / "yt_dlp"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(import_body, encoding="utf-8")
    (package / "version.py").write_text(
        f"__version__ = {version!r}\n", encoding="utf-8"
    )
    (package / "extractor.py").write_text("VALUE = 1\n", encoding="utf-8")
    return package


def make_wheel(version: str, import_body: str = MINIMAL_API) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("yt_dlp/__init__.py", import_body)
        archive.writestr("yt_dlp/version.py", f"__version__ = {version!r}\n")
        archive.writestr("yt_dlp/extractor.py", "VALUE = 2\n")
        archive.writestr(
            f"yt_dlp-{version}.dist-info/METADATA",
            f"Name: yt-dlp\nVersion: {version}\n",
        )
    return output.getvalue()


class FakeResponse(io.BytesIO):
    def __init__(self, data: bytes):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}


class FakeOpener:
    def __init__(self, metadata: dict, wheel: bytes):
        self.metadata = json.dumps(metadata).encode("utf-8")
        self.wheel = wheel
        self.calls = []

    def __call__(self, request, timeout):
        url = request.full_url
        self.calls.append((url, timeout))
        if url.endswith("/json"):
            return FakeResponse(self.metadata)
        return FakeResponse(self.wheel)


def release_metadata(
    version: str,
    wheel: bytes,
    digest: str = None,
    requires_python: str = None,
) -> dict:
    return {
        "info": {"version": version, "requires_python": requires_python},
        "urls": [
            {
                "packagetype": "bdist_wheel",
                "filename": f"yt_dlp-{version}-py3-none-any.whl",
                "url": (
                    "https://files.pythonhosted.org/packages/test/"
                    f"yt_dlp-{version}-py3-none-any.whl"
                ),
                "digests": {
                    "sha256": digest or hashlib.sha256(wheel).hexdigest()
                },
            }
        ],
    }


class YtDlpManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.seed = make_package(self.root / "readonly-seed", "2026.08.01")
        self.config = self.root / "config"

    def tearDown(self):
        self.temporary.cleanup()

    def manager(self, **kwargs):
        return YtDlpManager(
            config_dir=self.config,
            seed_package=self.seed,
            clock=lambda: 1_000_000,
            **kwargs,
        )

    def test_first_run_copies_seed_outside_appimage(self):
        original_digest = hashlib.sha256(
            (self.seed / "version.py").read_bytes()
        ).hexdigest()
        os.chmod(self.seed, 0o555)
        os.chmod(self.seed / "version.py", 0o444)

        result = self.manager().ensure_ready(check_updates=False)

        self.assertEqual(result.status, "seeded")
        self.assertEqual(result.current_version, "2026.08.01")
        active = self.config / "yt-dlp/versions/2026.08.01/yt_dlp"
        self.assertTrue((active / "__init__.py").is_file())
        self.assertEqual(
            hashlib.sha256((self.seed / "version.py").read_bytes()).hexdigest(),
            original_digest,
        )

    def test_successful_update_is_versioned_and_preserves_vendor_files(self):
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        active_root = manager.active_root()
        (active_root / "optional_dependency.py").write_text(
            "PRESENT = True\n", encoding="utf-8"
        )
        wheel = make_wheel("2026.08.30")
        opener = FakeOpener(release_metadata("2026.08.30", wheel), wheel)
        manager._urlopen = opener

        result = manager.update()

        self.assertEqual(result.status, "updated")
        self.assertEqual(result.previous_version, "2026.08.01")
        self.assertEqual(result.current_version, "2026.08.30")
        new_root = self.config / "yt-dlp/versions/2026.08.30"
        self.assertTrue((new_root / "optional_dependency.py").is_file())
        self.assertTrue((new_root / "yt_dlp/version.py").is_file())
        self.assertTrue((self.config / "yt-dlp/versions/2026.08.01").is_dir())

    def test_network_failure_keeps_last_known_good_version(self):
        manager = self.manager()
        manager.ensure_ready(check_updates=False)

        def offline(*args, **kwargs):
            raise TimeoutError("offline")

        manager._urlopen = offline
        result = manager.update()

        self.assertEqual(result.status, "offline")
        self.assertEqual(result.current_version, "2026.08.01")
        self.assertEqual(manager.active_root().name, "2026.08.01")

    def test_bad_checksum_never_replaces_working_version(self):
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        wheel = make_wheel("2026.08.30")
        bad_digest = "0" * 64
        manager._urlopen = FakeOpener(
            release_metadata("2026.08.30", wheel, bad_digest), wheel
        )

        result = manager.update()

        self.assertEqual(result.status, "offline")
        self.assertEqual(manager.active_root().name, "2026.08.01")
        self.assertFalse(
            (self.config / "yt-dlp/versions/2026.08.30").exists()
        )

    def test_corrupt_active_state_recovers_seed(self):
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        (manager.active_root() / "yt_dlp/version.py").write_text(
            "this is not python !", encoding="utf-8"
        )

        # The bundled seed remains the recovery source.
        result = manager.ensure_ready(check_updates=False)

        self.assertEqual(result.status, "seeded")
        self.assertEqual(result.current_version, "2026.08.01")
        self.assertIn(
            "__version__",
            (manager.active_root() / "yt_dlp/version.py").read_text(
                encoding="utf-8"
            ),
        )

    def test_update_check_is_throttled(self):
        wheel = make_wheel("2026.08.30")
        opener = FakeOpener(release_metadata("2026.08.30", wheel), wheel)
        manager = self.manager(urlopen=opener)
        first = manager.ensure_ready(check_updates=True)
        second = manager.ensure_ready(check_updates=True)

        self.assertEqual(first.status, "updated")
        self.assertEqual(second.status, "ready")
        self.assertEqual(len(opener.calls), 2)

    def test_pypi_normalized_version_matches_version_module(self):
        wheel = make_wheel("2026.08.30")
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        manager._urlopen = FakeOpener(
            release_metadata("2026.8.30", wheel), wheel
        )

        result = manager.update()

        self.assertEqual(result.status, "updated")
        self.assertEqual(manager.active_root().name, "2026.8.30")

    def test_incompatible_python_release_is_rejected(self):
        wheel = make_wheel("2026.08.30")
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        manager._urlopen = FakeOpener(
            release_metadata(
                "2026.08.30", wheel, requires_python=">=99.0"
            ),
            wheel,
        )

        result = manager.update()

        self.assertEqual(result.status, "offline")
        self.assertEqual(manager.active_root().name, "2026.08.01")

    def test_default_config_honors_xdg(self):
        path = default_config_dir(
            {"XDG_CONFIG_HOME": str(self.root / "xdg-config")}
        )
        self.assertEqual(path, self.root / "xdg-config/media-downloader")

    def test_unsafe_wheel_path_is_rejected(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("../outside", "bad")
            archive.writestr("yt_dlp/__init__.py", "")
            archive.writestr(
                "yt_dlp/version.py", "__version__ = '2026.08.30'\n"
            )
        wheel = output.getvalue()
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        manager._urlopen = FakeOpener(
            release_metadata("2026.08.30", wheel), wheel
        )

        result = manager.update()

        self.assertEqual(result.status, "offline")
        self.assertFalse((self.root / "outside").exists())
        self.assertEqual(manager.active_root().name, "2026.08.01")

    def test_pruning_keeps_seed_active_and_rollback(self):
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        for version in ("2026.08.02", "2026.08.03", "2026.08.04"):
            make_package(manager.versions_dir / version, version)
        state = manager._read_state()
        state["active_version"] = "2026.08.04"
        state["previous_version"] = "2026.08.03"
        manager._write_state(state)

        manager.prune_versions(keep_recent=2)

        self.assertTrue((manager.versions_dir / "2026.08.01").exists())
        self.assertFalse((manager.versions_dir / "2026.08.02").exists())
        self.assertTrue((manager.versions_dir / "2026.08.03").exists())
        self.assertTrue((manager.versions_dir / "2026.08.04").exists())

    def test_missing_required_api_rolls_back_and_is_not_reactivated(self):
        (self.seed / "__init__.py").write_text(
            MINIMAL_API + "\nSOURCE = 'seed'\n", encoding="utf-8"
        )
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        broken_wheel = make_wheel(
            "2026.08.30", "SOURCE = 'incomplete candidate'\n"
        )
        manager._urlopen = FakeOpener(
            release_metadata("2026.08.30", broken_wheel), broken_wheel
        )
        self.assertEqual(manager.update().status, "updated")

        old_manager = ytdlp_manager._default_manager
        old_module = ytdlp_manager._loaded_module
        old_result = ytdlp_manager._startup_result
        old_finder = ytdlp_manager._external_finder
        old_roots = set(ytdlp_manager._external_search_roots)
        original_path = list(sys.path)
        original_meta_path = list(sys.meta_path)
        try:
            ytdlp_manager._default_manager = manager
            ytdlp_manager._loaded_module = None
            ytdlp_manager._startup_result = None
            with mock.patch.dict(
                os.environ,
                {
                    "MEDIA_DOWNLOADER_FORCE_EXTERNAL_YTDLP": "1",
                    "MEDIA_DOWNLOADER_DISABLE_YTDLP_AUTO_UPDATE": "1",
                },
            ):
                module = ytdlp_manager.load_ytdlp()

            self.assertEqual(module.SOURCE, "seed")
            self.assertEqual(manager.active_root().name, "2026.08.01")
            retry = manager.update()
            self.assertEqual(retry.status, "rollback")
            self.assertEqual(manager.active_root().name, "2026.08.01")
        finally:
            ytdlp_manager._purge_ytdlp_modules()
            sys.path[:] = original_path
            ytdlp_manager._default_manager = old_manager
            ytdlp_manager._loaded_module = old_module
            ytdlp_manager._startup_result = old_result
            ytdlp_manager._external_finder = old_finder
            ytdlp_manager._external_search_roots = old_roots
            sys.meta_path[:] = original_meta_path

    def test_multiple_broken_versions_roll_back_to_seed(self):
        (self.seed / "__init__.py").write_text(
            MINIMAL_API + "\nSOURCE = 'seed-a'\n", encoding="utf-8"
        )
        manager = self.manager()
        manager.ensure_ready(check_updates=False)
        for version in ("2026.08.20", "2026.08.30"):
            wheel = make_wheel(version, f"SOURCE = {version!r}\n")
            manager._urlopen = FakeOpener(
                release_metadata(version, wheel), wheel
            )
            self.assertEqual(manager.update().status, "updated")

        saved = (
            ytdlp_manager._default_manager,
            ytdlp_manager._loaded_module,
            ytdlp_manager._startup_result,
            ytdlp_manager._external_finder,
            set(ytdlp_manager._external_search_roots),
            list(sys.path),
            list(sys.meta_path),
        )
        try:
            ytdlp_manager._default_manager = manager
            ytdlp_manager._loaded_module = None
            ytdlp_manager._startup_result = None
            with mock.patch.dict(
                os.environ,
                {
                    "MEDIA_DOWNLOADER_FORCE_EXTERNAL_YTDLP": "1",
                    "MEDIA_DOWNLOADER_DISABLE_YTDLP_AUTO_UPDATE": "1",
                },
            ):
                module = ytdlp_manager.load_ytdlp()

            self.assertEqual(module.SOURCE, "seed-a")
            self.assertEqual(manager.active_root().name, "2026.08.01")
            state = json.loads(manager.state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(state["broken_versions"]), 2)
        finally:
            ytdlp_manager._purge_ytdlp_modules()
            (
                ytdlp_manager._default_manager,
                ytdlp_manager._loaded_module,
                ytdlp_manager._startup_result,
                ytdlp_manager._external_finder,
                old_roots,
                old_path,
                old_meta_path,
            ) = saved
            ytdlp_manager._external_search_roots = old_roots
            sys.path[:] = old_path
            sys.meta_path[:] = old_meta_path


if __name__ == "__main__":
    unittest.main()
