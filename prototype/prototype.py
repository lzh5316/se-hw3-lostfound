"""生成"校园失物招领小程序"的 6 张原型界面图（Pillow 手绘）。

运行：
    python prototype.py            # 输出到 screenshots/
    python prototype.py -o 目录    # 输出到指定目录

页面清单（对应作业要求第 4、5 条）：
    01_home_首页.png        首页：搜索入口 + 全部/招领/寻物 分类 + 信息流
    02_search_搜索.png      搜索：关键词「校园卡」→ 搜索结果列表
    03_detail_信息详情.png  信息详情：图片、时间、地点、状态、描述、联系方式
    04_publish_发布信息.png 发布信息：类型选择 + 表单 + 发布
    05_success_发布成功.png 发布成功：结果反馈 + 信息预览
    06_mine_我的发布.png    我的发布：查看并修改自己发布的信息状态
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
    COLORS, button, center_text, fit, fit_draw, line, list_card, navbar,
    new_screen, px, rect, rrect, status_bar, tabbar, tag, text, text_w, thumb,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "screenshots")

W, H = 375, 812

# 演示数据：招领 / 寻物 两条主线，字段与详情页保持一致
ITEMS = [
    dict(glyph="卡", title="校园卡（姓名：李同学）", tag="招领", info="三食堂二楼 · 今天 12:30",
         status="待认领", status_fg=COLORS["found"]),
    dict(glyph="钥", title="钥匙一串（带蓝色钥匙扣）", tag="寻物", info="图书馆三楼 · 今天 09:15",
         status="寻找中", status_fg=COLORS["lost"]),
    dict(glyph="伞", title="黑色折叠伞", tag="招领", info="教学楼 A 区 205 · 昨天 18:40",
         status="已归还", status_fg=COLORS["sub"]),
    dict(glyph="杯", title="白色保温杯（贴有字母贴纸）", tag="寻物", info="体育馆更衣室 · 昨天 16:05",
         status="寻找中", status_fg=COLORS["lost"]),
    dict(glyph="耳", title="蓝牙耳机充电盒", tag="招领", info="运动场看台 · 前天 20:10",
         status="待认领", status_fg=COLORS["found"]),
]


def tag_colors(item):
    if item["tag"] == "寻物":
        return COLORS["lost"], COLORS["lost_soft"]
    return COLORS["found"], COLORS["found_soft"]


def draw_card(d, x, y, w, h, item):
    fg, bg = tag_colors(item)
    list_card(d, x, y, w, h, item["glyph"], item["title"], item["tag"], fg, bg,
              item["info"], item["status"], item["status_fg"])


# ---------------------------------------------------------------- 01 首页


def screen_home():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "校园失物招领")
    # 搜索入口
    rrect(d, 16, 76, 343, 36, 18, fill=COLORS["bg"])
    d.ellipse([px(28), px(87), px(38), px(97)], outline=COLORS["sub"], width=px(1.5))
    line(d, 37, 96, 41, 100, COLORS["sub"], width=1.5)
    text(d, 48, 86, "搜索物品名称，如：校园卡、钥匙、雨伞", size=12, fill=COLORS["sub"])
    # 分类标签
    tabs = ("全部", "招领", "寻物")
    x = 16.0
    for i, name in enumerate(tabs):
        tw = text_w(d, name, 14, bold=True) + 16
        center_text(d, x, 132, tw, name, size=14, bold=True,
                    fill=COLORS["primary"] if i == 0 else COLORS["sub"], ctx="分类标签")
        if i == 0:
            rrect(d, x + tw / 2 - 10, 152, 20, 3, 1.5, fill=COLORS["primary"])
        x += tw + 8
    line(d, 0, 163, W, 163, COLORS["line"], width=1)
    # 信息流
    y = 175.0
    for item in ITEMS:
        draw_card(d, 16, y, 343, 84, item)
        y += 96
    text(d, W / 2, y + 6, "已加载全部 · 共 126 条信息", size=11, fill=COLORS["sub"], anchor="ma")
    # 悬浮「发布」按钮
    rrect(d, 275, 664, 84, 44, 22, fill=COLORS["shadow"])
    button(d, 275, 660, 84, 44, "＋ 发布", size=15)
    tabbar(d, 0)
    return im


# ---------------------------------------------------------------- 02 搜索


def screen_search():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "搜索", back=True)
    rrect(d, 16, 76, 343, 40, 20, fill=COLORS["bg"])
    d.ellipse([px(28), px(88), px(38), px(98)], outline=COLORS["primary"], width=px(1.5))
    line(d, 37, 97, 41, 101, COLORS["primary"], width=1.5)
    text(d, 48, 87, "校园卡", size=14, bold=True)
    line(d, 48 + text_w(d, "校园卡", 14, True) + 4, 86, 48 + text_w(d, "校园卡", 14, True) + 5, 106,
         COLORS["primary"], width=1.5)  # 光标
    center_text(d, W - 46, 88, 24, "✕", size=13, fill=COLORS["sub"], ctx="清空")
    text(d, 16, 130, "找到 3 条与「校园卡」相关的信息", size=12, fill=COLORS["sub"])
    hits = [ITEMS[0],
            dict(glyph="卡", title="校园卡（学号尾号 37，捡到的）", tag="寻物",
                 info="紫金楼 B 座 401 · 今天 08:40", status="寻找中", status_fg=COLORS["lost"]),
            dict(glyph="卡", title="校园卡（已挂失，请勿使用）", tag="招领",
                 info="校医院一楼大厅 · 昨天 10:20", status="已归还", status_fg=COLORS["sub"])]
    y = 150.0
    for item in hits:
        draw_card(d, 16, y, 343, 84, item)
        y += 96
    # 空状态提示（说明"没有更多结果"时的界面）
    line(d, 24, y + 12, W - 24, y + 12, COLORS["line"], width=1)
    text(d, W / 2, y + 26, "没有更多结果了，换个关键词试试？", size=11,
         fill=COLORS["sub"], anchor="ma")
    from proto_common import tabbar
    tabbar(d, 1)
    return im


# ---------------------------------------------------------------- 03 信息详情


def screen_detail():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "信息详情", back=True, right="分享")
    # 物品大图（原型中用色块 + 物品名称表示，实际开发时换成用户上传的图片）
    rect(d, 0, 68, W, 176, fill=COLORS["primary_soft"])
    fg, bg = tag_colors(ITEMS[0])
    tag(d, 16, 80, "招领", fg, bg, size=11)
    center_text(d, 0, 128, W, "校 园 卡", size=30, bold=True, fill=COLORS["primary"], ctx="图片占位")
    text(d, W / 2, 216, "（此处为上传的物品照片）", size=11,
         fill=COLORS["primary_dark"], anchor="ma")
    # 标题与状态
    text(d, 16, 258, "校园卡（姓名：李同学）", size=17, bold=True)
    tag(d, 16, 288, "待认领", COLORS["found"], COLORS["found_soft"], size=10)
    text(d, 60, 291, "发布于 今天 12:30", size=11, fill=COLORS["sub"])
    line(d, 16, 316, W - 16, 316, COLORS["line"], width=1)
    # 信息表
    rows = (("信息类型", "招领"), ("物品名称", "校园卡（尾号 37）"),
            ("拾取地点", "三食堂二楼"), ("拾取时间", "今天 12:30"),
            ("联系方式", "微信 Lzh-5316"))
    y = 330.0
    for label, value in rows:
        fit(d, value, 13, 240, ctx="详情字段")
        text(d, 16, y, label, size=12, fill=COLORS["sub"])
        text(d, 96, y, value, size=13, bold=True)
        y += 30
    line(d, 16, y + 6, W - 16, y + 6, COLORS["line"], width=1)
    # 描述
    text(d, 16, y + 18, "物品描述", size=13, bold=True)
    fit_draw(d, 16, y + 40,
             "在三食堂二楼靠窗的位置捡到一张校园卡，卡面姓名李同学，学号尾号 37，"
             "已交到食堂一楼服务台备份登记，也可以直接联系我。",
             12, W - 32, fill=COLORS["text"], spacing=6, ctx="详情描述")
    # 底部操作区
    button(d, 16, 704, 166, 46, "修改状态", size=15, kind="ghost")
    button(d, 193, 704, 166, 46, "联系发布者", size=15)
    return im


# ---------------------------------------------------------------- 04 发布信息


def screen_publish():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "发布信息", back=True)
    # 类型切换：寻物 / 招领
    rrect(d, 16, 84, 343, 40, 10, fill="#eef1f7")
    rrect(d, 20, 88, 168, 32, 8, fill=COLORS["card"])
    center_text(d, 20, 95, 168, "寻物", size=14, fill=COLORS["sub"], ctx="类型")
    center_text(d, 192, 95, 168, "招领", size=14, bold=True, fill=COLORS["primary"], ctx="类型")
    # 表单
    rrect(d, 16, 136, 343, 396, 14, fill=COLORS["card"])
    fields = (("物品名称 *", "校园卡"), ("物品类型 *", "证件卡类 ▾"),
              ("拾取地点 *", "三食堂二楼"), ("拾取时间 *", "今天 12:30"))
    y = 148.0
    for label, value in fields:
        text(d, 32, y + 4, label, size=12, fill=COLORS["sub"])
        fit(d, value, 13, 200, ctx="表单值")
        text(d, 150, y + 3, value, size=13, bold=True)
        y += 52
        line(d, 32, y - 14, W - 32, y - 14, COLORS["line"], width=1)
    text(d, 32, y + 2, "物品描述", size=12, fill=COLORS["sub"])
    fit_draw(d, 150, y, "放在二楼靠窗座位，卡面姓名李同学", 12, 192, spacing=5, ctx="发布描述")
    y += 62
    line(d, 32, y, W - 32, y, COLORS["line"], width=1)
    text(d, 32, y + 14, "上传图片", size=12, fill=COLORS["sub"])
    thumb(d, 150, y + 8, 64, "卡", COLORS["primary"], COLORS["primary_soft"])
    rrect(d, 222, y + 8, 64, 64, 12, fill=None, outline=COLORS["line"], width=1)
    center_text(d, 222, y + 30, 64, "＋", size=20, fill=COLORS["sub"], ctx="上传")
    y += 84
    line(d, 32, y, W - 32, y, COLORS["line"], width=1)
    text(d, 32, y + 14, "联系方式 *", size=12, fill=COLORS["sub"])
    text(d, 150, y + 13, "微信 Lzh-5316", size=13, bold=True)
    # 提示与提交
    rrect(d, 16, 552, 343, 44, 10, fill=COLORS["lost_soft"])
    fit_draw(d, 28, 564, "请勿在描述中填写他人隐私信息；发布后可在「我的发布」修改状态。",
             11, 319, fill="#9a5b00", spacing=3, ctx="发布提示")
    button(d, 16, 616, 343, 46, "发 布", size=16)
    text(d, W / 2, 682, "发布成功后，信息会展示在首页与搜索结果中", size=11,
         fill=COLORS["sub"], anchor="ma")
    return im


# ---------------------------------------------------------------- 05 发布成功


def screen_success():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "发布成功")
    d.ellipse([px(W / 2 - 40), px(150), px(W / 2 + 40), px(230)], fill=COLORS["found_soft"])
    line(d, W / 2 - 18, 190, W / 2 - 6, 202, COLORS["ok"], width=4)
    line(d, W / 2 - 6, 202, W / 2 + 19, 175, COLORS["ok"], width=4)
    center_text(d, 0, 254, W, "发布成功！", size=24, bold=True, ctx="成功标题")
    fit_draw(d, 68, 300, "你的招领信息已经发布，其他同学可以在首页或通过搜索找到它。",
             13, 239, fill=COLORS["sub"], spacing=6, ctx="成功说明")
    draw_card(d, 24, 360, 327, 84, ITEMS[0])
    text(d, 24, 458, "接下来可以：", size=12, fill=COLORS["sub"])
    button(d, 24, 480, 327, 46, "查看我的发布", size=15, kind="soft")
    button(d, 24, 538, 327, 46, "返回首页", size=15)
    text(d, W / 2, 610, "信息填错了？可以在「我的发布」里修改状态。", size=11,
         fill=COLORS["sub"], anchor="ma")
    return im


# ---------------------------------------------------------------- 06 我的发布


def screen_mine():
    im, d = new_screen(W, H)
    status_bar(d)
    navbar(d, "我的发布", back=True, right="筛选")
    rect(d, 0, 68, W, 52, fill=COLORS["card"])
    text(d, 16, 84, "我发布了 3 条信息", size=14, bold=True)
    text(d, 16, 104, "待认领 1 条 · 寻找中 1 条 · 已归还 1 条", size=11, fill=COLORS["sub"])
    for i, item in enumerate((ITEMS[0], ITEMS[1], ITEMS[2])):
        y = 132.0 + i * 132
        draw_card(d, 16, y, 343, 120, item)
        button(d, 100, y + 88, 76, 26, "修改状态", size=11, kind="ghost")
        button(d, 184, y + 88, 96, 26, "标记已归还", size=11, kind="soft")
        text(d, 292, y + 94, "更多 ›", size=11, fill=COLORS["primary"])
    tabbar(d, 3)
    return im


# ---------------------------------------------------------------- 入口

SCREENS = (
    ("01_home_首页.png", screen_home),
    ("02_search_搜索.png", screen_search),
    ("03_detail_信息详情.png", screen_detail),
    ("04_publish_发布信息.png", screen_publish),
    ("05_success_发布成功.png", screen_success),
    ("06_mine_我的发布.png", screen_mine),
)


def main(argv=None):
    ap = argparse.ArgumentParser(description="生成校园失物招领小程序的原型界面图")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT, help="输出目录")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    for name, fn in SCREENS:
        im = fn()
        path = os.path.join(args.out, name)
        im.save(path)
        print(f"saved {path} {im.size[0]}x{im.size[1]}")
    print(f"共 {len(SCREENS)} 张原型图；文字排版自检通过（无溢出）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
