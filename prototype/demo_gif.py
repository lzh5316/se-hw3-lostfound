"""生成「三条基本流程综合演示」动图（GIF）。

把 6 张原型图按
    首页 → 信息详情 → 发布信息 → 发布成功 → 搜索物品 → 我的发布
的顺序串成一个循环播放的动图，每帧底部配一句说明，
用来对应作业要求「演示三条基本流程」。

为什么单独写一个脚本（而不是复用 proto_common 的 SCALE=2）：
GIF 每帧都要存一张图，体积对帧数很敏感，所以这里按 1 倍设计尺寸
（375×868）绘制，并在保存前把每帧量化成 64 色调色板——同样的内容，
体积能压到 2 倍图的 1/4 左右，方便直接上传到博客园。

用法（在 hw3 目录下）：
    python prototype/demo_gif.py     # 也可以直接跑 python tools/build.py，它会自动调用
输出：prototype/screenshots/09_流程演示.gif（tools/build.py 会复制到 blog/img/）
"""

from __future__ import annotations

import os
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError；兜底改成替换。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots")
OUT = os.path.join(SHOTS, "09_流程演示.gif")

W, H, CAP = 375, 812, 56          # 屏宽、屏高、底部说明栏高
FRAME = (W, H + CAP)
DURATION = 1400                   # 每帧停留毫秒数

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "msyh.ttc")
FONT_BOLD = os.path.join(FONT_DIR, "msyhbd.ttc")

PRIMARY = "#2f6bff"
DARK = "#1f2430"
LINE = "#e6e9f0"

# (原型图文件名, 底部说明, 步骤序号)  —— 与博客「五、用户使用流程」的顺序一致
STEPS = [
    ("01_home_首页.png", "① 首页：浏览最新的寻物 / 招领信息", "1"),
    ("03_detail_信息详情.png", "② 点卡片进详情页，可「联系发布者」", "2"),
    ("04_publish_发布信息.png", "③ 点「＋ 发布」：选类型、填物品信息", "3"),
    ("05_success_发布成功.png", "④ 点「发 布」：进入发布成功页", "4"),
    ("02_search_搜索.png", "⑤ 搜索「校园卡」：查看搜索结果", "5"),
    ("06_mine_我的发布.png", "⑥ 「我的发布」：修改 / 标记状态", "6"),
]

_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_REGULAR
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def wrap(d: ImageDraw.ImageDraw, s: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """按字符折行；任何一行超宽都抛错——和 proto_common.fit 一样用于自检排版溢出。"""
    lines: list[str] = []
    cur = ""
    for ch in s:
        cand = cur + ch
        if d.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    for ln in lines:
        w = d.textlength(ln, font=font)
        if w > max_w + 0.5:
            raise ValueError(f"文本溢出：{ln!r} 宽 {w:.1f} > {max_w}")
    return lines


def caption_frame(path: str, note: str, step: str) -> Image.Image:
    """一帧：上面是原型图，下面是深色说明栏（序号 + 说明文字）。"""
    src = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    canvas = Image.new("RGB", FRAME, "#ffffff")
    canvas.paste(src, (0, 0))

    d = ImageDraw.Draw(canvas)
    d.rectangle([0, H, W, H + CAP], fill=DARK)
    d.rectangle([0, H, W, H + 1], fill=LINE)

    # 序号胶囊
    d.rounded_rectangle([14, H + 17, 14 + 22, H + 17 + 22], radius=11, fill=PRIMARY)
    d.text((14 + 11, H + 17 + 11), step, font=fnt(13, True), fill="#ffffff", anchor="mm")

    # 说明文字（最多两行，垂直居中）
    f = fnt(14, True)
    lines = wrap(d, note, f, W - 52 - 14)
    step_h = 20
    y0 = H + (CAP - len(lines) * step_h) / 2 + 1
    for i, ln in enumerate(lines):
        d.text((52, y0 + i * step_h), ln, font=f, fill="#ffffff")
    return canvas


def title_frame() -> Image.Image:
    """首帧：标题卡，说明这张动图演示哪三条流程。"""
    canvas = Image.new("RGB", FRAME, PRIMARY)
    d = ImageDraw.Draw(canvas)

    f_big = fnt(24, True)
    for i, ln in enumerate(wrap(d, "三条基本流程综合演示", f_big, W - 60)):
        d.text((W / 2, 300 + i * 36), ln, font=f_big, fill="#ffffff", anchor="mm")

    d.text((W / 2, 366), "校园失物招领小程序 · 可点击原型", font=fnt(13), fill="#dbe4ff", anchor="mm")
    d.line([60, 396, W - 60, 396], fill="#6f9bff", width=1)

    f = fnt(14, True)
    for i, line in enumerate([
        "查看信息 → 查看详情",
        "发布信息 → 发布成功",
        "搜索物品 → 查看搜索结果",
    ]):
        y = 430 + i * 30
        d.rounded_rectangle([74, y - 4, 88, y + 10], radius=7, fill="#ffffff")
        d.text((81, y + 3), str(i + 1), font=fnt(10, True), fill=PRIMARY, anchor="mm")
        d.text((104, y + 3), line, font=f, fill="#ffffff", anchor="lm")

    d.text((W / 2, H + CAP - 34), "自动循环播放 · 每帧 1.4 秒", font=fnt(12), fill="#c9d6ff", anchor="mm")
    return canvas


def main() -> int:
    frames = [title_frame()]
    for name, note, step in STEPS:
        path = os.path.join(SHOTS, name)
        if not os.path.exists(path):
            print(f"FAIL 缺少原型图：{name}（先运行 python prototype/prototype.py）")
            return 1
        frames.append(caption_frame(path, note, step))

    # 量化成 64 色调色板后再存 GIF，体积更小
    paletted = [f.convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
    paletted[0].save(
        OUT,
        save_all=True,
        append_images=paletted[1:],
        duration=DURATION,
        loop=0,
        optimize=True,
        disposal=2,
    )

    size_kb = os.path.getsize(OUT) / 1024
    print(f"saved {OUT} {FRAME[0]}x{FRAME[1]} 共 {len(paletted)} 帧（{size_kb:.0f} KB，循环播放）")
    if size_kb > 2048:
        print("提示：动图超过 2 MB，博客上传可能变慢，可以减小 DURATION 帧数或调低 colors。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
