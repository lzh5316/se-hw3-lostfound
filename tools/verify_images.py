"""图片自检：核对尺寸，并用"像素探针"确认关键元素真的画在了预期位置。

为什么需要它：原型图是脚本生成的，脚本只会检查文字有没有溢出，
但"按钮画没画上、颜色对不对、图片有没有变成一片空白"必须靠像素来验证——
本脚本把每个页面的几个关键坐标取色，和期望颜色比对，任何一处不符就返回非 0。

用法（在 hw3 目录下）：
    python tools/verify_images.py

除了 prototype/screenshots 里的 9 张图与动图，本脚本还会读一遍博客 Markdown，
核对它引用的每张插图（含 07/08 两张过程截图）都确实躺在 blog/img/ 里、且不是空白图——
博客用的是相对路径 ``img/xxx.png``，仓库里少一张，贴上去就是一张破图。
"""

from __future__ import annotations

import os
import re
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError，
# 直接把自检结果打断；这里把不可表示的字符替换掉，保证脚本不会因输出编码失败。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

from PIL import Image, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "prototype", "screenshots")

# 博客正文与插图目录：正文里每个 ![..](img/xxx.png) 都要能在 blog/img/ 里找到
BLOG = os.path.join(ROOT, "blog", "校园失物招领小程序-第三次作业.md")
BLOG_IMG = os.path.join(ROOT, "blog", "img")
REF_RE = re.compile(r"!\[[^\]]*\]\((?:\./)?img/([^)\s]+)\)")
MIN_SIZE = (600, 400)   # 贴进博客后不至于看不清
MIN_STD = 6.0           # 灰度标准差下限，用来判"整张图是不是一片空白"

# 颜色（与 prototype/proto_common.py 的 COLORS 保持一致）
BLUE = "#2f6bff"
BLUE_SOFT = "#e8efff"
PAGE_BG = "#f2f4f8"
CARD = "#ffffff"
GREEN_SOFT = "#e7f8f0"
BOX_FILL = "#f7f9ff"

# (文件, 设计坐标 x, y, 期望颜色, 说明)
# 注意：探针要避开文字与图标，否则会取到白色文字或彩色图标
PROBES = [
    ("01_home_首页.png", 285, 682, BLUE, "「＋ 发布」悬浮按钮（避开文字）"),
    ("01_home_首页.png", 330, 250, CARD, "信息卡片空白处"),
    ("01_home_首页.png", 40, 90, PAGE_BG, "首页搜索框底色"),
    ("02_search_搜索.png", 100, 96, PAGE_BG, "搜索输入框底色"),
    ("02_search_搜索.png", 330, 230, CARD, "搜索结果卡片空白处"),
    ("03_detail_信息详情.png", 187, 100, BLUE_SOFT, "详情页物品图片区"),
    ("03_detail_信息详情.png", 210, 710, BLUE, "「联系发布者」按钮"),
    ("04_publish_发布信息.png", 100, 639, BLUE, "「发布」主按钮"),
    ("04_publish_发布信息.png", 187, 200, CARD, "表单卡片底色"),
    ("05_success_发布成功.png", 187, 165, GREEN_SOFT, "成功对勾圆底"),
    ("06_mine_我的发布.png", 187, 150, CARD, "我的发布卡片底色"),
    ("flow_view_查看信息流程图.png", 187, 64, BLUE_SOFT, "「开始」胶囊填充"),
    ("flow_view_查看信息流程图.png", 58, 160, BOX_FILL, "第一个处理框填充（留白处）"),
    ("flow_view_查看信息流程图.png", 187, 92, BLUE, "两个框之间的箭头"),
    ("flow_publish_发布信息流程图.png", 58, 160, BOX_FILL, "第一个处理框填充（留白处）"),
    ("flow_search_搜索流程图.png", 58, 160, BOX_FILL, "第一个处理框填充（留白处）"),
]

# 期望尺寸：设计坐标 × 2（SCALE=2）
EXPECT_SIZE = {
    "01_home_首页.png": (750, 1624),
    "02_search_搜索.png": (750, 1624),
    "03_detail_信息详情.png": (750, 1624),
    "04_publish_发布信息.png": (750, 1624),
    "05_success_发布成功.png": (750, 1624),
    "06_mine_我的发布.png": (750, 1624),
    "flow_view_查看信息流程图.png": (750, 1612),
    "flow_publish_发布信息流程图.png": (750, 1612),
    "flow_search_搜索流程图.png": (750, 1432),
}

# 动图单独校验：量化成 64 色调色板后颜色略有偏差，所以容差放宽
GIF_NAME = "09_流程演示.gif"
GIF_SIZE = (375, 868)
GIF_FRAMES = 7  # 1 张标题卡 + 6 个界面
DARK_BAR = "#1f2430"
# (帧号, x, y, 期望颜色, 说明)
GIF_PROBES = [
    (0, 30, 300, BLUE, "标题卡底色（避开文字）"),
    (0, 187, 700, BLUE, "标题卡下半部底色"),
    (1, 10, 860, DARK_BAR, "① 说明栏底色"),
    (1, 18, 845, BLUE, "① 序号胶囊"),
    (6, 150, 860, DARK_BAR, "⑥ 说明栏底色"),
    (6, 18, 845, BLUE, "⑥ 序号胶囊"),
]


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def near(a, b, tol=8) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def check_gif() -> int:
    """动图校验：帧数、尺寸，以及每类帧的关键取色。"""
    path = os.path.join(SHOTS, GIF_NAME)
    if not os.path.exists(path):
        print(f"FAIL 缺少动图：{GIF_NAME}（先运行 python prototype/demo_gif.py）")
        return 1
    failed = 0
    with Image.open(path) as gif:
        if gif.size != GIF_SIZE:
            print(f"FAIL {GIF_NAME} 尺寸 {gif.size}，期望 {GIF_SIZE}")
            failed += 1
        else:
            print(f"ok   {GIF_NAME} 尺寸 {gif.size[0]}x{gif.size[1]}")
        frames = getattr(gif, "n_frames", 1)
        if frames != GIF_FRAMES:
            print(f"FAIL {GIF_NAME} 共 {frames} 帧，期望 {GIF_FRAMES} 帧")
            failed += 1
        else:
            print(f"ok   {GIF_NAME} 共 {frames} 帧（1 张标题卡 + 6 个界面，循环播放）")
        for idx, x, y, want, desc in GIF_PROBES:
            gif.seek(idx)
            got = gif.convert("RGB").getpixel((x, y))
            if near(got, hex2rgb(want), tol=24):  # 调色板量化，容差放宽
                print(f"ok   {desc:<20} 第 {idx} 帧 ({x},{y}) = {got}")
            else:
                print(f"FAIL {desc:<20} 第 {idx} 帧 ({x},{y}) = {got}，期望 {hex2rgb(want)}")
                failed += 1
    return failed


def check_blog_images() -> int:
    """核对博客引用的每张插图：文件在不在、尺寸够不够、是不是空白图。"""
    if not os.path.exists(BLOG):
        print(f"FAIL 找不到博客正文：{os.path.relpath(BLOG, ROOT)}")
        return 1
    with open(BLOG, encoding="utf-8") as fh:
        md = fh.read()
    names: list[str] = []
    for name in REF_RE.findall(md):
        if name not in names:
            names.append(name)

    failed = 0
    for name in names:
        path = os.path.join(BLOG_IMG, name)
        if not os.path.exists(path):
            print(f"FAIL 博客引用了 img/{name}，但 blog/img/ 里没有这个文件（贴到博客会是破图）")
            failed += 1
            continue
        with Image.open(path) as im:
            size, fmt = im.size, im.format
            std = ImageStat.Stat(im.convert("L").resize((48, 48))).stddev[0]
        if size[0] < MIN_SIZE[0] or size[1] < MIN_SIZE[1]:
            if name.lower().endswith(".gif") and size[0] >= 300:
                print(f"ok   img/{name} {size[0]}x{size[1]} {fmt}（动图，按原尺寸贴出）")
                continue
            print(f"FAIL img/{name} 尺寸 {size} 小于 {MIN_SIZE}，贴进博客会看不清")
            failed += 1
        elif std < MIN_STD:
            print(f"FAIL img/{name} 灰度标准差 {std:.1f} < {MIN_STD}，像是一张空白图")
            failed += 1
        else:
            print(f"ok   img/{name} {size[0]}x{size[1]} {fmt}")
    print(f"（博客共引用 {len(names)} 张插图，其中 07/08 是两张过程截图）")
    return failed


def main() -> int:
    failed = 0
    for name, size in EXPECT_SIZE.items():
        path = os.path.join(SHOTS, name)
        if not os.path.exists(path):
            print(f"FAIL 缺少文件：{name}")
            failed += 1
            continue
        actual = Image.open(path).size
        if actual != size:
            print(f"FAIL {name} 尺寸 {actual}，期望 {size}")
            failed += 1
        else:
            print(f"ok   {name} 尺寸 {actual[0]}x{actual[1]}")

    print()
    for name, dx, dy, want, desc in PROBES:
        path = os.path.join(SHOTS, name)
        if not os.path.exists(path):
            failed += 1
            continue
        im = Image.open(path).convert("RGB")
        got = im.getpixel((dx * 2, dy * 2))
        if near(got, hex2rgb(want)):
            print(f"ok   {desc:<18} {name} ({dx},{dy}) = {got}")
        else:
            print(f"FAIL {desc:<18} {name} ({dx},{dy}) = {got}，期望 {hex2rgb(want)}")
            failed += 1

    print()
    failed += check_gif()

    print()
    failed += check_blog_images()

    print()
    if failed:
        print(f"自检未通过：{failed} 项异常")
    else:
        print(f"自检全部通过：{len(EXPECT_SIZE)} 张图片尺寸正确，{len(PROBES)} 个关键元素位置与颜色符合预期，"
              f"动图 {GIF_FRAMES} 帧校验通过，博客引用的插图齐全且无空白图")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
