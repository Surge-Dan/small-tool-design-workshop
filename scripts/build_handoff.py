#!/usr/bin/env python3
"""Validate a design record and export an AI development reference bundle.

Standard library only. This validates recorded claims, not prototype behavior.
"""

import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
KINDS = ("screenshot", "static", "browser", "device", "offline", "export")
ROUTES = ("typographic", "object-led", "asset-led", "scene-led")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def fingerprint(value, context):
    require(isinstance(value, str) and SHA256.fullmatch(value) is not None,
            f"{context}必须为小写SHA-256")
    return value


def version_manifest(spec, html_bytes, attachment_bytes):
    actual = hashlib.sha256(html_bytes).hexdigest()
    recorded = spec.get("prototype_sha256")
    if recorded is not None:
        require(fingerprint(recorded, "prototype_sha256") == actual,
                "HTML版本已变化；更新设计记录并重新检查受影响项后再导出")
    bindings = []
    for entry in spec["evidence"]:
        bound = entry.get("prototype_sha256")
        if recorded is not None:
            require(bound is not None,
                    f"证据{entry['id']}未绑定HTML版本；新记录需实际检查后逐项绑定，不能沿用未知版本证据")
        if bound is not None:
            require(fingerprint(bound, f"{entry['id']}.prototype_sha256") == actual,
                    f"证据{entry['id']}属于旧HTML版本；移除过期证据或重新检查，不能直接重标哈希")
        source = attachment_bytes[entry["id"]]
        digest = hashlib.sha256(source).hexdigest() if source is not None else None
        saved = entry.get("attachment_sha256")
        if recorded is not None and source is not None:
            require(saved is not None,
                    f"证据附件{entry['id']}未绑定内容版本；新记录需实际检查后记录附件哈希")
        if saved is not None:
            require(source is not None, f"{entry['id']}记录附件哈希但没有附件")
            require(fingerprint(saved, f"{entry['id']}.attachment_sha256") == digest,
                    f"证据附件{entry['id']}已变化；重新检查后更新记录")
        bindings.append({"id": entry["id"], "prototype_sha256": bound,
                         "attachment_sha256": digest, "version_bound": bound is not None})
    return {"prototype_sha256": actual, "prototype_bytes": len(html_bytes),
            "evidence": bindings,
            "scope": "字节版本与附件一致性，不证明观察真实、功能通过或审美质量"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_field(obj, key, context, allow_empty=False):
    value = obj.get(key)
    require(isinstance(value, str), f"{context}.{key}必须是字符串")
    require(allow_empty or bool(value.strip()), f"{context}.{key}不能为空")
    return value


def items(obj, key, context, nonempty=False):
    value = obj.get(key)
    require(isinstance(value, list), f"{context}.{key}必须是数组")
    require(not nonempty or bool(value), f"{context}.{key}不能为空")
    return value


def strings(obj, key, context, nonempty=False):
    value = items(obj, key, context, nonempty)
    require(all(isinstance(s, str) and s.strip() for s in value),
            f"{context}.{key}只能包含非空字符串")
    return value


def index(entries, context):
    result = {}
    for entry in entries:
        require(isinstance(entry, dict), f"{context}条目必须是对象")
        key = text_field(entry, "id", context)
        require(ID.fullmatch(key) is not None, f"{context}的ID无效：{key}")
        require(key not in result, f"{context}的ID重复：{key}")
        result[key] = entry
    return result


def references(values, known, context):
    require(len(set(values)) == len(values), f"{context}含重复引用")
    for value in values:
        require(value in known, f"{context}引用不存在的ID：{value}")


def attachment(entry, root):
    raw = entry.get("path")
    if raw is None:
        require(entry["kind"] != "screenshot", "截图必须提供实际文件路径")
        return None
    require(isinstance(raw, str) and raw.strip(), "证据path必须为非空相对路径")
    relative = Path(raw)
    require(not relative.is_absolute() and not relative.drive,
            "证据文件必须使用项目内相对路径")
    source = (root / relative).resolve()
    require(source.is_relative_to(root), "证据路径超出设计记录所在目录")
    require(source.is_file(), f"证据文件不存在：{raw}")
    suffix = source.suffix.lower()
    if entry["kind"] == "screenshot":
        with source.open("rb") as handle:
            head = handle.read(12)
        valid = ((suffix == ".png" and head.startswith(b"\x89PNG\r\n\x1a\n"))
                 or (suffix in {".jpg", ".jpeg"} and head.startswith(b"\xff\xd8\xff"))
                 or (suffix == ".webp" and head[:4] == b"RIFF" and head[8:12] == b"WEBP"))
        require(valid, f"截图类型或文件头不符：{raw}")
    else:
        require(suffix in {".txt", ".md", ".json"}, "操作日志仅接受UTF-8文本、Markdown或JSON")
        source.read_text(encoding="utf-8-sig")
    return source


def validate(spec, root):
    require(isinstance(spec, dict), "设计记录必须是JSON对象")
    require(type(spec.get("schema_version")) is int and spec["schema_version"] == 1,
            "schema_version必须为1")
    text_field(spec, "title", "spec")
    brief = spec.get("brief")
    require(isinstance(brief, dict), "brief必须是对象")
    require(brief.get("status") in ("confirmed", "delegated"),
            "设计仍是草稿；需真实确认或明确委托后才能导出开发参考包")
    for key in ("confirmation_evidence", "target_user", "scenario", "goal"):
        text_field(brief, key, "brief")
    strings(brief, "non_goals", "brief")
    require(type(brief.get("offline")) is bool, "brief.offline必须是布尔值")
    require(not strings(brief, "blocking_questions", "brief"), "仍有未解决的关键问题")
    pages = index(items(spec, "pages", "spec", True), "pages")
    all_states = []
    for page in pages.values():
        for key in ("name", "layout"):
            text_field(page, key, "page")
        states = items(page, "states", "page", True)
        for state in index(states, "states").values():
            text_field(state, "description", "state")
        all_states.extend(states)
    states = index(all_states, "states")
    evidence = index(items(spec, "evidence", "spec"), "evidence")
    attachments = {}
    for entry in evidence.values():
        require(entry.get("kind") in KINDS, "无效证据类型")
        text_field(entry, "description", "evidence")
        state_ids = strings(entry, "state_ids", "evidence",
                            entry["kind"] == "screenshot")
        references(state_ids, states, "evidence.state_ids")
        if entry["kind"] == "screenshot":
            viewport = entry.get("viewport")
            require(isinstance(viewport, dict), "截图需记录viewport")
            for dimension in ("width", "height"):
                value = viewport.get(dimension)
                require(value is None or (type(value) is int and value > 0),
                        "截图视口必须是正整数；未记录的维度用null")
                require(dimension in viewport, "截图视口需包含width和height")
        attachments[entry["id"]] = attachment(entry, root)
    requirements = index(items(spec, "requirements", "spec", True), "requirements")
    for req in requirements.values():
        for key in ("description", "acceptance"):
            text_field(req, key, "requirement")
        references(strings(req, "page_ids", "requirement", True), pages, "requirement.page_ids")
        require(req.get("implementation") in ("planned", "partial", "implemented"),
                "无效实现状态")
        level = req.get("verification")
        require(level in ("not_run", "static", "browser", "device"), "无效验证级别")
        evidence_ids = strings(req, "evidence_ids", "requirement")
        references(evidence_ids, evidence, "requirement.evidence_ids")
        if level != "not_run":
            require(any(evidence[e]["kind"] == level for e in evidence_ids),
                    f"{req['id']}缺少{level}操作记录；截图不能替代运行验证")
    interactions = index(items(spec, "interactions", "spec"), "interactions")
    for interaction in interactions.values():
        for key in ("from_state", "to_state", "trigger", "feedback"):
            text_field(interaction, key, "interaction")
        for key in ("guard", "preserves"):
            text_field(interaction, key, "interaction", allow_empty=True)
        references([interaction["from_state"]], states, "interaction.from_state")
        references([interaction["to_state"]], states, "interaction.to_state")
    for rule in index(items(spec, "logic", "spec"), "logic").values():
        for key in ("description", "rule", "example"):
            text_field(rule, key, "logic")
        strings(rule, "inputs", "logic")
        require(type(rule.get("simulation")) is bool, "logic.simulation必须是布尔值")
    visual = spec.get("visual")
    require(isinstance(visual, dict), "visual必须是对象")
    text_field(visual, "direction", "visual")
    text_field(visual, "motion", "visual", allow_empty=True)
    tokens = visual.get("tokens")
    require(isinstance(tokens, dict) and bool(tokens), "记录实际采用的visual.tokens")
    require(all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
                for k, v in tokens.items()), "设计参数必须为非空名称和字符串值")
    if "motion_plan" in visual:
        motions = index(items(visual, "motion_plan", "visual"), "visual.motion_plan")
        for motion in motions.values():
            for key in ("interaction_id", "purpose", "continuity", "easing",
                        "interrupt", "reduced_motion"):
                text_field(motion, key, "motion")
            references([motion["interaction_id"]], interactions, "motion.interaction_id")
            strings(motion, "properties", "motion", True)
            duration = motion.get("duration_ms")
            require(type(duration) in (int, float) and duration >= 0
                    and (type(duration) is int or math.isfinite(duration)),
                    "motion.duration_ms必须为有限的非负毫秒数")
            level = motion.get("verification")
            require(level in ("not_run", "static", "browser", "device"), "无效动效验证级别")
            evidence_ids = strings(motion, "evidence_ids", "motion")
            references(evidence_ids, evidence, "motion.evidence_ids")
            if level != "not_run":
                records = [evidence[e] for e in evidence_ids if evidence[e]["kind"] == level]
                require(bool(records), f"{motion['id']}缺少{level}动效记录；截图不能证明运动")
                if level in ("browser", "device"):
                    interaction = interactions[motion["interaction_id"]]
                    covered = {state for record in records for state in record["state_ids"]}
                    require({interaction["from_state"], interaction["to_state"]}.issubset(covered),
                            f"{motion['id']}的操作记录需关联前后状态")
    if "design_plan" in visual:
        plan = visual["design_plan"]
        require(isinstance(plan, dict), "visual.design_plan必须是对象")
        require(plan.get("route") in ROUTES, "选择实际视觉路线，不能导出未定方向")
        for key in ("intent", "reference_basis"):
            text_field(plan, key, "visual.design_plan")
        for key in ("anchors", "techniques", "acceptance"):
            strings(plan, key, "visual.design_plan", True)
    if "review" in visual:
        review = visual["review"]
        require(isinstance(review, dict), "visual.review必须是对象")
        status = review.get("status")
        level = review.get("level")
        require(status in ("not_reviewed", "reviewed", "needs_revision"), "无效视觉复查状态")
        require(level in ("not_run", "static", "rendered"), "无效视觉复查级别")
        evidence_ids = strings(review, "evidence_ids", "visual.review")
        references(evidence_ids, evidence, "visual.review.evidence_ids")
        if status != "not_reviewed":
            require(level != "not_run", "已复查需注明静态或实际渲染级别")
        if level != "not_run":
            kind = "screenshot" if level == "rendered" else "static"
            require(any(evidence[e]["kind"] == kind for e in evidence_ids),
                    f"视觉{level}复查缺少对应证据；不能用文字记录代替实际画面")
        findings = index(items(review, "findings", "visual.review"), "visual.review.findings")
        for finding in findings.values():
            for key in ("location", "observation", "action"):
                text_field(finding, key, "visual.finding")
            require(finding.get("severity") in ("blocker", "major", "minor"), "无效视觉问题级别")
            require(finding.get("status") in ("open", "fixed", "accepted"), "无效视觉问题处理状态")
            references(strings(finding, "state_ids", "visual.finding"), states, "visual.finding.state_ids")
            if finding["status"] == "accepted":
                text_field(finding, "acceptance_evidence", "visual.finding")
            if status == "reviewed":
                require(not (finding["severity"] == "blocker" and finding["status"] != "fixed"),
                        "视觉阻断问题未修复，不能标记复查完成")
                require(not (finding["severity"] == "major" and finding["status"] == "open"),
                        "主要视觉问题仍未处理，不能标记复查完成")
    for asset in items(visual, "assets", "visual"):
        require(isinstance(asset, dict), "资产条目必须是对象")
        for key in ("name", "source", "license", "usage"):
            text_field(asset, key, "asset")
        require(type(asset.get("embedded")) is bool, "asset.embedded必须是布尔值")
    for key in ("assumptions", "limitations"):
        strings(spec, key, "spec")
    if "changes" in spec:
        strings(spec, "changes", "spec")
    if "revision" in spec:
        text_field(spec, "revision", "spec")
    return attachments


def warnings(spec):
    result = list(spec["limitations"])
    if spec.get("prototype_sha256") is None:
        result.append("旧版设计记录未绑定HTML版本，无法核验记录与当前原型的一致性")
    if any(e.get("prototype_sha256") is None for e in spec["evidence"]):
        result.append("部分证据未绑定HTML版本，仅作未核验版本的参考；不能自动视为当前验证")
    visual = spec["visual"]
    for motion in visual.get("motion_plan", []):
        if motion["verification"] in ("not_run", "static"):
            result.append(f"动效{motion['id']}尚无动态操作验证：{motion['verification']}")
    if "design_plan" not in visual:
        result.append("未记录视觉设计路线；旧版记录仍可交接")
    review = visual.get("review")
    if review is None or review["status"] == "not_reviewed":
        result.append("未记录已执行的视觉复查")
    elif review["status"] == "needs_revision":
        result.append("视觉复查仍需修正，不能称完整视觉验收通过")
    if review:
        if review["level"] == "static":
            result.append("视觉复查仅静态检查，未验收实际渲染画面")
        for finding in review["findings"]:
            if finding["status"] == "open":
                result.append(f"视觉问题{finding['id']}未处理：{finding['observation']}")
            elif finding["status"] == "accepted":
                result.append(f"视觉差异{finding['id']}已接受：{finding['observation']}")
    for req in spec["requirements"]:
        if req["implementation"] != "implemented":
            result.append(f"{req['id']}实现状态：{req['implementation']}")
        if req["verification"] == "not_run":
            result.append(f"{req['id']}尚未验证")
        elif req["verification"] == "static":
            result.append(f"{req['id']}仅静态检查，未证明交互可用")
    if not any(e["kind"] == "screenshot" for e in spec["evidence"]):
        result.append("未附实际页面截图，请打开prototype.html查看")
    for e in spec["evidence"]:
        if e["kind"] == "screenshot" and any(e["viewport"][d] is None for d in ("width", "height")):
            result.append(f"{e['id']}截图的视口尺寸记录不完整")
    if spec["brief"]["offline"] and not any(e["kind"] == "offline" for e in spec["evidence"]):
        result.append("要求离线交付，但未记录断网直接打开文件的验证证据")
    return list(dict.fromkeys(result))


def bullet(values):
    return "\n".join("- " + v.replace("\n", "\n  ") for v in values) or "- 无记录"


def handoff(spec):
    b = spec["brief"]
    lines = [f"# {spec['title']}开发交接", "", "## 设计依据", "",
             f"- 版本：{spec.get('revision', '未标注')}",
             f"- 记录绑定的HTML SHA-256：{spec.get('prototype_sha256') or '未绑定'}",
             "- 实际导出文件及证据的版本清单见ARTIFACT.json；哈希一致不代表功能或视觉通过。",
             f"- 确认状态：{b['status']}；依据：{b['confirmation_evidence']}",
             f"- 用户：{b['target_user']}", f"- 场景：{b['scenario']}",
             f"- 目标：{b['goal']}", f"- 离线要求：{'是' if b['offline'] else '否'}",
             "", "### 明确不做", "", bullet(b["non_goals"]),
             "", "## 页面与状态", ""]
    for p in spec["pages"]:
        lines.extend([f"### {p['id']}：{p['name']}", "", p["layout"], "",
                      bullet([f"{s['id']}：{s['description']}" for s in p["states"]]), ""])
    lines.extend(["## 需求与验收", ""])
    for r in spec["requirements"]:
        lines.extend([f"### {r['id']}：{r['description']}", "",
                      f"- 关联页面：{', '.join(r['page_ids'])}",
                      f"- 验收：{r['acceptance']}",
                      f"- 实现：{r['implementation']}；验证：{r['verification']}",
                      f"- 证据：{', '.join(r['evidence_ids']) or '无'}", ""])
    lines.extend(["## 交互", ""])
    for i in spec["interactions"]:
        lines.extend([f"### {i['id']}：{i['trigger']}", "",
                      f"- 状态：{i['from_state']} → {i['to_state']}",
                      f"- 条件：{i['guard'] or '无额外条件'}",
                      f"- 反馈：{i['feedback']}", f"- 保留：{i['preserves'] or '无'}", ""])
    lines.extend(["## 业务规则与模拟边界", ""])
    for rule in spec["logic"]:
        lines.extend([f"### {rule['id']}：{rule['description']}", "",
                      f"- 输入：{', '.join(rule['inputs']) or '无'}", f"- 规则：{rule['rule']}",
                      f"- 例子：{rule['example']}",
                      f"- 模拟：{'是' if rule['simulation'] else '否'}", ""])
    lines.extend(["## 视觉与资产", "", spec["visual"]["direction"], "", "```json",
                  json.dumps(spec["visual"]["tokens"], ensure_ascii=False, indent=2), "```", "",
                  f"动效：{spec['visual']['motion'] or ('关键运动详见下方' if spec['visual'].get('motion_plan') else '无额外动效')}", ""])
    motions = spec["visual"].get("motion_plan", [])
    if motions:
        lines.extend(["### 关键运动与连续操作", "",
                      "规格与记录不等于运动质量已通过；按对应操作证据核对。", ""])
        interactions = {entry["id"]: entry for entry in spec["interactions"]}
        for motion in motions:
            interaction = interactions[motion["interaction_id"]]
            lines.extend([f"#### {motion['id']}：{motion['purpose']}", "",
                          f"- 交互：{motion['interaction_id']}；触发：{interaction['trigger']}",
                          f"- 状态：{interaction['from_state']} → {interaction['to_state']}",
                          f"- 连续性：{motion['continuity']}",
                          f"- 属性：{', '.join(motion['properties'])}",
                          f"- 时长：{motion['duration_ms']}ms；曲线：{motion['easing']}",
                          f"- 快速重复／中断：{motion['interrupt']}",
                          f"- 减少动效：{motion['reduced_motion']}",
                          f"- 验证：{motion['verification']}；证据：{', '.join(motion['evidence_ids']) or '无'}", ""])
    lines.append(bullet([f"{a['name']}：{a['usage']}；来源：{a['source']}；许可：{a['license']}；"
                         f"内嵌：{'是' if a['embedded'] else '否'}" for a in spec["visual"]["assets"]]))
    plan = spec["visual"].get("design_plan")
    if plan:
        lines.extend(["", "### 视觉计划", "", f"- 主要路线：{plan['route']}",
                      f"- 表现意图：{plan['intent']}", f"- 参考依据：{plan['reference_basis']}",
                      "", "需保留的视觉特征：", "", bullet(plan["anchors"]),
                      "", "方法与理由：", "", bullet(plan["techniques"]),
                      "", "视觉验收：", "", bullet(plan["acceptance"])])
    review = spec["visual"].get("review")
    if review:
        lines.extend(["", "### 对抗式视觉复查", "",
                      f"- 记录状态：{review['status']}；检查级别：{review['level']}",
                      f"- 证据：{', '.join(review['evidence_ids']) or '无'}", ""])
        for finding in review["findings"]:
            lines.extend([f"#### {finding['id']}：{finding['severity']}／{finding['status']}", "",
                          f"- 位置：{finding['location']}",
                          f"- 状态：{', '.join(finding['state_ids']) or '整体'}",
                          f"- 观察：{finding['observation']}", f"- 处理：{finding['action']}"])
            if finding["status"] == "accepted":
                lines.append(f"- 接受依据：{finding['acceptance_evidence']}")
            lines.append("")
    lines.extend(["", "## 验证记录与截图", "",
                  "以下是Agent记录的证据。打包器仅校验结构与文件，不独立执行或确认这些测试。", ""])
    for e in spec["evidence"]:
        viewport = e.get("viewport") if e["kind"] == "screenshot" else None
        size = (f"；视口：{viewport['width'] or '未记录'}×{viewport['height'] or '未记录'}"
                if viewport else "")
        lines.extend([f"### {e['id']}：{e['kind']}", "", e["description"], "",
                      f"状态：{', '.join(e['state_ids']) or '整体检查'}{size}", ""])
        if "path" in e:
            lines.extend([f"[证据文件]({e['path']})", ""])
    lines.extend(["## 假设", "", bullet(spec["assumptions"]),
                  "", "## 限制与未完成事项", "", bullet(warnings(spec)),
                  "", "## 本次变动", "", bullet(spec.get("changes", [])), ""])
    return "\n".join(lines)


AI_START = """# 给下一位AI的开工说明

请根据本包实现产品。先读HANDOFF.md与design-spec.json，打开prototype.html，查看已有screenshots中的状态截图。

- 以已确认需求、业务规则、页面状态和验收例子为约束，保留原型的视觉层级、素材与交互；不要只凭截图猜规则或默认套通用模板。
- 有visual.design_plan和visual.review时读取表现意图、必保留特征、方法及未完成发现。不要把简约自动加装饰，也不要把复杂方向简化成默认表单。reviewed只表示记录的复查已完成，不保证视觉效果或运行测试通过。
- 有visual.motion_plan时保留前后状态、对象连续性、时长曲线、中断与减少动效行为。实现方式可按目标环境调整，不能只复刻动画外观而丢失焦点、滚动和业务状态；截图不能证明动态表现。
- 用ARTIFACT.json核对当前HTML字节版本；未绑定版本的旧证据只作参考，修改HTML后重新检查受影响项，不把旧证据直接重标为当前版本。
- 用户最新明确的需求优先。原型、截图与设计记录若冲突，指出具体冲突并确认，不悄悄决定。未实现、未验证不等于没有要求。
- 若用户尚未指定目标平台、技术栈和真实数据来源，先确认开发需要的缺口。原型里的模拟数据、价格和服务不能冒充生产接口；不擅自加入登录、支付或后台。
- prototype.html是设计与行为参考，不能直接认定为生产代码。按目标环境实现，遵守资产许可，保留明确的排除项与离线约束。
- 实现后按需求ID验收核心路径、异常恢复与窄屏显示，区分静态检查、浏览器操作及真机结果。

本包不保证已经真机验证、通过平台审核或适合直接上线。格式校验不会证明设计效果、业务正确性或运行时离线可用，具体证据与限制见HANDOFF.md。
"""


def build(spec_path, html_path, output):
    spec_path = spec_path.resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    attachments = validate(spec, spec_path.parent)
    html_path = html_path.resolve()
    require(html_path.is_file() and html_path.suffix.lower() in {".html", ".htm"},
            "提供存在的HTML原型文件")
    html_bytes = html_path.read_bytes()
    require(bool(html_bytes.decode("utf-8-sig").strip()), "原型文件为空")
    attachment_bytes = {key: source.read_bytes() if source is not None else None
                        for key, source in attachments.items()}
    artifact = version_manifest(spec, html_bytes, attachment_bytes)
    output = output.absolute()
    archive_path = output.with_name(output.name + ".zip")
    require(not output.exists() and not archive_path.exists(), "输出目录或ZIP已存在，请使用新名称")
    require(bool(output.name), "输出需要指定新目录名称")
    output.parent.mkdir(parents=True, exist_ok=True)
    exported = copy.deepcopy(spec)
    with tempfile.TemporaryDirectory(prefix=".handoff-", dir=output.parent) as temp:
        temp = Path(temp)
        content = temp / "content"
        content.mkdir()
        (content / "prototype.html").write_bytes(html_bytes)
        for e in exported["evidence"]:
            source = attachments[e["id"]]
            if source is not None:
                folder = "screenshots" if e["kind"] == "screenshot" else "evidence"
                relative = Path(folder) / (e["id"] + source.suffix.lower())
                (content / folder).mkdir(exist_ok=True)
                (content / relative).write_bytes(attachment_bytes[e["id"]])
                e["path"] = relative.as_posix()
        (content / "design-spec.json").write_text(
            json.dumps(exported, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (content / "HANDOFF.md").write_text(handoff(exported), encoding="utf-8")
        (content / "AI-START.md").write_text(AI_START, encoding="utf-8")
        (content / "ARTIFACT.json").write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        staged_zip = temp / "bundle.zip"
        with zipfile.ZipFile(staged_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(content.rglob("*")):
                if file.is_file():
                    archive.write(file, (Path(output.name) / file.relative_to(content)).as_posix())
        # Exclusive creation prevents accidental replacement of an existing delivery.
        # Only remove a ZIP this operation itself created if the final move fails.
        created_archive = False
        try:
            with archive_path.open("xb") as destination:
                created_archive = True
                with staged_zip.open("rb") as source:
                    shutil.copyfileobj(source, destination)
            content.rename(output)
        except OSError:
            if created_archive:
                archive_path.unlink(missing_ok=True)
            raise
    return output, archive_path, warnings(spec)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="生成待确认的设计记录草稿")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--title", default="待命名工具")
    export = commands.add_parser("build", help="校验并生成开发参考目录与ZIP")
    export.add_argument("--spec", type=Path, required=True)
    export.add_argument("--html", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            require(bool(args.title.strip()), "工具名不能为空")
            template = Path(__file__).resolve().parent.parent / "assets" / "design-spec.template.json"
            spec = json.loads(template.read_text(encoding="utf-8"))
            spec["title"] = args.title
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as file:
                json.dump(spec, file, ensure_ascii=False, indent=2)
                file.write("\n")
            print(f"已生成草稿：{args.output}")
        else:
            directory, archive, notices = build(args.spec, args.html, args.output)
            print(f"已导出：{directory}\nZIP：{archive}")
            for notice in notices:
                print(f"注意：{notice}")
    except (ValueError, OSError, UnicodeError) as error:
        print(f"未导出：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
