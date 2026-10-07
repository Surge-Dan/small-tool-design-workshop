"""Review board provenance and portability, not prototype design quality."""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "design_review.py"
MODULE = importlib.util.spec_from_file_location("design_review", SCRIPT)
review = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(review)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aU1QAAAAASUVORK5CYII=")


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "截图.png").write_bytes(PNG)
        self.manifest = self.root / "review.json"
        self.output = self.root / "review.html"
        self.prototype = self.root / "prototype.html"
        self.prototype.write_text("<!doctype html><p>当前版本</p>", encoding="utf-8")
        self.item = {"role": "current", "label": '<script>alert("x")</script>', "path": "截图.png",
                     "state": "结果", "viewport_width": 390}

    def build(self):
        self.manifest.write_text(json.dumps({"items": [self.item]}, ensure_ascii=False), encoding="utf-8")
        return review.build(self.manifest, self.output, self.prototype)

    def test_portable_images_escaped_labels_and_unverified_version(self):
        self.build()
        text = self.output.read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64,", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn('<script>alert("x")</script>', text)
        self.assertNotIn(str(self.root), text)
        self.assertIn("版本未核验", text)
        (self.root / "截图.png").unlink()
        self.assertIn(base64.b64encode(PNG).decode(), text)

    def test_current_hash_cannot_be_reused_after_html_changes(self):
        self.item["prototype_sha256"] = hashlib.sha256(self.prototype.read_bytes()).hexdigest()
        self.prototype.write_text("新版", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "旧HTML"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_reference_is_not_current_evidence(self):
        self.item.update(role="reference", prototype_sha256="0" * 64)
        self.item.pop("viewport_width")
        self.build()
        text = self.output.read_text(encoding="utf-8")
        self.assertIn("参考素材，非原型证据", text)
        self.assertIn("视口未知", text)
        self.assertNotIn("HTML哈希一致", text)

    def test_reject_remote_or_active_image_content(self):
        for path in ("https://example.org/ref.png", "data:image/png;base64,x", "active.svg"):
            with self.subTest(path=path):
                self.item["path"] = path
                (self.root / "active.svg").write_text('<svg onload="alert(1)"/>', encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse(self.output.exists())

    def test_no_overwrite_and_valid_binding(self):
        self.item["prototype_sha256"] = hashlib.sha256(self.prototype.read_bytes()).hexdigest()
        self.build()
        initial = self.output.read_bytes()
        self.assertIn("HTML哈希一致", initial.decode())
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(initial, self.output.read_bytes())


if __name__ == "__main__":
    unittest.main()
