# GitDoc — 让 Word 文档拥有 Git 的力量

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**GitDoc** 为 Word 文档提供 Git 式的版本控制：每次保存自动记录版本，任意两个版本之间词级对比，一键回滚。不需要学 Git。

---

## GitDoc 能做什么

- **自动版本记录** — 每次保存文档，GitDoc 自动创建一个版本快照
- **可视化历史时间轴** — 在浏览器中查看所有历史版本，谁在什么时候改了什么，一目了然
- **词级差异对比** — 任意两个版本逐词对比，绿增红删，中文分词精准高亮
- **一键回滚** — 恢复到任意历史版本，回滚前自动备份，永远不怕丢数据
- **AI 助手集成** — 内置 MCP 服务器，让 Claude Code 等 AI 工具直接读取和对比 Word 文档

---

## 两种使用方式

GitDoc 提供两种使用方式，分别面向**人**和 **AI**。

### 🌐 浏览器界面（给人用）

后端启动后，浏览器访问 **`https://localhost:18521/`**，输入文档路径即可使用全部功能。

- 版本历史时间轴
- 并排差异对比（绿色新增 / 红色删除）
- 版本内容预览
- 一键回滚

> **为什么不用 Word 插件？** Microsoft 365 家庭版不支持自定义加载项。GitDoc 提供完整的 Web 界面，不依赖 Office 版本。

如果你使用的是 **Office 专业版 / 企业版**，也可以通过 Word 任务窗格使用 GitDoc —— 详见下方 [可选：安装 Word 加载项](#可选安装-word-加载项)。

### 🤖 MCP 服务（给 AI 用）

GitDoc 内置 MCP（模型上下文协议）服务器，让 AI 编程助手可以直接操作 Word 文档。

AI 可以帮你：

- 读取 `.docx` 需求文档，根据内容写代码
- 对比合同/报告的修改版本，自动生成变更摘要
- 在 PR 审查时，自动解析关联的 Word 设计文档

```bash
# Claude Code 一键接入
claude mcp add gitdoc -- python backend/mcp_server.py
```

详细文档：[docs/mcp.md](docs/mcp.md)

---

## 快速开始

三步启动：**装依赖 → 生成证书 → 启动后端**。

### 1. 安装依赖

```bash
git clone https://github.com/xijunyuan/GitDoc.git
cd GitDoc
cd backend
pip install -r requirements.txt
```

### 2. 生成 SSL 证书（只需一次）

浏览器需要 HTTPS 才能访问本地服务。双击运行 **`scripts\gen_cert.bat`**：

- 自动调用 PowerShell 生成自签名证书
- 弹 UAC 提示时点 **"是"**（需要管理员权限信任证书）
- 看到 `[OK] Certificate is now trusted.` 即完成

> 也可以手动信任：双击 `scripts\certs\localhost.crt` → 安装到"受信任的根证书颁发机构"。

### 3. 启动后端

双击运行 **`scripts\start_backend.bat`**，看到以下输出即启动成功：

```text
GitDoc Backend v1.0.0
Frontend:  https://localhost:18521
API docs:  https://localhost:18521/docs
SSL:       enabled
```

然后浏览器打开 **<https://localhost:18521/>**，输入你的 `.docx` 文件路径，开始使用。

> 首次访问会提示"连接不是私密连接"——点击 **「高级」→「继续前往」** 即可。

### 接下来

1. 在输入框中填入 `.docx` 文件的完整路径，如 `C:\Users\用户名\Desktop\报告.docx`
2. 像平常一样编辑和保存文档，GitDoc 自动记录每个版本
3. 在 Web 界面中查看历史、对比差异、回滚

---

## 系统要求

- Windows 10/11
- Python 3.10+
- Git for Windows

---

## 可选：安装 Word 加载项

> **注意**：Microsoft 365 家庭版不支持自定义加载项。此方式仅适用于 **Office 专业版 / 企业版**。

如果你使用的是支持的 Office 版本，可以在 Word 任务窗格中使用 GitDoc：

1. 确保后端已启动
2. 双击运行 **`scripts\install_addin.bat`**
3. 打开 Word → **插入** → **我的加载项** → **共享文件夹** → 添加 **"GitDoc - 文档版本管理"**

---

## 技术栈

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 文档解析 | `python-docx` + `lxml` | 提取 OOXML 结构化文本 |
| 差异引擎 | `diff-match-patch` + `jieba` | 词级精确对比，中文分词 |
| 后端框架 | FastAPI + Uvicorn | REST API + HTTPS |
| 版本控制 | Git CLI | 核心版本管理 |
| Web 前端 | HTML5 / CSS3 / JS (零依赖) | 浏览器界面与 Word 加载项共用 |
| AI 接口 | MCP (FastMCP) | AI 助手标准协议 |

---

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/status` | 健康检查 |
| `POST` | `/api/init` | 初始化文档仓库 |
| `POST` | `/api/commit` | 手动提交版本 |
| `GET` | `/api/history` | 版本历史列表 |
| `GET` | `/api/diff` | 两版本词级差异对比 |
| `POST` | `/api/rollback` | 回滚到指定版本 |
| `GET` | `/api/preview` | 版本内容纯文本预览 |
| `GET/POST` | `/api/notes` | 版本备注管理 |

---

## MCP 工具一览

| 工具 | 说明 | 需要 Git 仓库 |
| --- | --- | --- |
| `read_docx` | 解析任意 `.docx` 文件，返回结构化文本 | ❌ |
| `get_history` | 获取文档 Git 提交历史 | ✅ |
| `diff_versions` | 同一文档两个 Git 版本的词级差异 | ✅ |
| `preview_version` | 某个 Git 版本的纯文本内容 | ✅ |
| `diff_files` | 任意两个 `.docx` 文件的词级差异 | ❌ |

---

## 文档存储

GitDoc 在每个文档同级目录创建 `.gitdoc/` 隐藏文件夹：

```text
论文.docx                  ← 你编辑的文件
.gitdoc/
  ├── .git/               ← Git 仓库（完整版本历史）
  ├── cache/              ← 文本提取缓存
  ├── backups/            ← 回滚前安全备份
  └── config.json         ← 文档级别配置
```

---

## 项目结构

```text
GitDoc/
├── backend/
│   ├── main.py              # REST API 入口 (FastAPI)
│   ├── mcp_server.py        # MCP 服务器 (AI 助手接口)
│   ├── config.py            # 全局配置
│   ├── models.py            # 数据模型
│   ├── git_operations.py    # Git 操作封装
│   ├── docx_parser.py       # OOXML 文档解析
│   ├── diff_engine.py       # 词级差异引擎
│   ├── commit_manager.py    # 提交管理
│   ├── rollback_manager.py  # 回滚管理
│   ├── file_watcher.py      # 文件变更监听
│   └── tests/               # 单元测试
├── frontend/
│   └── word-addin/          # Web 界面 & Word 加载项
│       ├── index.html       # 入口页面
│       ├── main.js          # 主逻辑
│       ├── api.js           # API 客户端
│       ├── panels/          # 功能面板 (history/diff/preview/rollback)
│       ├── utils/           # 工具模块 (i18n/event-bus)
│       └── styles/          # 样式
├── docs/
│   └── mcp.md               # MCP 服务器文档
├── scripts/                 # 一键脚本
│   ├── start_backend.bat    # 启动后端
│   ├── gen_cert.bat         # 生成 SSL 证书
│   ├── install_addin.bat    # 安装 Word 加载项
│   └── install_mcp.bat      # 安装 MCP 依赖
└── LICENSE
```

---

## 后续计划

- **VS Code 插件** — 在编辑器内渲染 `.docx`、查看 Git 历史和差异
- **GitHub Action** — PR 中的 Word 文档变更自动生成摘要
- **国产化适配** — WPS 格式支持、统信 UOS / 麒麟系统适配

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
