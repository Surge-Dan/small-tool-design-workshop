"""Exporter invariants; these are not prototype/browser tests."""

import base64
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_handoff.py"
MODULE = importlib.util.spec_from_file_location("build_handoff", SCRIPT)
exporter = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(exporter)


def fixture():
    return {
        "schema_version": 1, "title": "晚餐参考｜测试", "revision": "test-1",
        "brief": {"status": "delegated", "confirmation_evidence": "测试用例中的明确委托",
                  "target_user": "测试用户", "scenario": "安排晚餐", "goal": "预算内选择",
                  "non_goals": ["登录"], "offline": True, "blocking_questions": []},
        "pages": [{"id": "input", "name": "输入", "layout": "预算、人数、生成按钮",
                   "states": [{"id": "ready", "description": "待输入"},
                              {"id": "result", "description": "显示结果"}]}],
        "requirements": [{"id": "R1", "description": "预算计算", "page_ids": ["input"],
                          "acceptance": "合计不超预算", "implementation": "implemented",
                          "verification": "static", "evidence_ids": ["E1"]}],
        "interactions": [{"id": "I1", "from_state": "ready", "to_state": "result",
                          "trigger": "提交", "guard": "输入有效", "feedback": "显示结果",
                          "preserves": "预算、人数"}],
        "logic": [{"id": "L1", "description": "除法", "inputs": ["总价", "人数"],
                   "rule": "总价除人数", "example": "40元／2人＝20元", "simulation": False}],
        "visual": {"direction": "价签", "tokens": {"--ink": "#384e40"}, "motion": "",
                   "assets": []},
        "evidence": [{"id": "E1", "kind": "static", "description": "测试中的静态记录",
                      "state_ids": ["result"]}],
        "assumptions": ["基础调味料自备"], "limitations": ["无真机验证"], "changes": []
    }


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.spec_path = self.root / "design-spec.json"
        self.html = self.root / "晚餐.html"
        self.html.write_text("<!doctype html><title>晚餐</title><p>原型参考</p>", encoding="utf-8")
        self.spec = fixture()

    def tearDown(self):
        self.temp.cleanup()

    def build(self, name="交接包"):
        self.spec_path.write_text(json.dumps(self.spec, ensure_ascii=False), encoding="utf-8")
        return exporter.build(self.spec_path, self.html, self.root / name)

    def test_unicode_bundle_and_zip_content(self):
        directory, archive, notices = self.build()
        self.assertEqual((directory / "prototype.html").read_bytes(), self.html.read_bytes())
        exported = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(exported, self.spec)
        handoff = (directory / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("R1", handoff)
        self.assertIn("基础调味料自备", handoff)
        self.assertTrue(any("断网" in s for s in notices))
        self.assertTrue(any("截图" in s for s in notices))
        with zipfile.ZipFile(archive) as package:
            self.assertIsNone(package.testzip())
            for name in package.namelist():
                relative = Path(name)
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                source = directory / Path(*relative.parts[1:])
                self.assertEqual(package.read(name), source.read_bytes())

    def test_evidence_files_are_copied_and_paths_rewritten(self):
        (self.root / "检查.txt").write_text("操作记录", encoding="utf-8")
        self.spec["evidence"][0]["path"] = "检查.txt"
        directory, _, _ = self.build()
        exported = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(exported["evidence"][0]["path"], "evidence/E1.txt")
        self.assertEqual((directory / "evidence/E1.txt").read_text(encoding="utf-8"), "操作记录")

    def test_draft_and_blocking_questions_reject_without_output(self):
        for change in ({"status": "draft"}, {"blocking_questions": ["规则未定"]}):
            with self.subTest(change=change):
                self.spec = fixture()
                self.spec["brief"].update(change)
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse((self.root / "交接包").exists())
                self.assertFalse((self.root / "交接包.zip").exists())

    def test_broken_references_duplicate_ids_and_verification_reject(self):
        variants = []
        broken = fixture()
        broken["requirements"][0]["page_ids"] = ["missing"]
        variants.append(broken)
        duplicate = fixture()
        duplicate["pages"][0]["states"].append(copy.deepcopy(duplicate["pages"][0]["states"][0]))
        variants.append(duplicate)
        screenshot_claim = fixture()
        screenshot_claim["requirements"][0]["verification"] = "browser"
        variants.append(screenshot_claim)
        for variant in variants:
            with self.subTest(variant=variant):
                self.spec = variant
                with self.assertRaises(ValueError):
                    self.build()

    def test_paths_cannot_escape_project(self):
        for path in ("../outside.txt", str((self.root / "绝对.txt").resolve())):
            with self.subTest(path=path):
                self.spec["evidence"][0]["path"] = path
                with self.assertRaises(ValueError):
                    self.build()

    def test_missing_and_fake_screenshot_reject(self):
        self.spec["evidence"].append({"id": "shot", "kind": "screenshot",
                                     "description": "测试截图", "state_ids": ["ready"],
                                     "viewport": {"width": 390, "height": 844}, "path": "fake.png"})
        with self.assertRaises(ValueError):
            self.build()
        (self.root / "fake.png").write_text("not an image", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.build()

    def test_partial_and_unverified_are_disclosed(self):
        self.spec["requirements"][0].update(implementation="partial", verification="not_run",
                                             evidence_ids=[])
        directory, _, notices = self.build()
        self.assertTrue(any("partial" in n for n in notices))
        self.assertTrue(any("尚未验证" in n for n in notices))
        handoff = (directory / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("partial", handoff)
        self.assertIn("not_run", handoff)

    def test_existing_delivery_is_not_overwritten(self):
        directory, archive, _ = self.build()
        original = archive.read_bytes()
        with self.assertRaises(ValueError):
            self.build()
        self.assertTrue(directory.exists())
        self.assertEqual(archive.read_bytes(), original)

    def test_malformed_types_fail_with_validation_error(self):
        for key, value in (("status", []), ("offline", "true")):
            with self.subTest(key=key):
                self.spec = fixture()
                self.spec["brief"][key] = value
                with self.assertRaises(ValueError):
                    self.build()
        self.spec = fixture()
        self.spec["evidence"][0]["kind"] = {}
        with self.assertRaises(ValueError):
            self.build()

    def test_init_cli_and_no_overwrite(self):
        command = [sys.executable, str(SCRIPT), "init", "--output", str(self.spec_path),
                   "--title", "今晚吃什么"]
        first = subprocess.run(command, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        initialized = json.loads(self.spec_path.read_text(encoding="utf-8"))
        self.assertEqual(initialized["title"], "今晚吃什么")
        self.assertEqual(initialized["brief"]["status"], "draft")
        second = subprocess.run(command, capture_output=True)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(initialized, json.loads(self.spec_path.read_text(encoding="utf-8")))

    def visual_plan(self):
        return {"route": "typographic", "intent": "克制的价格层级", "reference_basis": "本次确认的极简方向",
                "anchors": ["价格为主体"], "techniques": ["字重和留白区分主次"],
                "acceptance": ["结果与单位一眼可辨"]}

    def visual_review(self, status="reviewed", level="static"):
        return {"status": status, "level": level, "evidence_ids": ["E1"], "findings": []}

    def visual_finding(self, severity="major", status="open"):
        return {"id": "V1", "severity": severity, "location": "结果数字与单位",
                "state_ids": ["result"], "observation": "单位压住数字", "action": "增加两者间距",
                "status": status}

    def test_visual_plan_and_review_survive_handoff(self):
        self.spec["visual"]["design_plan"] = self.visual_plan()
        self.spec["visual"]["review"] = self.visual_review()
        directory, _, notices = self.build()
        exported = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(exported["visual"], self.spec["visual"])
        report = (directory / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("价格为主体", report)
        self.assertIn("克制的价格层级", report)
        self.assertTrue(any("视觉复查仅静态" in n for n in notices))

    def test_unresolved_major_cannot_be_marked_reviewed(self):
        review = self.visual_review()
        review["findings"] = [self.visual_finding()]
        self.spec["visual"]["review"] = review
        with self.assertRaises(ValueError):
            self.build()
        review["status"] = "needs_revision"
        _, _, notices = self.build()
        self.assertTrue(any("V1" in n and "未处理" in n for n in notices))

    def test_rendered_visual_review_needs_actual_image(self):
        self.spec["visual"]["review"] = self.visual_review(level="rendered")
        with self.assertRaises(ValueError):
            self.build()

    def test_rendered_review_image_is_packaged_with_relative_reference(self):
        # A tiny fixture image tests packaging only; it is not a design screenshot.
        image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jA7sAAAAASUVORK5CYII=")
        (self.root / "fixture.png").write_bytes(image)
        self.spec["evidence"].append({"id": "shot", "kind": "screenshot", "description": "测试文件，不是实际原型画面",
                                     "state_ids": ["result"], "viewport": {"width": 390, "height": 844},
                                     "path": "fixture.png"})
        review = self.visual_review(level="rendered")
        review["evidence_ids"] = ["shot"]
        self.spec["visual"]["review"] = review
        directory, archive, _ = self.build()
        self.assertEqual((directory / "screenshots/shot.png").read_bytes(), image)
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(package.read("交接包/screenshots/shot.png"), image)
        record = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        exporter.validate(record, directory.resolve())
        self.assertIn("[证据文件](screenshots/shot.png)",
                      (directory / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_accepted_difference_needs_user_evidence_and_blockers_stay_open(self):
        finding = self.visual_finding(status="accepted")
        review = self.visual_review()
        review["findings"] = [finding]
        self.spec["visual"]["review"] = review
        with self.assertRaises(ValueError):
            self.build()
        finding["acceptance_evidence"] = "测试中的用户明确保留紧凑排版"
        _, _, notices = self.build()
        self.assertTrue(any("V1" in n and "已接受" in n for n in notices))
        finding["severity"] = "blocker"
        with self.assertRaises(ValueError):
            self.build(name="second")

    def test_unset_route_cannot_be_exported(self):
        self.spec["visual"]["design_plan"] = self.visual_plan()
        self.spec["visual"]["design_plan"]["route"] = "undecided"
        with self.assertRaises(ValueError):
            self.build()


    def motion_plan(self, verification="not_run", evidence_ids=None):
        return {"id": "M1", "interaction_id": "I1", "purpose": "结果与输入关系清楚",
                "continuity": "保留输入值与当前焦点", "properties": ["opacity", "transform"],
                "duration_ms": 220, "easing": "ease-out", "interrupt": "再次提交重定向到最新结果",
                "reduced_motion": "直接切换结果并保留输入", "verification": verification,
                "evidence_ids": [] if evidence_ids is None else evidence_ids}

    def test_motion_behaviors_survive_json_markdown_and_zip(self):
        motion = self.motion_plan()
        self.spec["visual"]["motion_plan"] = [motion]
        directory, archive, notices = self.build()
        record = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        self.assertEqual(record["visual"]["motion_plan"], [motion])
        handoff = (directory / "HANDOFF.md").read_text(encoding="utf-8")
        for behavior in (motion["continuity"], motion["interrupt"], motion["reduced_motion"]):
            self.assertIn(behavior, handoff)
        self.assertIn("ready → result", handoff)
        self.assertNotIn("动效：无额外动效", handoff)
        self.assertIn("visual.motion_plan", (directory / "AI-START.md").read_text(encoding="utf-8"))
        self.assertTrue(any("M1" in n and "尚无动态" in n for n in notices))
        with zipfile.ZipFile(archive) as package:
            self.assertEqual(package.read("交接包/HANDOFF.md"),
                             (directory / "HANDOFF.md").read_bytes())

    def test_invalid_motion_specs_reject_before_writing(self):
        variants = [
            {"duration_ms": -1}, {"duration_ms": True}, {"duration_ms": "220"},
            {"duration_ms": float("nan")}, {"duration_ms": float("inf")},
            {"interaction_id": "absent"}, {"evidence_ids": ["absent"]},
            {"properties": []}, {"interrupt": ""}, {"reduced_motion": ""},
            {"verification": "rendered"},
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                motion = self.motion_plan()
                motion.update(variant)
                self.spec["visual"]["motion_plan"] = [motion]
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse((self.root / "交接包").exists())
                self.assertFalse((self.root / "交接包.zip").exists())
        self.spec["visual"]["motion_plan"] = [self.motion_plan(), self.motion_plan()]
        with self.assertRaises(ValueError):
            self.build()

    def test_screenshot_does_not_prove_dynamic_behavior(self):
        image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jA7sAAAAASUVORK5CYII=")
        (self.root / "fixture.png").write_bytes(image)
        self.spec["evidence"].append({"id": "shot", "kind": "screenshot",
                                     "description": "测试文件，不是运动验证",
                                     "state_ids": ["ready", "result"], "path": "fixture.png",
                                     "viewport": {"width": 390, "height": 844}})
        self.spec["visual"]["motion_plan"] = [self.motion_plan("browser", ["shot"])]
        with self.assertRaisesRegex(ValueError, "截图不能证明运动"):
            self.build()

    def test_motion_running_evidence_covers_related_states(self):
        # These are validation fixtures, not claims that a browser was run here.
        self.spec["evidence"].append({"id": "run", "kind": "browser",
                                     "description": "结构测试中的操作记录占位",
                                     "state_ids": ["result"]})
        self.spec["visual"]["motion_plan"] = [self.motion_plan("browser", ["run"])]
        with self.assertRaisesRegex(ValueError, "前后状态"):
            self.build()
        self.spec["evidence"][-1]["state_ids"] = ["ready", "result"]
        directory, _, notices = self.build()
        self.assertFalse(any("M1" in n and "尚无动态" in n for n in notices))
        exported = json.loads((directory / "design-spec.json").read_text(encoding="utf-8"))
        exporter.validate(exported, directory.resolve())

    def test_static_motion_evidence_keeps_dynamic_warning(self):
        self.spec["visual"]["motion_plan"] = [self.motion_plan("static", ["E1"])]
        _, _, notices = self.build()
        self.assertTrue(any("M1" in n and "尚无动态" in n for n in notices))

    def test_empty_optional_motion_plan_preserves_legacy_export(self):
        self.spec["visual"]["motion_plan"] = []
        directory, _, notices = self.build()
        handoff = (directory / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("动效：无额外动效", handoff)
        self.assertFalse(any("动效" in n for n in notices))

    def test_device_motion_claim_needs_device_records(self):
        self.spec["evidence"].append({"id": "run", "kind": "browser",
                                     "description": "结构测试占位",
                                     "state_ids": ["ready", "result"]})
        self.spec["visual"]["motion_plan"] = [self.motion_plan("device", ["run"])]
        with self.assertRaisesRegex(ValueError, "device"):
            self.build()
        self.spec["evidence"][-1]["kind"] = "device"
        self.build()


if __name__ == "__main__":
    unittest.main()
