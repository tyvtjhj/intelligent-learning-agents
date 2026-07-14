<div align="center">

# 🧠 Feynman Tutor

**一个把「讲清楚一件事」变成可复用方法论的 Claude 技能（Skill）**

*A Claude Code skill that turns "truly understanding something" into a repeatable teaching method.*

[![Skill](https://img.shields.io/badge/Claude-Skill-8A63D2?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code/skills)
[![Live Demo](https://img.shields.io/badge/🌐_在线演示-Live-8A63D2.svg)](https://wangsiyi7.github.io/feynman-tutor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Language](https://img.shields.io/badge/lang-中文-red.svg)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/status-active-success.svg)](#-路线图--roadmap)

[**🌐 在线演示**](https://wangsiyi7.github.io/feynman-tutor/) · [功能](#-它能做什么) · [安装](#-安装) · [用法](#-用法) · [理念](#-设计理念) · [示例](#-示例片段) · [路线图](#-路线图--roadmap)

<br/>

**▶ 在线体验「费曼演示台」 → https://wangsiyi7.github.io/feynman-tutor/**

</div>

---

## 📖 这是什么

**Feynman Tutor** 是一个 [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) 技能。一旦启用，Claude 在给你讲解任何概念时，会自动切换成一套严格、有耐心、绝不甩术语的「费曼式」教学人格：

> 用户要的不是「知道名词」，而是「在脑子里建出一台能自己运转的模型」。

它把这套教学法固化为 **7 条可复用的教学纪律**，无论主题是计算机网络、机器学习、量子物理还是期权定价，都用同一种节奏招呼你——**默认零基础起步，每个术语当场讲透，能画图就画图。**

---

## ✨ 它能做什么

启用后，Claude 的每一次讲解都会遵循下面七条纪律：

| # | 纪律 | 一句话 |
|---|------|--------|
| 1 | 🧩 **费曼化** | 先给生活类比和画面，再回到术语，不甩干巴巴的定义 |
| 2 | 🔤 **零英文裸词** | 任何英文 / 简写首次出现，当场给「全称 → 直译 → 大白话」 |
| 3 | 📒 **术语账本** | 维护一张「已声明清单」，新词标 🆕，讲过的不重复 |
| 4 | 🗺️ **概念云 + 连线** | 先给一张概念地图看全貌，再逐块填肉 |
| 5 | 🟦 **像素图** | 用 ASCII 字符把抽象机制画出来，看比读快 |
| 6 | 🎚️ **动态节奏** | 零基础起步，但在舒适圈之上垫一点；讲透但不灌水 |
| 7 | 🧭 **结尾给菜单** | 列出 3~4 个深钻方向，把方向盘交给你的好奇心 |

每条纪律在 [`SKILL.md`](SKILL.md) 里都附带了 **「为什么这样做」** 的解释——这样 Claude 执行时不是死记规则，而是真正理解意图、灵活发挥。

---

## 📦 安装

技能就是一个放进 `~/.claude/skills/` 的文件夹。克隆本仓库到该目录即可：

**macOS / Linux**
```bash
git clone https://github.com/wangsiyi7/feynman-tutor.git ~/.claude/skills/feynman-tutor
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/wangsiyi7/feynman-tutor.git "$env:USERPROFILE\.claude\skills\feynman-tutor"
```

安装后重启 Claude Code，技能即可被自动发现。验证：

```bash
# 在 Claude Code 里输入，应能看到 feynman-tutor 出现在技能列表
/feynman-tutor
```

---

## 🚀 用法

**两种触发方式：**

- **自动触发** —— 当你表达「想真正搞懂」时，Claude 会自己启用：
  > 「帮我理解一下 TCP 拥塞控制的原理」
  > 「区块链共识机制底层到底是怎么回事，费曼化讲一下」
  > 「假设我啥也不懂，从零帮我理解傅里叶变换」

- **手动触发** —— 直接调用：
  ```
  /feynman-tutor
  ```

**它会自动放过的场景**（这些不该触发深度教学）：
快速命令（`git rebase 咋敲`）、修 bug、执行任务、单词翻译、要「一句话」结论——技能会识别意图，该简洁就简洁。

---

## 🎯 设计理念

大多数「讲解」失败，是因为它在**堆砌定义**而不是**搭建模型**。本技能围绕一个核心信念设计：

```
            ┌─────────────────────────────────────────┐
            │  知道名词  ≠  真正理解                     │
            └─────────────────────────────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
  ┌─────────┐       ┌─────────┐       ┌─────────┐
  │ 生活类比 │  ──▶  │ 像素图   │  ──▶  │ 术语账本 │
  │ 挂钩经验 │       │ 看见机制 │       │ 累积掌控 │
  └─────────┘       └─────────┘       └─────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                ┌───────────────────┐
                │ 脑中可运转的模型   │
                └───────────────────┘
```

人脑靠「挂钩」记东西：一个孤立的定义没有挂钩，记不住；一个「像寄快递」「像打电话」的类比，能让陌生概念挂到已有经验上，一下就稳了。最好的学习区永远在「已知」与「未知」的交界处——所以技能要求**零基础起步，却在舒适圈之上再垫一点**。

---

## 💬 示例片段

下面是技能启用后，解释 `DNS`（域名系统）时的真实风格：

> **DNS**，全称 *Domain Name System*，直译「域名系统」。费曼一下：它就是**互联网的电话簿**。你只记得住 `google.com` 这种名字，但机器之间靠一串数字地址找彼此。你一输入网址，设备先偷偷问 DNS：「`google.com` 的数字地址是多少？」DNS 答：「142.250.x.x。」——名字翻成数字，这就是它干的唯一一件事。

配合像素图呈现机制：

```
📱手机:"google.com 地址多少?"
   │
   ▼ 先问家里的路由器(它常兼任小电话簿)
🛜路由器:"我没存…我去帮你问运营商的大电话簿"
   │
   ▼
🏢运营商DNS ──── 一路接力问到权威源 ────▶ 答案传回 📱
```

> 📄 完整的一段教学示例见 [`docs/example-session.md`](docs/example-session.md)。

---

## 🗂️ 项目结构

本仓库遵循 **skill-creator 渐进式披露范式**：`SKILL.md` 保持精简常驻，更深的弹药库放进 `references/`，按需查阅。

```
feynman-tutor/
├── SKILL.md                       # 技能入口：7 条纪律 + 为什么 + 资源导航
├── references/                    # 渐进式披露的深度资源（按需加载）
│   ├── analogy-bank.md            #   类比库（网络/编程/ML/物理/金融）
│   ├── pixel-diagram-cookbook.md  #   ASCII 像素图模板库
│   └── teaching-playbook.md       #   临场读信号、判断真懂、开菜单
├── assets/
│   └── term-ledger-template.md    # 术语账本表格模板
├── evals/
│   └── evals.json                 # 触发评测集（该触发 / 不该触发）
├── docs/                          # GitHub Pages 网站 + 教学示例
│   ├── index.html · style.css · script.js   # 交互式展示站（费曼演示台）
│   └── example-session.md         # 一段完整的教学示例
├── .github/workflows/pages.yml    # 自动部署 Pages
├── README.md · CONTRIBUTING.md · LICENSE
```

---

## 🛣️ 路线图 / Roadmap

- [x] v1.0 — 七条教学纪律成型，可自动 / 手动触发
- [x] v1.1 — 升级为完整 **skill-creator 范式**（`references/` + `evals/` + `assets/`）+ 交互式 GitHub Pages 网站
- [ ] v1.2 — **触发描述优化**：用 `evals/evals.json` 校准「该触发 / 不该触发」的准确度
- [ ] v1.3 — 英文版 README（`README.en.md`）
- [ ] 探索 — 跨会话持久化「术语账本」，让长期学习连贯

---

## 🤝 参与贡献

欢迎提 Issue 和 PR——尤其是更好的类比、更清晰的像素图、或新的近似坑测试用例。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📜 License

[MIT](LICENSE) © 2026 wangsiyi7

---

<div align="center">
<sub>用费曼的方式学习：如果你不能把它讲简单，说明你还没真懂它。</sub>
</div>
