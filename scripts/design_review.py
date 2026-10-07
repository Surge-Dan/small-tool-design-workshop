"""Build an offline reference/screenshot board; no aesthetic scoring or rendering."""

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import sys


def image_uri(path):
    data = path.read_bytes()
    if not data or len(data) > 16 * 1024 * 1024:
        raise ValueError(f"图片为空或超过16MB：{path.name}")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ValueError(f"只接受PNG/JPEG/WebP位图：{path.name}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def build(manifest_path, output, prototype=None):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    entries = manifest.get("items") if isinstance(manifest, dict) else None
    if not isinstance(entries, list) or not 1 <= len(entries) <= 20:
        raise ValueError("items需含1～20张实际图片")
    prototype_hash = (hashlib.sha256(Path(prototype).read_bytes()).hexdigest()
                      if prototype is not None else None)
    cards = []
    for item in entries:
        if not isinstance(item, dict) or item.get("role") not in {"reference", "approved", "current"}:
            raise ValueError("role需为reference、approved或current")
        for key in ("label", "path"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"缺少{key}")
        if "://" in item["path"] or item["path"].startswith("data:"):
            raise ValueError("path必须是已有本地图片，不下载远程图片")
        path = Path(item["path"])
        path = path if path.is_absolute() else manifest_path.parent / path
        width = item.get("viewport_width")
        if width is not None and (type(width) is not int or not 100 <= width <= 4000):
            raise ValueError("viewport_width需为100～4000的CSS像素整数")
        bound = item.get("prototype_sha256")
        if bound is not None and (not isinstance(bound, str) or len(bound) != 64
                                  or any(c not in "0123456789abcdefABCDEF" for c in bound)):
            raise ValueError("prototype_sha256需为64位十六进制")
        if item["role"] == "current" and bound and prototype_hash and bound.lower() != prototype_hash:
            raise ValueError(f"当前截图绑定旧HTML：{item['label']}")
        roles = {"reference": "参考素材，非原型证据", "approved": "已认可画面，版本按原记录",
                 "current": "当前画面声明，来源须由操作者核对"}
        status = roles[item["role"]]
        if item["role"] == "current":
            status += "；HTML哈希一致" if bound and prototype_hash else "；版本未核验"
        scale = f"视口宽{width}px" if width else "视口未知，不作等尺度判断"
        details = f"{status}；{scale}；{item.get('state', '状态未记录')}"
        if item.get("source"):
            details += f"；来源：{item['source']}"
        cards.append(f'<article><h2>{html.escape(item["label"])}</h2>'
                     f'<p>{html.escape(details)}</p><div class="image">'
                     f'<img style="width:{width or 390}px" src="{image_uri(path)}" '
                     f'alt="{html.escape(item["label"], quote=True)}"></div></article>')
    title = html.escape(str(manifest.get("title", "参考与画面对照")))
    document = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{margin:24px;background:#eee;color:#202020;font:15px system-ui}}
h1{{font-size:22px}}p{{line-height:1.6}}main{{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}}
article{{background:white;padding:16px;max-width:calc(100vw - 80px)}}h2{{font-size:17px}}
article p{{max-width:390px}}.image{{overflow:auto}}img{{display:block;height:auto;max-width:none}}</style>
<h1>{title}</h1><p>仅供人工对照。未渲染原型、未执行交互、未评判美丑。
宽度来自输入记录，不推断设备或截图像素密度；哈希一致不证明截图确实来自该版本。</p>
<main>{''.join(cards)}</main></html>'''
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as file:
        file.write(document)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--html", type=Path, help="核对current截图原有绑定，不生成或重标证据")
    args = parser.parse_args()
    try:
        print(build(args.manifest, args.output, args.html))
    except (ValueError, OSError, UnicodeError) as error:
        print(f"未生成对照：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
