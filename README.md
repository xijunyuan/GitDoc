# GitDoc — 文档版本管理系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基于 Git 的 Word 文档版本控制工具，为课题组和工程项目部提供代码级版本管理能力，**无需学习 Git**。

## 项目愿景

为课题组写论文、工程项目部写报告等需要**异步协作、强版本管理**的团队，提供一套兼容 Word/WPS，具备 Git 式版本历史、差异对比与回滚能力的文档协作工具。用户无需学习 Git，即可享受代码级版本控制带来的清晰与安全。

### 核心原则

- **最小增量** — 不取代 Word/WPS，而是用 Git 的协作理念"武装"现有工作流
- **零学习成本** — 分支、PR 等概念全部翻译为文档术语
- **异步优先** — 刻意不做实时协同编辑，聚焦异步场景下的版本混乱和合并痛点
- **兼容 Word/WPS** — 以 `.docx` 为主要格式，通过解析 OOXML 实现结构化对比

## 功能 (MVP)

- **自动版本记录** — 保存文档时自动创建 Git commit
- **版本历史** — 可视化时间轴展示所有历史版本
- **差异对比** — 任意两个版本间的词级高亮对比（绿增红删）
- **一键回滚** — 恢复到任意历史版本，回滚前自动备份
- **手动提交** — 支持带描述的版本保存

## 系统要求

- Windows 10/11
- Microsoft Word 2016 或更高版本
- Python 3.10+（或使用打包后的 exe）
- [Git for Windows](https://git-scm.com/download/win)

## 快速开始

整个配置流程只需三步，**每一步都有对应的 `.bat` 脚本，双击即可运行**：

> 🔒 → ▶️ → 📎
> 信任证书 → 启动后端 → 安装加载项

---

### 1. 克隆项目 & 安装依赖

```bash
git clone https://github.com/xijunyuan/GitDoc.git
cd GitDoc
cd backend
pip install -r requirements.txt
```

---

### 2. 配置 SSL 证书（只需一次）

由于 Word 要求加载项必须通过 HTTPS 通信，GitDoc 使用自签名证书在本地建立安全连接。**这一步会生成证书并让 Windows 信任它**。

双击运行 **`scripts\gen_cert.bat`**：

- 会自动调用 PowerShell 生成证书（无需安装 OpenSSL）
- 弹 UAC 提示时点 **"是"**（需要管理员权限来信任证书）
- 看到 `[OK] Certificate is now trusted.` 即完成

> **如果不想给管理员权限**，脚本会提示手动信任的方法：双击 `scripts\certs\localhost.crt`，按向导安装到"受信任的根证书颁发机构"。
>
> 也可以手动执行以下命令信任证书：
> ```powershell
> certutil -addstore -user "Root" "scripts\certs\localhost.crt"
> ```

---

### 3. 启动后端服务

后端是 GitDoc 的"大脑"，负责管理文档版本、计算差异等工作。**每次使用 GitDoc 前都需要先启动它**。

双击运行 **`scripts\start_backend.bat`**，会弹出命令行窗口，显示：

```text
GitDoc Backend v0.1.0
Python:   C:\...\python.exe
Location: ...\GitDoc\backend
Port:     http://127.0.0.1:18521
```

看到这几行就说明启动成功了。**不要关掉这个窗口**，让它一直在后台运行。

> **如果窗口一闪就消失了**：说明 Python 没有正确安装。请先安装 [Python 3.10+](https://www.python.org/downloads/)，安装时务必勾选 **"Add Python to PATH"**，然后重新双击 `start_backend.bat`。
>
> **备选方案（手动启动）**：在项目文件夹地址栏输入 `cmd` 回车，执行：
>
> ```bash
> cd backend
> python main.py
> ```

---

### 4. 在 Word 中安装加载项（只需一次）

双击运行 **`scripts\install_addin.bat`**，它会自动完成以下检查并安装：

1. ✅ 检查 SSL 证书是否已信任
2. ✅ 检查后端是否正在运行
3. ✅ 将加载项清单复制到 Office 共享文件夹

如果某项未通过，脚本会告诉你具体怎么修。

安装完成后，打开（或重启）Word：

1. 点击顶部菜单栏 **插入** → **我的加载项**
2. 在弹出的窗口中，选择顶部的 **"共享文件夹"** 标签页
3. 列表里会出现 **"GitDoc - 文档版本管理"**，点击 → **"添加"**

Word 右侧会弹出 GitDoc 任务窗格，说明安装成功！

---

### 5. 开始使用

1. 用 Word 打开任意 `.docx` 文档
2. 右侧任务窗格会显示 GitDoc 面板（如果没显示，点击 **插入** → **我的加载项** 重新打开）
3. 像平常一样编辑文档，每次保存（`Ctrl+S`）时，GitDoc 会自动记录一个新版本
4. 在面板中可以查看历史版本、对比任意两个版本的差异、一键回滚到旧版本、对版本进行备注

### 浏览器端使用（推荐）

后端启动后，也可以直接在浏览器中访问 GitDoc Web 界面：

1. 浏览器访问 **https://localhost:18521/**
2. 首次访问会提示"连接不是私密连接"，点击 **「高级」→「继续前往」**
3. 在输入框中填入 `.docx` 文件的完整路径，如 `C:\Users\用户名\Desktop\报告.docx`，即可使用全部功能（版本历史、差异对比、回滚）

> 此方式不依赖 Word 加载项，Office 365 家庭版用户也可使用。

## 文档格式说明

| 格式 | 版本控制 | 文本对比 | 回滚 |
|---|---|---|---|
| `.docx`（Word 2007+） | ✅ | ✅ | ✅ |
| `.doc`（Word 97-2003） | ✅ | ❌ | ✅ |

> **强烈建议使用 `.docx` 格式。** 如果是 `.doc` 文件，请在 Word 中「另存为」`.docx`。

## MCP 服务器（AI 助手集成）

GitDoc v0.2.0 起内置 MCP（模型上下文协议）服务器，让 AI 编程助手可以直接读取、对比和分析 Word 文档。

### 快速开始

双击运行 **`scripts\install_mcp.bat`** 一键安装，然后：

```bash
# Claude Code
claude mcp add gitdoc -- python backend/mcp_server.py

# 或启动 HTTP 模式
python backend/mcp_server.py --transport http
```

安装后，AI 可以帮你：
- 读 `.docx` 需求文档，根据内容写代码
- 对比合同的修改版本，生成变更摘要
- 自动追踪文档变更历史

详细文档见 **[docs/mcp.md](docs/mcp.md)**。

## 项目结构

```
GitDoc/
├── backend/                    # Python 后端 (FastAPI)
│   ├── main.py                 # REST API 服务入口
│   ├── mcp_server.py           # MCP 服务器（AI 助手接口）
│   ├── config.py               # 配置管理
│   ├── models.py               # Pydantic 数据模型
│   ├── git_operations.py       # Git 操作封装
│   ├── docx_parser.py          # OOXML 文档解析 (python-docx)
│   ├── diff_engine.py          # 词级差异引擎 (diff-match-patch)
│   ├── commit_manager.py       # 提交管理器
│   ├── rollback_manager.py     # 回滚管理器
│   ├── file_watcher.py         # 文件变更监听器 (watchdog)
│   └── tests/                  # 单元测试 (pytest)
├── frontend/
│   └── word-addin/             # Word 加载项 (HTML/JS/Office.js)
│       ├── manifest.xml        # Office 加载项清单
│       ├── index.html          # 任务窗格入口
│       ├── main.js             # 插件主逻辑
│       ├── api.js              # API 客户端
│       ├── panels/             # 面板组件 (history/diff/preview/rollback)
│       ├── styles/             # CSS 样式
│       └── assets/             # 图标资源
├── docs/
│   └── mcp.md                  # MCP 服务器详细文档
└── scripts/                    # 安装/构建/启动脚本
    ├── start_backend.bat       # 启动后端
    ├── install_addin.bat       # 安装 Word 加载项
    ├── install_mcp.bat         # 安装 MCP 服务器依赖
    ├── build_exe.bat           # 打包为独立 exe
    ├── gen_cert.bat            # 生成 SSL 证书
    ├── sideload.bat            # 侧载加载项
    └── e2e_test.py             # 端到端测试
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 文档解析 | `python-docx`, `lxml` | 提取 OOXML 文本内容 |
| 差异引擎 | `diff-match-patch` (Google) | 词级精确对比 |
| 后端框架 | FastAPI + Uvicorn | REST API + HTTPS |
| Git 操作 | `git` CLI (subprocess) | 版本控制核心 |
| 插件前端 | HTML5, CSS3, JS (IIFE) | 零依赖轻量前端 |
| Office 集成 | Office.js API | Word 加载项通信 |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/status` | 健康检查 |
| `POST` | `/api/init` | 初始化文档仓库 |
| `POST` | `/api/commit` | 手动提交版本 |
| `GET` | `/api/history` | 版本历史列表 |
| `GET` | `/api/diff` | 版本差异对比 |
| `POST` | `/api/rollback` | 回滚到指定版本 |
| `GET` | `/api/preview` | 版本内容预览 |
| `POST` | `/api/shutdown` | 关闭后端 |

## 文档存储说明

GitDoc 在每个文档同级目录创建 `.gitdoc/` 隐藏文件夹：

```
论文.docx                  ← Word 编辑的文件
.gitdoc/
  ├── .git/                ← Git 仓库（文档完整二进制历史）
  ├── cache/               ← 文本提取缓存 (JSON)
  ├── backups/             ← 回滚前安全备份 (.docx)
  └── gitdoc.config.json   ← 文档级配置
```

## 后续迭代

- **第二阶段：本地多人协作** — 分支（评审分支）、本地 PR、冲突解决 UI
- **第三阶段：远程协作** — 协作服务器、远程 PR、Web 端审阅

## 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。
