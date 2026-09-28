"""生成 3 张流程图（Pillow 手绘，风格与原型图一致）。

对应作业要求第 5 条与第 8 条：
    查看信息 → 查看详情
    发布信息 → 发布成功
    搜索物品 → 查看搜索结果

运行：
    python flowcharts.py
"""

from __future__ import annotations

import argparse
import os
import sys

# 中文控制台（cp936 / cp950）打不出某些简体字时会抛 UnicodeEncodeError；兜底改成替换。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

from proto_common import (
    COLORS, arrow_down, center_text, fit, line, new_screen, px, rrect, text, text_w,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "screenshots")

WIDTH = 375
CW = 279          # 流程框宽度
CX = WIDTH / 2    # 中心线


def flow_canvas(title, steps):
    """按步数计算画布高度后绘制：胶囊(开始/结束) + 矩形(处理) + 箭头 + 标题。"""
    step_h, gap = 56, 34
    top = 24
    height = top + len(steps) * step_h + (len(steps) - 1) * gap + 96
    im, d = new_screen(WIDTH, height)
    rrect(d, 12, 12, WIDTH - 24, height - 24, 16, fill=COLORS["card"])
    y = top + 12
    for i, (kind, label) in enumerate(steps):
        if kind == "end":       # 开始 / 结束：胶囊形
            rrect(d, CX - 52, y, 104, 40, 20, fill=COLORS["primary_soft"],
                  outline=COLORS["primary"], width=1.5)
            center_text(d, CX - 52, y + 12, 104, label, size=14, bold=True,
                        fill=COLORS["primary"], ctx="起止框")
            box_h = 40
        else:                   # 处理框：圆角矩形
            rrect(d, CX - CW / 2, y, CW, step_h, 12, fill="#f7f9ff",
                  outline=COLORS["primary"], width=1.5)
            lines = fit(d, label, 13, CW - 24, ctx=f"流程框{i}")
            step = 19
            y0 = y + (step_h - len(lines) * step) / 2 + 1
            for j, ln in enumerate(lines):
                center_text(d, CX - CW / 2, y0 + j * step, CW, ln, size=13, ctx="流程文字")
            box_h = step_h
        if i < len(steps) - 1:
            arrow_down(d, CX, y + box_h + 6, y + box_h + gap - 6)
        y += box_h + gap
    # 图题（与样例博客一致：图题在流程图下方）
    ty = y - gap + 28
    center_text(d, 0, ty, WIDTH, title, size=16, bold=True, ctx="图题")
    return im


FLOWS = (
    ("flow_view_查看信息流程图.png", "查看信息流程图", (
        ("end", "开始"),
        ("box", "进入首页，浏览最新寻物 / 招领信息"),
        ("box", "在信息流中选择感兴趣的信息"),
        ("box", "点击卡片右下角「点击查看详情」"),
        ("box", "进入信息详情页"),
        ("box", "查看图片、时间、地点、状态、描述和联系方式"),
        ("box", "点击「联系发布者」联系对方"),
        ("end", "结束"),
    )),
    ("flow_publish_发布信息流程图.png", "发布信息流程图", (
        ("end", "开始"),
        ("box", "点击首页右下角「＋ 发布」按钮"),
        ("box", "选择信息类型：寻物 / 招领"),
        ("box", "填写物品名称、类型、地点、时间"),
        ("box", "上传物品照片并填写联系方式"),
        ("box", "点击「发布」按钮提交"),
        ("box", "系统校验必填项并保存信息"),
        ("end", "发布成功"),
    )),
    ("flow_search_搜索流程图.png", "搜索物品流程图", (
        ("end", "开始"),
        ("box", "在首页点击顶部搜索框"),
        ("box", "输入物品名称等关键词（如：校园卡）"),
        ("box", "点击「搜索」查看结果列表"),
        ("box", "结果为空时提示更换关键词"),
        ("box", "点击目标信息进入详情页"),
        ("end", "结束"),
    )),
)


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成校园失物招领小程序的流程图")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT, help="输出目录")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    for name, title, steps in FLOWS:
        im = flow_canvas(title, steps)
        path = os.path.join(args.out, name)
        im.save(path)
        print(f"saved {path} {im.size[0]}x{im.size[1]}")
    print(f"共 {len(FLOWS)} 张流程图；文字排版自检通过（无溢出）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
