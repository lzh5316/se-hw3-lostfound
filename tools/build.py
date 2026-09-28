"""一键重建并分发本次作业的全部图片，同时打印校验结果。

用法（在 hw3 目录下）：
    python tools/build.py

做的事情：
    1. 运行 prototype/prototype.py  → 6 张原型图
    2. 运行 prototype/flowcharts.py → 3 张流程图
    3. 运行 prototype/demo_gif.py   → 1 张「三条基本流程综合演示」动图
    4. 把 prototype/screenshots 里的 PNG / GIF 复制到 blog/img/（博客插图用同一份文件）
    5. 运行 tools/process_shots.py  → 收录 07 制作原型过程截图、生成 08 画流程图过程截图
    6. 运行 tools/verify_images.py 做像素取色校验、核对博客引用的图是否都在，并统计博客正文字数
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError；兜底改成替换。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOTYPE = os.path.join(ROOT, "prototype")
SHOTS = os.path.join(PROTOTYPE, "screenshots")
BLOG_IMG = os.path.join(ROOT, "blog", "img")


def run(script: str, cwd: str) -> int:
    print(f"\n$ python {os.path.relpath(script, ROOT)}")
    proc = subprocess.run([sys.executable, script], cwd=cwd)
    if proc.returncode != 0:
        print(f"（{os.path.basename(script)} 返回 {proc.returncode}，请按上面的提示修正）")
    return proc.returncode


def copy_to_blog() -> int:
    os.makedirs(BLOG_IMG, exist_ok=True)
    count = 0
    for name in sorted(os.listdir(SHOTS)):
        if name.lower().endswith((".png", ".gif")) and not name.startswith("_"):
            shutil.copyfile(os.path.join(SHOTS, name), os.path.join(BLOG_IMG, name))
            count += 1
    print(f"\n已复制 {count} 张图片到 blog/img/")
    return count


def main() -> int:
    run(os.path.join(PROTOTYPE, "prototype.py"), PROTOTYPE)
    run(os.path.join(PROTOTYPE, "flowcharts.py"), PROTOTYPE)
    run(os.path.join(PROTOTYPE, "demo_gif.py"), PROTOTYPE)
    copy_to_blog()
    run(os.path.join(ROOT, "tools", "process_shots.py"), ROOT)   # 07 收录 + 08 生成
    codes = [
        run(os.path.join(ROOT, "tools", "verify_images.py"), ROOT),
        run(os.path.join(ROOT, "tools", "count_words.py"), ROOT),
    ]
    if any(codes):
        print("\n图片与文档已生成，但有自检项未通过，请查看上面的 FAIL 提示。")
        return 1
    print("\n全部完成：图片已生成并分发到 blog/img/，自检全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
