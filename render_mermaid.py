#!/usr/bin/env python3
"""从 manuscript.md 提取 mermaid 代码块，用 mmdc 渲染成 PNG。

mmdc 自带 puppeteer chromium 在 Win 启动失败，改用 playwright 的 chromium
（经 puppeteerConfigFile 指定 executablePath）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(r"d:\Project\Person\internship")
MANUSCRIPT = WORKSPACE / "manuscript.md"
IMAGES_DIR = WORKSPACE / "images"
CHROMIUM = r"C:\Users\int2t\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"

MMDC = r"D:\DevelopTools\nodejs\node_global\mmdc.cmd"

def main():
    IMAGES_DIR.mkdir(exist_ok=True)
    # puppeteer config 指向 playwright chromium
    cfg = {"executablePath": CHROMIUM, "args": ["--no-sandbox", "--disable-setuid-sandbox"]}
    cfg_path = IMAGES_DIR / ".puppeteer.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    text = MANUSCRIPT.read_text(encoding="utf-8")
    # 按 ^---$ 分页（每段含正文 + Notes）
    pages = re.split(r"^---\s*$", text, flags=re.MULTILINE)

    mermaid_re = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    rendered = 0
    for idx, page in enumerate(pages, 1):
        m = mermaid_re.search(page)
        if not m:
            continue
        code = m.group(1).strip()
        mmd_src = IMAGES_DIR / f".mmd_{idx:02d}.mmd"
        png_out = IMAGES_DIR / f"mmd_{idx:02d}.png"
        mmd_src.write_text(code, encoding="utf-8")

        cmd = [
            MMDC, "-i", str(mmd_src), "-o", str(png_out),
            "-w", "1600", "-H", "900", "-b", "white", "-s", "2",
            "-p", str(cfg_path),
        ]
        print(f"[page {idx:02d}] rendering mermaid -> {png_out.name}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not png_out.exists():
            print(f"  FAIL: {r.stderr.strip() or r.stdout.strip()}", file=sys.stderr)
            mmd_src.unlink(missing_ok=True)
            sys.exit(1)
        mmd_src.unlink(missing_ok=True)
        rendered += 1

    cfg_path.unlink(missing_ok=True)
    print(f"\n完成：渲染 {rendered} 个 mermaid 图 -> {IMAGES_DIR}")


if __name__ == "__main__":
    main()
