"""统计博客正文字数，核对作业要求"字数在 800—1200 字左右"。

统计口径：中文/英文字符 + 数字，**排除**代码块、行内代码、图片、Markdown 表格与引用块说明，
因为作业看的是"正文写了多少内容"，表格和插图不计入正文本身。

用法（在 hw3 目录下）：
    python tools/count_words.py
"""

from __future__ import annotations

import os
import re
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError；兜底改成替换。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "blog", "校园失物招领小程序-第三次作业.md")

LOW, HIGH = 800, 1200

WORD = re.compile(r"[\u4e00-\u9fff]|[A-Za-z]+|\d+(?:\.\d+)?")


def body_lines(text: str) -> list[str]:
    """去掉代码块、表格、图片、引用块与标题行，只留正文段落。"""
    out: list[str] = []
    in_code = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line:
            continue
        if line.startswith("|") or line.startswith(">") or line.startswith("#"):
            continue
        if line.startswith("!["):
            continue
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"`[^`]*`", "", line)
        out.append(line)
    return out


def main() -> int:
    text = open(BLOG, encoding="utf-8").read()
    lines = body_lines(text)
    count = sum(len(WORD.findall(ln)) for ln in lines)
    print(f"博客正文：{count} 字（{len(lines)} 个正文段落）")
    print(f"要求区间：{LOW}—{HIGH} 字")
    if LOW <= count <= HIGH:
        print("字数检查通过。")
        return 0
    if count < LOW:
        print(f"字数偏少，建议再补 {LOW - count} 字以上（可以补充需求分析或结对过程中的具体细节）。")
    else:
        print(f"字数偏多，建议删减 {count - HIGH} 字左右（可以压缩表格说明或合并重复描述）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
