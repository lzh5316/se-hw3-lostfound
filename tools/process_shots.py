#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""准备「过程截图」：作业要求第 11 条要的两张过程证据。

要求里写的是"可以提供讨论需求、画流程图、制作原型时的照片或截图"，本脚本管这两张：

* ``07_制作原型_过程截图.jpg`` —— **收录**你在原型工具里截的图。
  原图一般是 PNG（放在仓库的 ``截图/`` 目录），而博客里按 ``.jpg`` 引用，
  所以这里统一转成白底 JPEG 再放进 ``blog/img/``，原图保留不动。
* ``08_画流程图_过程截图.jpg`` —— **生成**一张"流程图画布草稿"示意图。
  本仓库的 3 张流程图是 ``prototype/flowcharts.py`` 用同一套配色渲染出来的，
  这张示意图把"在画布上摆节点 → 连箭头 → 补「否」分支"的过程画下来，配色与流程图一致。
  说明白一点：它由脚本绘制，**不是真实软件截屏**；若老师要求真实截屏，
  用 draw.io / ProcessOn / 墨刀 照下面的节点文案画 3 个框截一张替换即可。

用法（在 hw3 目录下）：

    python tools/process_shots.py                 # 08 生成 + 07 收录（默认）
    python tools/process_shots.py --only 08       # 只生成 08
    python tools/process_shots.py --only 07       # 只收录 07
    python tools/process_shots.py --out 目录      # 改输出目录（默认 blog/img）
    python tools/process_shots.py --from-07 路径  # 指定 07 的原图路径
"""

from __future__ import annotations

import argparse
import math
import os
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError；兜底改成替换。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "prototype"))

from proto_common import COLORS, FONT_BOLD, FONT_REGULAR  # noqa: E402  （配色与本仓库原型、流程图一致）

NAME_07 = "07_制作原型_过程截图.jpg"
NAME_08 = "08_画流程图_过程截图.jpg"
DEFAULT_07_SRC = os.path.join(ROOT, "截图", "07_制作原型_过程截图.png")
BLOG_IMG = os.path.join(ROOT, "blog", "img")

# ---------------------------------------------------------------- 画布尺寸与配色

W, H = 1440, 900                                      # 截图尺寸
WIN_X0, WIN_Y0, WIN_X1, WIN_Y1 = 40, 40, 1400, 860   # 软件窗口
TITLE_Y1 = 82                                         # 标题栏底部
TOOLBAR_Y1 = 122                                      # 工具条底部
STATUS_Y0 = 826                                       # 状态栏顶部
LEFT_X1 = 240                                         # 左面板右边界
CANVAS_X0 = LEFT_X1
CANVAS_X1 = 1170                                      # 画布右边界（= 右面板左边界）
CX = (CANVAS_X0 + CANVAS_X1) / 2                      # 画布中轴（节点居中于此）
NODE_W, NODE_H = 210, 52                              # 流程节点尺寸

DESKTOP = "#e7ebf4"
WIN = "#ffffff"
PANEL = "#fafbfd"
FIELD = "#f1f3f8"
BORDER = "#e3e7f0"
GRID_DOT = "#dfe4ee"
GUIDE = "#c7d3ff"
TXT = COLORS["text"]
SUB = COLORS["sub"]
PRIMARY = COLORS["primary"]
SOFT = COLORS["primary_soft"]
LOST = COLORS["lost"]
LOST_SOFT = COLORS["lost_soft"]
FOUND = COLORS["found"]

# ---------------------------------------------------------------- 文本工具

_fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)
    return _fonts[key]


def tw(d: ImageDraw.ImageDraw, s: str, f_: ImageFont.FreeTypeFont) -> float:
    return d.textlength(s, font=f_)


def clip(d, s: str, f_, max_w: float) -> str:
    """超宽就截断加省略号（面板较窄时用，避免文字压到隔壁栏）。"""
    if tw(d, s, f_) <= max_w:
        return s
    while s and tw(d, s + "…", f_) > max_w:
        s = s[:-1]
    return s + "…"


def put(d, xy, s, size=13, bold=False, fill=None, anchor="la", max_w=None):
    """写字；给了 ``max_w`` 会自动截断。返回文本宽度。"""
    f_ = font(size, bold)
    if max_w is not None:
        s = clip(d, s, f_, max_w)
    d.text(xy, s, font=f_, fill=fill or TXT, anchor=anchor)
    return tw(d, s, f_)


def wrap(d, s, size, max_w, bold=False) -> list[str]:
    """按字符折行（中文逐字断行即可），返回行列表。"""
    f_ = font(size, bold)
    lines: list[str] = []
    cur = ""
    for ch in s:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if not cur or tw(d, cur + ch, f_) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, s, size=12, max_w=190, line_h=None, bold=False, fill=None) -> float:
    """画一段折行文字，返回底部 y。"""
    lines = wrap(d, s, size, max_w, bold)
    line_h = line_h or size + 5
    for i, ln in enumerate(lines):
        put(d, (x, y + i * line_h), ln, size, bold=bold, fill=fill)
    return y + len(lines) * line_h


def center_block(d, cx, cy, s, size=13, max_w=170, max_lines=2, bold=False, fill=None):
    """在 (cx, cy) 居中画一段文字（行数超了就整体缩小字号，保证不出框）。"""
    lines = wrap(d, s, size, max_w, bold)
    while len(lines) > max_lines and size > 10:
        size -= 1
        lines = wrap(d, s, size, max_w, bold)
    lines = lines[:max_lines]
    line_h = size + 4
    y0 = cy - (len(lines) * line_h) / 2 + 2
    for i, ln in enumerate(lines):
        put(d, (cx, y0 + i * line_h), ln, size, bold=bold, fill=fill, anchor="lm")


# ---------------------------------------------------------------- 图形工具


def rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


def line(d, x0, y0, x1, y1, fill, width=1):
    d.line([x0, y0, x1, y1], fill=fill, width=width)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(list(box), radius=r, fill=fill, outline=outline, width=width)


def dashed(d, p0, p1, fill, width=1, dash=6, gap=4):
    """虚线（Pillow 没有现成的，按长度切段自己画）。"""
    (x0, y0), (x1, y1) = p0, p1
    total = math.hypot(x1 - x0, y1 - y0)
    if total == 0:
        return
    ux, uy = (x1 - x0) / total, (y1 - y0) / total
    pos = 0.0
    while pos < total:
        end = min(pos + dash, total)
        line(d, x0 + ux * pos, y0 + uy * pos, x0 + ux * end, y0 + uy * end, fill, width)
        pos = end + gap


def dashed_rect(d, box, fill, width=2, dash=7, gap=5):
    x0, y0, x1, y1 = box
    dashed(d, (x0, y0), (x1, y0), fill, width, dash, gap)
    dashed(d, (x1, y0), (x1, y1), fill, width, dash, gap)
    dashed(d, (x1, y1), (x0, y1), fill, width, dash, gap)
    dashed(d, (x0, y1), (x0, y0), fill, width, dash, gap)


def arrow_v(d, cx, y0, y1, color=PRIMARY, width=2, head=7):
    line(d, cx, y0, cx, y1 - head, color, width)
    d.polygon([(cx - head, y1 - head), (cx + head, y1 - head), (cx, y1)], fill=color)


def arrow_h(d, x0, x1, y, color=PRIMARY, width=2, head=7):
    sgn = 1 if x1 >= x0 else -1
    line(d, x0, y, x1 - sgn * head, y, color, width)
    d.polygon([(x1 - sgn * head, y - head), (x1 - sgn * head, y + head), (x1, y)], fill=color)


def handle_square(d, x, y, s=7, color=PRIMARY):
    d.rectangle([x - s // 2, y - s // 2, x + s // 2, y + s // 2], fill=WIN, outline=color)


def selection(d, box, color=PRIMARY):
    """选中态：虚线外框 + 8 个控制点。"""
    x0, y0, x1, y1 = box
    dashed_rect(d, box, color, width=1, dash=5, gap=4)
    for x in (x0, (x0 + x1) / 2, x1):
        for y in (y0, (y0 + y1) / 2, y1):
            if x in (x0, x1) or y in (y0, y1):
                handle_square(d, x, y)


def pill(d, x, y, w, h, label, primary=False, size=12):
    rrect(d, (x, y, x + w, y + h), h / 2 if primary else 5,
          fill=PRIMARY if primary else FIELD,
          outline=None if primary else BORDER)
    put(d, (x + w / 2, y + h / 2 + 1), label, size, bold=primary,
        fill=WIN if primary else TXT, anchor="mm")


def chip(d, x, y, label, size=12, active=False, h=24):
    f_ = font(size, active)
    w = tw(d, label, f_) + 24
    rrect(d, (x, y, x + w, y + h), 6,
          fill=SOFT if active else FIELD,
          outline=PRIMARY if active else BORDER)
    put(d, (x + w / 2, y + h / 2 + 1), label, size, bold=active,
        fill=PRIMARY if active else TXT, anchor="mm")
    return w


def checkbox(d, x, y, checked=True, size=13):
    rrect(d, (x, y, x + size, y + size), 3,
          fill=PRIMARY if checked else WIN,
          outline=PRIMARY if checked else "#c8cfdd")
    if checked:
        line(d, x + 3, y + size * 0.55, x + size * 0.45, y + size - 3, WIN, 2)
        line(d, x + size * 0.45, y + size - 3, x + size - 3, y + 3, WIN, 2)
    return size


def dot_grid(d, box, step=24, color=GRID_DOT):
    x0, y0, x1, y1 = box
    x = x0 + step / 2
    while x < x1:
        y = y0 + step / 2
        while y < y1:
            d.rectangle([x, y, x + 1, y + 1], fill=color)
            y += step
        x += step


def cursor_arrow(d, x, y, color=TXT):
    pts = [(0, 0), (0, 17), (4.4, 13), (7.4, 19.6), (10.2, 18.2), (7.2, 11.8), (13, 11.4)]
    d.polygon([(x + a, y + b) for a, b in pts], fill=color, outline=WIN)


def magnifier(d, x, y, color=SUB, r=5):
    d.ellipse([x, y, x + r * 2, y + r * 2], outline=color, width=2)
    line(d, x + r * 2 - 1, y + r * 2 - 1, x + r * 2 + 4, y + r * 2 + 4, color, 2)


# ---------------------------------------------------------------- 窗口各区域


def window(d):
    d.rectangle([WIN_X0 + 7, WIN_Y0 + 9, WIN_X1 + 7, WIN_Y1 + 9], fill="#d3dae9")
    d.rectangle([WIN_X0, WIN_Y0, WIN_X1, WIN_Y1], fill=WIN, outline="#cbd3e2")


def titlebar(d):
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        x = 64 + i * 20
        d.ellipse([x - 6, 55, x + 6, 67], fill=c)
    put(d, (124, 62), "校园失物招领 · 画流程图（3 条主流程草稿）", 15, bold=True, anchor="lm")
    d.ellipse([1158, 57, 1166, 65], fill=COLORS["ok"])
    put(d, (1154, 62), "草稿已自动保存 20:22", 12, fill=SUB, anchor="rm")
    pill(d, 1246, 50, 60, 22, "分享", primary=True)
    pill(d, 1314, 50, 76, 22, "导出 PNG")


def toolbar(d):
    d.rectangle([WIN_X0, TITLE_Y1, WIN_X1, TOOLBAR_Y1], fill="#fbfcfe")
    line(d, WIN_X0, TOOLBAR_Y1, WIN_X1, TOOLBAR_Y1, BORDER)
    x = 56
    for label in ("选择", "连线", "文字", "便签", "图片", "备注"):
        x += chip(d, x, 89, label, active=(label == "连线")) + 8
    line(d, x + 4, 93, x + 4, 111, BORDER)
    x += 18
    checkbox(d, x, 94)
    put(d, (x + 20, 101), "网格吸附", 12, anchor="lm")
    x += 20 + 62
    checkbox(d, x, 94)
    put(d, (x + 20, 101), "对齐参考线", 12, anchor="lm")
    pill(d, 1288, 89, 26, 24, "−")
    put(d, (1336, 102), "100%", 12, fill=SUB, anchor="lm")
    pill(d, 1366, 89, 26, 24, "+")


def left_panel(d):
    d.rectangle([WIN_X0, TOOLBAR_Y1, LEFT_X1, STATUS_Y0], fill=PANEL)
    line(d, LEFT_X1, TOOLBAR_Y1, LEFT_X1, STATUS_Y0, BORDER)

    # 搜索框
    rrect(d, (52, 134, 228, 162), 6, fill=FIELD)
    magnifier(d, 64, 142)
    put(d, (84, 149), "搜索图形 / 组件", 12, fill=SUB, anchor="lm", max_w=132)

    put(d, (56, 176), "图形", 12, bold=True, fill=SUB)
    shapes = ("开始 / 结束（圆角）", "处理（矩形）", "判断（菱形）", "连线 / 箭头", "便签 / 备注")
    for i, label in enumerate(shapes):
        y = 194 + i * 34
        if i == 2:  # 菱形：当前正在补的分支
            rrect(d, (48, y - 4, 232, y + 30), 6, fill=SOFT)
        if i in (0, 1):
            rrect(d, (58, y, 78, y + 16), 8 if i == 0 else 2, outline=PRIMARY, width=2)
        elif i == 2:
            d.polygon([(58, y + 8), (68, y), (78, y + 8), (68, y + 16)], outline=LOST, width=2)
        elif i == 3:
            arrow_h(d, 58, 78, y + 8)
        else:
            rrect(d, (58, y, 78, y + 16), 2, fill="#ffe9a8", outline="#e8c860", width=2)
        put(d, (88, y + 8), label, 12.5, anchor="lm", max_w=140,
            bold=(i == 2), fill=PRIMARY if i == 2 else TXT)

    put(d, (56, 372), "页面", 12, bold=True, fill=SUB)
    pages = (("查看信息流程", "09-25"), ("发布信息流程", "编辑中"), ("搜索物品流程", "09-25"))
    for i, (name, tag) in enumerate(pages):
        y = 390 + i * 32
        if i == 1:
            rrect(d, (48, y, 232, y + 28), 6, fill=SOFT)
        put(d, (58, y + 14), name, 12.5, bold=(i == 1), anchor="lm",
            fill=PRIMARY if i == 1 else TXT)
        put(d, (222, y + 14), tag, 11, anchor="rm",
            fill=PRIMARY if i == 1 else SUB)

    put(d, (56, 496), "草稿备注", 12, bold=True, fill=SUB)
    rrect(d, (52, 514, 228, 610), 8, fill="#fffdf4", outline="#f0e3b8")
    block(d, 64, 526, "待补分支：搜索无结果 → 提示「换个关键词试试」，与原型 02 页一致。",
          12, max_w=152, line_h=18)

    put(d, (56, 632), "自查清单", 12, bold=True, fill=SUB)
    todos = ("每张图都有开始与结束", "箭头单向、不交叉", "与 6 个原型页一一对应",
             "寻物橙 / 招领绿的配色", "分支都标了「是 / 否」")
    for i, t in enumerate(todos):
        y = 650 + i * 22
        line(d, 58, y + 5, 63, y + 10, FOUND, 2)
        line(d, 63, y + 10, 71, y + 1, FOUND, 2)
        put(d, (78, y), t, 12)


def canvas(d):
    d.rectangle([CANVAS_X0, TOOLBAR_Y1, CANVAS_X1, STATUS_Y0], fill="#fcfdff")
    dot_grid(d, (CANVAS_X0, TOOLBAR_Y1, CANVAS_X1, STATUS_Y0))
    # 对齐参考线（正在编辑时软件会显示的那种虚线）
    dashed(d, (CX, 134), (CX, 600), GUIDE, 1, 6, 6)
    dashed(d, (252, 430), (898, 430), GUIDE, 1, 6, 6)
    put(d, (256, 136), "画布 · 发布信息（主流程 2 / 3）", 12, fill=SUB)

    # ① 开始
    rrect(d, (CX - NODE_W / 2, 150, CX + NODE_W / 2, 202), NODE_H / 2,
          fill=SOFT, outline=PRIMARY, width=2)
    center_block(d, CX, 176, "开始：打开小程序首页", 13, max_w=NODE_W - 28)
    arrow_v(d, CX, 202, 224)

    # ② 进入发布页
    rrect(d, (CX - NODE_W / 2, 224, CX + NODE_W / 2, 276), 10, fill=WIN, outline="#d7ddea", width=2)
    center_block(d, CX, 250, "点首页「＋ 发布」→ 选「寻物 / 招领」", 13, max_w=NODE_W - 28)
    arrow_v(d, CX, 276, 298)

    # ③ 填表单
    rrect(d, (CX - NODE_W / 2, 298, CX + NODE_W / 2, 350), 10, fill=WIN, outline="#d7ddea", width=2)
    center_block(d, CX, 324, "填写：物品名称、类型、地点、时间", 13, max_w=NODE_W - 28)
    arrow_v(d, CX, 350, 378)

    # ④ 判断（选中态）
    d.polygon([(CX - 128, 430), (CX, 378), (CX + 128, 430), (CX, 482)],
              fill=LOST_SOFT, outline=LOST, width=2)
    center_block(d, CX, 428, "必填项都填了吗？", 13.5, max_w=150, bold=True, fill="#a8680a")
    selection(d, (CX - 140, 366, CX + 140, 494))

    # ⑤「是」分支
    arrow_v(d, CX, 482, 512, FOUND)
    put(d, (CX + 18, 502), "是", 12, bold=True, fill=FOUND, anchor="lm")
    rrect(d, (CX - NODE_W / 2, 512, CX + NODE_W / 2, 564), 10, fill=WIN, outline="#d7ddea", width=2)
    center_block(d, CX, 538, "上传照片、填联系方式（选填）", 13, max_w=NODE_W - 28)

    # ⑥ 正在连到刚放下的节点（橡皮筋 + 吸附预览）
    d.ellipse([CX - 4, 560, CX + 4, 568], fill=PRIMARY)
    dashed(d, (CX, 564), (880, 612), PRIMARY, 2, 8, 5)
    d.ellipse([874, 606, 886, 618], outline=PRIMARY, width=2)
    dashed_rect(d, (880, 586, 1090, 638), LOST, 2, 7, 5)
    d.rounded_rectangle([880, 586, 1090, 638], radius=10, fill=rgba(LOST_SOFT, 140))
    center_block(d, 985, 612, "点「发 布」→ 发布成功页", 13, max_w=180, fill="#a8680a")
    put(d, (985, 654), "刚放下 · 待连线", 11, fill=SUB, anchor="mm")
    d.rounded_rectangle([880, 522, 1108, 578], radius=8, fill="#1f2430")
    put(d, (896, 540), "连接中：处理 → 处理", 12, fill=WIN, anchor="lm")
    put(d, (896, 562), "松开自动吸附到最近节点", 12, fill="#c8cfdd", anchor="lm")
    cursor_arrow(d, 884, 620)

    # ⑦「否」分支
    arrow_h(d, CX + 128, 900, 430, LOST)
    put(d, (CX + 132, 412), "否", 12, bold=True, fill=LOST, anchor="lm")
    rrect(d, (900, 388, 1150, 460), 10, fill=LOST_SOFT, outline=LOST, width=2)
    block(d, 916, 400, "按钮置灰 + 字段旁红字提示，点「发 布」不跳转（与原型 04 页一致）。",
          12, max_w=218, line_h=17, fill="#a8680a")


def right_panel(d):
    d.rectangle([CANVAS_X1, TOOLBAR_Y1, WIN_X1, STATUS_Y0], fill=PANEL)
    line(d, CANVAS_X1, TOOLBAR_Y1, CANVAS_X1, STATUS_Y0, BORDER)

    put(d, (1188, 134), "属性", 12, bold=True, fill=SUB)
    rows = (("类型", "判断（菱形）", None), ("填充", "#FFF4E5", LOST_SOFT),
            ("描边", "#F79009 · 2 px", LOST), ("圆角", "10 px", None),
            ("文字", "14 px · 居中", None))
    for i, (label, value, swatch) in enumerate(rows):
        y = 162 + i * 28
        put(d, (1188, y), label, 12.5, fill=SUB, anchor="lm")
        w = tw(d, value, font(12.5))
        if swatch:
            d.rectangle([1382 - w - 20, y - 6, 1382 - w - 8, y + 6], fill=swatch, outline=BORDER)
        put(d, (1382, y), value, 12.5, anchor="rm")
    line(d, 1180, 300, 1390, 300, BORDER)

    put(d, (1188, 316), "操作历史", 12, bold=True, fill=SUB)
    history = (("20:05", "新建画布，放入「开始 / 结束」胶囊"),
               ("20:12", "连接「进入首页 → 选择信息」处理框"),
               ("20:18", "连上「是」分支：填写 → 上传照片 → 发布"),
               ("20:22", "补「否 · 必填校验」分支（本次）"))
    for i, (t, txt) in enumerate(history):
        y = 336 + i * 54
        put(d, (1188, y), t, 12, bold=True, fill=SUB)
        block(d, 1188, y + 16, txt, 12.5, max_w=194, line_h=17)
    line(d, 1180, 564, 1390, 564, BORDER)

    put(d, (1188, 580), "说明", 12, bold=True, fill=SUB)
    block(d, 1188, 600, "3 张流程图与原型里的 6 个页面一一对应，画完再逐条走查主流程；"
                       "「否」这类分支也要有明确出口。", 12.5, max_w=194, line_h=17)

    rrect(d, (1180, 690, 1390, 790), 8, fill="#f2f6ff", outline=SOFT)
    put(d, (1196, 706), "截图建议", 12, bold=True, fill=PRIMARY)
    block(d, 1196, 726, "把画布缩放到 100% 再截，节点与箭头都看得清；"
                       "让左侧页面清单一起入镜。", 12, max_w=178, line_h=17, fill=SUB)


def statusbar(d):
    d.rectangle([WIN_X0, STATUS_Y0, WIN_X1, WIN_Y1], fill="#f7f8fc")
    line(d, WIN_X0, STATUS_Y0, WIN_X1, STATUS_Y0, BORDER)
    put(d, (56, 843), "缩放 100% · 网格吸附：开 · 对齐参考线：开", 12, fill=SUB, anchor="lm")
    put(d, (1384, 843), "草稿 v3 · 共 3 条主流程（与 6 个原型页一致）", 12, fill=SUB, anchor="rm")


def draw_flow_shot() -> Image.Image:
    im = Image.new("RGB", (W, H), DESKTOP)
    d = ImageDraw.Draw(im, "RGBA")
    window(d)
    titlebar(d)
    toolbar(d)
    left_panel(d)
    canvas(d)
    right_panel(d)
    statusbar(d)
    return im


# ---------------------------------------------------------------- 07：收录原型过程截图


def to_white_rgb(im: Image.Image) -> Image.Image:
    """透明底 / 调色板图片统一贴到白底上，免得转成 JPEG 后变黑。"""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def collect_07(src: str, out_dir: str) -> int:
    dst = os.path.join(out_dir, NAME_07)
    if not os.path.exists(src):
        if os.path.exists(dst):
            print(f"ok   {NAME_07} 已存在（原图 {os.path.relpath(src, ROOT)} 不在，保留现有文件）")
            return 0
        print(f"跳过 07：找不到原图 {os.path.relpath(src, ROOT)}")
        print("     把原型工具的过程截图存成这个路径，或用 --from-07 <路径> 指定；")
        print(f"     本次不放过程截图的话，把博客「七」里的 ![..](img/{NAME_07}) 一行删掉即可。")
        return 0
    im = to_white_rgb(Image.open(src))
    if im.size[0] > 1600:                     # 太宽的截屏压一下，控制博客图片体积
        im = im.resize((1600, round(im.size[1] * 1600 / im.size[0])), Image.LANCZOS)
    im.save(dst, "JPEG", quality=88, optimize=True)
    print(f"ok   {NAME_07} ← {os.path.relpath(src, ROOT)}  {im.size[0]}x{im.size[1]}  "
          f"{os.path.getsize(dst) // 1024} KB")
    return 0


def generate_08(out_dir: str) -> int:
    dst = os.path.join(out_dir, NAME_08)
    im = draw_flow_shot()
    im.save(dst, "JPEG", quality=90, optimize=True)
    print(f"ok   {NAME_08}  {im.size[0]}x{im.size[1]}  {os.path.getsize(dst) // 1024} KB"
          "  （脚本绘制的画布示意图，非真实截屏）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="准备过程截图（作业要求第 11 条）")
    ap.add_argument("--only", choices=("07", "08", "both"), default="both",
                    help="只处理其中一张，默认两张都处理")
    ap.add_argument("--out", default=BLOG_IMG, help="输出目录，默认 blog/img")
    ap.add_argument("--from-07", default=DEFAULT_07_SRC, help="07 的原图路径")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"输出目录：{os.path.relpath(args.out, ROOT)}")
    if args.only in ("07", "both"):
        collect_07(args.from_07, args.out)
    if args.only in ("08", "both"):
        generate_08(args.out)
    print("过程截图准备完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
