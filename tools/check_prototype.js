/* 可点击原型自检：从 index.html 中抽出脚本，用 DOM 桩跑一遍 6 个界面。
   用法（在 hw3 目录下，需要本机装了 Node）： node tools/check_prototype.js
   检查两件事：
     1. 渲染：每个界面都能渲染，且包含关键内容；
     2. 交互：发布必填校验、详情页状态切换这两条分支行为正确。
   任何一项不符都会返回非 0。 */
const fs = require("fs");
const path = require("path");

const root = path.dirname(__dirname);
const html = fs.readFileSync(path.join(root, "prototype", "index.html"), "utf8");
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) {
  console.log("FAIL index.html 里没有找到 <script> 代码块");
  process.exit(1);
}

let page = "";
global.window = { location: { hash: "" } };
global.location = { hash: "" };
global.setTimeout = () => 0;
const docStub = {
  set innerHTML(v) { page = v; },
  get innerHTML() { return page; },
};
global.document = {
  getElementById: () => docStub,
  createElement: () => ({ style: {}, remove() {} }),
  body: { appendChild() {} },
};

eval(m[1] + "\n;globalThis.__screens = screens;");

const need = {
  home: ["校园失物招领", "＋ 发布", "点击查看详情"],
  search: ["找到 3 条", "校园卡", "没有更多结果"],
  detail: ["信息详情", "联系发布者", "三食堂二楼"],
  publish: ["发布信息", "物品名称", "发 布", "清空试试"],
  success: ["发布成功！", "返回首页"],
  mine: ["我的发布", "标记已归还"],
};

let failed = 0;
for (const id of Object.keys(need)) {
  try {
    render(id);
  } catch (e) {
    console.log("FAIL render(" + id + ")： " + e.message);
    failed++;
    continue;
  }
  const missing = need[id].filter((s) => !page.includes(s));
  if (missing.length) {
    console.log("FAIL " + id + " 缺少内容：" + missing.join(" / "));
    failed++;
  } else {
    console.log("ok   " + id + " 渲染正常（" + page.length + " 字符）");
  }
}
let behaviorFailed = 0;
function expect(cond, msg) {
  if (cond) {
    console.log("ok   " + msg);
  } else {
    console.log("FAIL " + msg);
    behaviorFailed++;
  }
}

// 行为断言 1：必填项填写完整时，「发 布」能进发布成功页
go("publish");
expect(page.includes("校园卡"), "发布页默认带出物品名称「校园卡」");
tryPublish();
expect(page.includes("发布成功！"), "填写完整时点「发 布」→ 进入发布成功页");

// 行为断言 2：清空必填项后，「发 布」会被拦下，停留在发布页
go("publish");
clearPublishName();
expect(page.includes("（必填，请填写）"), "点「清空试试 ›」后表单显示红色必填提示");
tryPublish();
expect(page.includes("发 布") && !page.includes("发布成功！"), "必填项为空时点「发 布」被拦下，不跳转");

// 行为断言 3：详情页「修改状态」能在两种状态间来回切换
go("detail");
const state = { textContent: "待认领", style: {} };
global.document.getElementById = (id) => (id === "detailState" ? state : docStub);
toggleState();
expect(state.textContent === "已归还", "详情页「修改状态」：待认领 → 已归还");
toggleState();
expect(state.textContent === "待认领", "详情页「修改状态」：已归还 → 待认领");

console.log(Object.keys(globalThis.__screens).length + " 个界面定义，失败 " + (failed + behaviorFailed)
  + " 项（渲染 " + failed + " / 交互 " + behaviorFailed + "）");
process.exit(failed + behaviorFailed ? 1 : 0);
