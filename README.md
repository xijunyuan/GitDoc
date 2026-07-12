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
- Git for Windows

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xijunyuan/GitDoc.git
cd GitDoc
```

### 2. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端

```bash
# Windows
scripts\start_backend.bat

# 或手动启动
cd backend
python main.py
```

后端启动后监听 `https://localhost:18521`，API 文档见 `https://localhost:18521/docs`。

> 提示：首次启动会自动使用自签名证书启用 HTTPS。如需使用 HTTP，加 `--http` 参数。

### 4. 安装 Word 加载项

在 Word 中：
1. 启用开发人员模式（文件 → 选项 → 自定义功能区 → 勾选"开发工具"）
2. 运行 `scripts\install_addin.bat`
3. 打开 Word → 插入 → 我的加载项 → 共享文件夹
4. 选择 "GitDoc - 文档版本管理"

### 5. 开始使用

1. 打开任意 `.docx` 文件
2. 在 Word 右侧任务窗格中可见 GitDoc 面板
3. 编辑并保存文档，版本历史自动更新
4. 点击版本旁的"对比"查看差异，点击"回滚"恢复历史版本

## 项目结构

```
GitDoc/
├── backend/                    # Python 后端 (FastAPI)
│   ├── main.py                 # 服务入口
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
└── scripts/                    # 安装/构建/启动脚本
    ├── start_backend.bat       # 启动后端
    ├── install_addin.bat       # 安装 Word 加载项
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
