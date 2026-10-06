"""Recoverable byte versions, path boundaries and explicit evidence marking."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prototype_state.py"
MODULE = importlib.util.spec_from_file_location("prototype_state", SCRIPT)
state = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(state)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.html = self.root / "原型.html"
        self.html.write_text("<!doctype html><p>原版</p>", encoding="utf-8")
        self.spec = self.root / "design-spec.json"
        self.record = {"evidence": [{"id": "E1", "path": "截图/观察.txt"}, {"id": "E2"}]}
        (self.root / "截图").mkdir()
        (self.root / "截图/观察.txt").write_text("原观察", encoding="utf-8")
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.spec.write_text(json.dumps(self.record, ensure_ascii=False), encoding="utf-8")

    def test_restore_preserves_html_spec_and_original_attachment(self):
        html, spec = self.html.read_bytes(), self.spec.read_bytes()
        snapshot = state.capture(self.html, self.root / "snapshot", self.spec)
        self.html.write_text("<p>新版</p>", encoding="utf-8")
        (self.root / "截图/观察.txt").write_text("新观察", encoding="utf-8")
        restored = state.restore(snapshot, self.root / "restored")
        self.assertEqual((restored / self.html.name).read_bytes(), html)
        self.assertEqual((restored / self.spec.name).read_bytes(), spec)
        self.assertEqual((restored / "截图/观察.txt").read_text(encoding="utf-8"), "原观察")
        self.assertEqual(self.html.read_text(encoding="utf-8"), "<p>新版</p>")

    def test_html_only_snapshot_restores_without_spec(self):
        snap = state.capture(self.html, self.root / "snapshot")
        out = state.restore(snap, self.root / "restored")
        self.assertEqual([p.name for p in out.iterdir()], [self.html.name])

    def test_snapshot_and_restore_refuse_existing_directories(self):
        snap = state.capture(self.html, self.root / "snapshot")
        with self.assertRaises(ValueError):
            state.capture(self.html, snap)
        existing = self.root / "existing"
        existing.mkdir()
        with self.assertRaises(ValueError):
            state.restore(snap, existing)

    def test_corrupt_snapshot_has_no_restore_output(self):
        snap = state.capture(self.html, self.root / "snapshot")
        (snap / "prototype.html").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "损坏"):
            state.restore(snap, self.root / "restored")
        self.assertFalse((self.root / "restored").exists())

    def test_outside_attachment_rejects_before_snapshot_creation(self):
        self.record["evidence"][0]["path"] = "../outside.txt"
        self.save()
        with self.assertRaises(ValueError):
            state.capture(self.html, self.root / "snapshot", self.spec)
        self.assertFalse((self.root / "snapshot").exists())

    def test_manifest_cannot_restore_outside_target(self):
        snap = state.capture(self.html, self.root / "snapshot")
        manifest = json.loads((snap / "manifest.json").read_text(encoding="utf-8"))
        manifest["files"][0]["target"] = "../outside.html"
        (snap / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            state.restore(snap, self.root / "restored")
        self.assertFalse((self.root / "outside.html").exists())

    def test_bind_without_ids_leaves_old_evidence_unbound(self):
        current = state.bind(self.spec, self.html)
        record = json.loads(self.spec.read_text(encoding="utf-8"))
        self.assertEqual(record["prototype_sha256"], current)
        self.assertTrue(all("prototype_sha256" not in e for e in record["evidence"]))

    def test_bind_marks_only_explicit_evidence_and_attachment(self):
        current = state.bind(self.spec, self.html, ["E1"])
        record = json.loads(self.spec.read_text(encoding="utf-8"))
        self.assertEqual(record["evidence"][0]["prototype_sha256"], current)
        self.assertIn("attachment_sha256", record["evidence"][0])
        self.assertNotIn("prototype_sha256", record["evidence"][1])

    def test_missing_evidence_id_does_not_mutate_record(self):
        before = self.spec.read_bytes()
        with self.assertRaises(ValueError):
            state.bind(self.spec, self.html, ["missing"])
        self.assertEqual(self.spec.read_bytes(), before)

    def test_missing_attachment_does_not_mutate_record(self):
        (self.root / "截图/观察.txt").unlink()
        before = self.spec.read_bytes()
        with self.assertRaises(OSError):
            state.bind(self.spec, self.html, ["E1"])
        self.assertEqual(self.spec.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
