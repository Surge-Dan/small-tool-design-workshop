#!/usr/bin/env python3
"""Save recoverable prototypes and bind explicitly observed evidence to bytes.

Standard library only. No browser execution or semantic/visual equivalence checks.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local(root, relative):
    require(isinstance(relative, str) and relative.strip(), "文件路径不能为空")
    path = Path(relative)
    require(not path.is_absolute() and not path.drive and ".." not in path.parts,
            "只接受目录内相对路径")
    result = (root / path).resolve()
    require(result.is_relative_to(root.resolve()) and result != root.resolve(),
            "文件路径超出目录")
    return result


def atomic_json(path, value):
    # Replace only the explicitly supplied design record; clean up on failure.
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False, prefix=".state-", suffix=".json") as file:
            temp = Path(file.name)
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def html_file(path):
    require(path.is_file() and path.suffix.lower() in (".html", ".htm"), "需要现有HTML文件")
    data = path.read_bytes()
    require(bool(data.decode("utf-8-sig").strip()), "HTML文件为空")
    return data


def bind(spec_path, html_path, evidence_ids=()):
    spec_path = spec_path.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    require(isinstance(spec, dict), "设计记录必须为对象")
    records = spec.get("evidence", [])
    require(isinstance(records, list) and all(isinstance(e, dict) for e in records),
            "证据必须为对象数组")
    ids = [e.get("id") for e in records]
    require(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids), "证据ID缺失或重复")
    require(len(set(evidence_ids)) == len(evidence_ids), "指定证据ID重复")
    require(set(evidence_ids).issubset(ids), "指定证据不存在")
    current = digest(html_file(html_path))
    spec["prototype_sha256"] = current
    for entry in records:
        if entry["id"] in evidence_ids:
            entry["prototype_sha256"] = current
            if entry.get("path") is not None:
                source = local(spec_path.parent, entry["path"])
                entry["attachment_sha256"] = digest(source.read_bytes())
            else:
                entry.pop("attachment_sha256", None)
    atomic_json(spec_path, spec)
    return current


def capture(html_path, output, spec_path=None):
    output = output.absolute()
    require(not output.exists(), "快照目录已存在，不覆盖")
    data = html_file(html_path)
    entries = [("prototype.html", html_path.name, data)]
    if spec_path is not None:
        spec_data = spec_path.read_bytes()
        spec = json.loads(spec_data.decode("utf-8-sig"))
        require(isinstance(spec, dict), "设计记录必须为对象")
        require(spec_path.suffix.lower() == ".json", "设计记录需为JSON文件")
        entries.append(("design-spec.json", spec_path.name, spec_data))
        for entry in spec.get("evidence", []):
            require(isinstance(entry, dict), "证据必须为对象")
            if entry.get("path") is not None:
                source = local(spec_path.parent, entry["path"])
                relative = source.relative_to(spec_path.parent.resolve()).as_posix()
                entries.append(("attachments/" + relative, relative, source.read_bytes()))
    # Resolve collisions before creating any output.
    targets = {}
    for saved, target, content in entries:
        local(output, saved)
        local(output, target)
        if target in targets:
            require(targets[target] == (saved, content), "快照文件目标冲突")
        targets[target] = (saved, content)
    for target in targets:
        require(not any(parent.as_posix() in targets for parent in Path(target).parents),
                "快照文件与目录目标冲突")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=output.parent) as temp:
        stage = Path(temp) / "content"
        stage.mkdir()
        manifest = {"schema_version": 1, "files": []}
        for target, (saved, content) in targets.items():
            destination = local(stage, saved)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            manifest["files"].append({"saved": saved, "target": target, "sha256": digest(content)})
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        require(not output.exists(), "快照目录已存在，不覆盖")
        stage.rename(output)
    return output


def restore(snapshot, output):
    snapshot = snapshot.resolve()
    output = output.absolute()
    require(not output.exists(), "恢复到新目录，不覆盖当前原型")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    require(isinstance(manifest, dict) and manifest.get("schema_version") == 1
            and isinstance(manifest.get("files"), list),
            "快照格式无效")
    entries = []
    targets = set()
    for entry in manifest["files"]:
        require(isinstance(entry, dict), "快照文件记录必须为对象")
        source = local(snapshot, entry["saved"])
        local(output, entry["target"])
        require(entry["target"] not in targets, "恢复目标重复")
        targets.add(entry["target"])
        content = source.read_bytes()
        require(digest(content) == entry["sha256"], "快照内容已损坏或被修改")
        entries.append((entry["target"], content))
    for target in targets:
        require(not any(parent.as_posix() in targets for parent in Path(target).parents),
                "恢复文件与目录目标冲突")
    require(any(e.get("saved") == "prototype.html" for e in manifest["files"]), "快照缺少原型")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".restore-", dir=output.parent) as temp:
        stage = Path(temp) / "content"
        stage.mkdir()
        for target, content in entries:
            destination = local(stage, target)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        require(not output.exists(), "恢复目录已存在，不覆盖")
        stage.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("snapshot", help="保存修改前HTML、可选记录与引用附件")
    save.add_argument("--html", type=Path, required=True)
    save.add_argument("--spec", type=Path)
    save.add_argument("--output", type=Path, required=True)
    undo = commands.add_parser("restore", help="校验快照并恢复到新目录")
    undo.add_argument("--snapshot", type=Path, required=True)
    undo.add_argument("--output", type=Path, required=True)
    mark = commands.add_parser("bind", help="绑定当前HTML及明确指定、已经观察过的证据")
    mark.add_argument("--html", type=Path, required=True)
    mark.add_argument("--spec", type=Path, required=True)
    mark.add_argument("--evidence-id", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            print(capture(args.html, args.output, args.spec))
        elif args.command == "restore":
            print(restore(args.snapshot, args.output))
        else:
            print("已绑定HTML：" + bind(args.spec, args.html, args.evidence_id))
            print("仅标记指定证据；命令不执行观察、运行测试或视觉验收。")
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as error:
        print(f"未完成：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
