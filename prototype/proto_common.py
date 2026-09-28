"""原型图 / 流程图的公共绘制工具。

作业要求原型要用墨刀、Figma 等工具制作，这里先用 Pillow 把原型**画成图片**：
好处是不依赖网络与设计工具账号，生成的 PNG 可以直接上传到博客，
也可以照着这份尺寸稿在墨刀/Figma 里快速复刻（见 docs 与 README）。

约定：
  * 所有几何尺寸都用\"设计坐标\"（小程序常见设计宽度 375pt）书写；
  * 输出图片按 ``SCALE`` 倍放大，保证贴到博客里清晰；
  * 文本一律通过 :func:`fit` 折行，并在超出预设宽度时直接报错，
    这样脚本自己就能检验\"排版有没有溢出\"。
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- 基础设置

SCALE = 2  # 设计坐标 → 输出像素的倍率

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "msyh.ttc")     # 微软雅黑
FONT_BOLD = os.path.join(FONT_DIR, "msyhbd.ttc")      # 微软雅黑 Bold

COLORS = {
    "bg": "#f2f4f8",
    "card": "#ffffff",
    "primary": "#2f6bff",
    "primary_soft": "#e8efff",
    "primary_dark": "#1f4fd8",
    "text": "#1f2430",
    "sub": "#8a90a0",
    "line": "#e6e9f0",
    "found": "#17b26a",        # 招领
    "found_soft": "#e7f8f0",
    "lost": "#f79009",         # 寻物
    "lost_soft": "#fff4e5",
    "ok": "#12b76a",
    "shadow": "#dfe3ec",
}

_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def px(value: float) -> int:
    """设计坐标 → 输出像素。"""
    return int(round(value * SCALE))


def fnt(size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (int(size * SCALE), bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_REGULAR
        if not os.path.exists(path):  # 非 Windows 环境回退
            path = FONT_REGULAR if os.path.exists(FONT_REGULAR) else path
        _font_cache[key] = ImageFont.truetype(path, key[0])
    return _font_cache[key]


def new_screen(width: float = 375, height: float = 812, color: str | None = None):
    """新建一张空白屏，返回 ``(image, draw)``（设计坐标 375×812）。"""
    im = Image.new("RGB", (px(width), px(height)), color or COLORS["bg"])
    return im, ImageDraw.Draw(im)


# ---------------------------------------------------------------- 绘制元件


def rrect(d: ImageDraw.ImageDraw, x, y, w, h, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(
        [px(x), px(y), px(x + w), px(y + h)],
        radius=px(r),
        fill=fill,
        outline=outline,
        width=px(width) if outline else 0,
    )


def rect(d: ImageDraw.ImageDraw, x, y, w, h, fill=None, outline=None, width=1):
    d.rectangle(
        [px(x), px(y), px(x + w), px(y + h)],
        fill=fill,
        outline=outline,
        width=px(width) if outline else 0,
    )


def line(d: ImageDraw.ImageDraw, x0, y0, x1, y1, fill, width=1):
    d.line([px(x0), px(y0), px(x1), px(y1)], fill=fill, width=px(width))


def text(d: ImageDraw.ImageDraw, x, y, s, size=13, bold=False, fill=None, anchor="la"):
    d.text((px(x), px(y)), s, font=fnt(size, bold), fill=fill or COLORS["text"], anchor=anchor)


def text_w(d: ImageDraw.ImageDraw, s, size=13, bold=False) -> float:
    """文本宽度（设计坐标）。"""
    return d.textlength(s, font=fnt(size, bold)) / SCALE


def fit(d, s, size, max_w, bold=False, ctx="") -> list[str]:
    """把 ``s`` 折行到不超过 ``max_w``（设计坐标），返回行列表。

    任何一行超宽都会抛 ``ValueError`` —— 脚本用这个约定自检排版。
    """
    lines: list[str] = []
    cur = ""
    for ch in s:
        cand = cur + ch
        if text_w(d, cand, size, bold) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    for ln in lines:
        w = text_w(d, ln, size, bold)
        if w > max_w + 0.5:
            raise ValueError(f"文本溢出（{ctx}）：{ln!r} 宽 {w:.1f} > {max_w:.1f}")
    return lines


def fit_draw(d, x, y, s, size, max_w, bold=False, fill=None, spacing=3, ctx="") -> float:
    """折行并绘制，返回文本块高度（设计坐标）。"""
    lines = fit(d, s, size, max_w, bold, ctx)
    step = size + spacing
    for i, ln in enumerate(lines):
        text(d, x, y + i * step, ln, size=size, bold=bold, fill=fill)
    return len(lines) * step


def center_text(d, x, y, w, s, size=13, bold=False, fill=None, ctx=""):
    """在宽度 ``w`` 的框里水平居中绘制单行文本（x、w 均为设计坐标）。"""
    fit(d, s, size, w, bold, ctx or s)
    d.text(
        (px(x + w / 2), px(y)),          # 取"框的中心"（设计坐标 → 像素）
        s,
        font=fnt(size, bold),
        fill=fill or COLORS["text"],
        anchor="ma",
    )


def tag(d, x, y, s, fg, bg, size=10, pad=6, h=17):
    """小胶囊标签，返回其宽度。"""
    w = text_w(d, s, size) + pad * 2
    rrect(d, x, y, w, h, h / 2, fill=bg)
    center_text(d, x, y + (h - size) / 2 - 1.5, w, s, size=size, fill=fg, ctx="标签")
    return w


def button(d, x, y, w, h, s, size=15, kind="primary"):
    if kind == "primary":
        rrect(d, x, y, w, h, h / 2, fill=COLORS["primary"])
        fg = "#ffffff"
    elif kind == "ghost":
        rrect(d, x, y, w, h, h / 2, fill=COLORS["card"], outline=COLORS["primary"], width=1)
        fg = COLORS["primary"]
    else:  # soft
        rrect(d, x, y, w, h, h / 2, fill=COLORS["primary_soft"])
        fg = COLORS["primary"]
    center_text(d, x, y + (h - size) / 2 - 1, w, s, size=size, bold=True, fill=fg, ctx="按钮")


def status_bar(d, width=375, time_s="9:41"):
    """简化状态栏：时间 + 右侧信号/电池示意。"""
    text(d, 16, 7, time_s, size=11, bold=True)
    # 信号：四根高低不同的竖条
    for i in range(4):
        rect(d, 320 + i * 5, 12 - i * 1.5, 3, 4 + i * 1.5, fill=COLORS["text"])
    rrect(d, 342, 9, 20, 10, 3, fill=None, outline=COLORS["text"], width=1)
    rrect(d, 344, 11, 13, 6, 1.5, fill=COLORS["text"])
    rect(d, 363, 11.5, 2, 5, fill=COLORS["text"])


def navbar(d, title, width=375, back=False, right=None, bg=None):
    """导航栏，返回底边 y 坐标。"""
    y = 24
    h = 44
    rect(d, 0, y, width, h, fill=bg or COLORS["card"])
    if back:
        line(d, 20, y + 22, 26, y + 15, COLORS["text"], width=2)
        line(d, 20, y + 22, 26, y + 29, COLORS["text"], width=2)
    center_text(d, 0, y + 13, width, title, size=16, bold=True, ctx="导航标题")
    if right:
        fit(d, right, 13, 60, ctx="导航右侧")
        text(d, width - 16, y + 15, right, size=13, fill=COLORS["primary"], anchor="ra")
    line(d, 0, y + h, width, y + h, COLORS["line"], width=1)
    return y + h


TABS = ("首页", "搜索", "发布", "我的")


def tabbar(d, active=0, width=375, y=756, h=56):
    """底部导航栏。"""
    rect(d, 0, y, width, h, fill=COLORS["card"])
    line(d, 0, y, width, y, COLORS["line"], width=1)
    for i, name in enumerate(TABS):
        cx = width / len(TABS) * (i + 0.5)
        color = COLORS["primary"] if i == active else COLORS["sub"]
        # 图标：统一用一个圆角小方块 + 圆点示意，避免依赖 emoji 字体
        if i == 0:      # 首页 → 小房子
            d.polygon(
                [(px(cx - 8), px(y + 20)), (px(cx), px(y + 12)), (px(cx + 8), px(y + 20))],
                fill=color,
            )
            rect(d, cx - 5.5, y + 20, 11, 9, fill=color)
        elif i == 1:    # 搜索 → 放大镜
            d.ellipse([px(cx - 7), px(y + 13), px(cx + 5), px(y + 25)], outline=color, width=px(2))
            line(d, cx + 4, y + 24, cx + 8, y + 28, color, width=2)
        elif i == 2:    # 发布 → 加号
            rrect(d, cx - 9, y + 13, 18, 18, 5, fill=COLORS["primary_soft"])
            line(d, cx, y + 17, cx, y + 27, COLORS["primary"], width=2)
            line(d, cx - 5, y + 22, cx + 5, y + 22, COLORS["primary"], width=2)
        else:           # 我的 → 小人
            d.ellipse([px(cx - 5), px(y + 12), px(cx + 5), px(y + 22)], outline=color, width=px(2))
            d.arc([px(cx - 9), px(y + 21), px(cx + 9), px(y + 35)], 200, 340, fill=color, width=px(2))
        center_text(d, cx - 30, y + 34, 60, name, size=10, fill=color, ctx="底部导航")


def thumb(d, x, y, size, glyph, fg, bg):
    """列表缩略图：圆角色块 + 居中物品汉字（不依赖 emoji / 图片素材）。"""
    rrect(d, x, y, size, size, 12, fill=bg)
    center_text(d, x, y + size / 2 - 11, size, glyph, size=20, bold=True, fill=fg, ctx="缩略图")


def list_card(d, x, y, w, h, glyph, title, tag_text, tag_fg, tag_bg, info, status, status_fg):
    """一条信息卡片（首页 / 搜索结果 / 我的发布 共用）。"""
    rrect(d, x, y, w, h, 14, fill=COLORS["card"])
    thumb(d, x + 12, y + 12, 56, glyph, COLORS["primary"], COLORS["primary_soft"])
    inner_x = x + 12 + 56 + 12
    inner_w = x + w - 12 - inner_x
    fit(d, title, 14, inner_w - text_w(d, status, 10) - 8, bold=True, ctx="卡片标题")
    text(d, inner_x, y + 14, title, size=14, bold=True)
    text(d, x + w - 12, y + 17, status, size=10, fill=status_fg, anchor="ra")
    tw = tag(d, inner_x, y + 36, tag_text, tag_fg, tag_bg)
    fit(d, info, 10, x + w - 12 - (inner_x + tw + 6), ctx="卡片信息行")
    text(d, inner_x + tw + 6, y + 39, info, size=10, fill=COLORS["sub"])
    text(d, inner_x, y + 62, "点击查看详情 ›", size=10, fill=COLORS["sub"])


def arrow_down(d, cx, y0, y1, color=None, width=2, head=5):
    """竖直向下的箭头（流程图用）。"""
    color = color or COLORS["primary"]
    line(d, cx, y0, cx, y1 - head, fill=color, width=width)
    d.polygon(
        [(px(cx - head), px(y1 - head)), (px(cx + head), px(y1 - head)), (px(cx), px(y1))],
        fill=color,
    )

