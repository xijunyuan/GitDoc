# GitDoc — 文档版本管理系统

基于 Git 的 Word 文档版本控制工具，为课题组和工程项目部提供代码级版本管理能力，无需学习 Git。

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

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/gitdoc/gitdoc.git
cd gitdoc

# 安装 Python 依赖
cd backend
pip install -r requirements.txt
```

### 2. 启动后端

```bash
# Windows
scripts\start_backend.bat

# 或手动启动
cd backend
python main.py
```

后端启动后监听 `http://127.0.0.1:18521`，API 文档见 `http://127.0.0.1:18521/docs`。

### 3. 安装 Word 加载项

在 Word 中：
1. 启用开发人员模式（文件 → 选项 → 自定义功能区 → 勾选"开发工具"）
2. 运行 `scripts\install_addin.bat`
3. 打开 Word → 插入 → 我的加载项 → 共享文件夹
4. 选择 "GitDoc - 文档版本管理"

### 4. 使用

1. 打开任意 .docx 文件
2. 在 Word 右侧任务窗格中可见 GitDoc 面板
3. 编辑并保存文档，版本历史自动更新
4. 点击版本旁的"对比"可查看差异，点击"回滚"可恢复

## 项目结构

```
GitDoc/
├── backend/                  # Python 后端 (FastAPI)
│   ├── main.py               # 服务入口
│   ├── git_operations.py     # Git 操作封装
│   ├── docx_parser.py        # OOXML 文档解析
│   ├── diff_engine.py        # 词级差异引擎
│   ├── commit_manager.py     # 提交管理器
│   ├── rollback_manager.py   # 回滚管理器
│   ├── file_watcher.py       # 文件监听器
│   └── tests/                # 单元测试
├── frontend/
│   └── word-addin/           # Word 加载项 (HTML/JS)
│       ├── manifest.xml      # Office 加载项清单
│       ├── index.html        # 任务窗格入口
│       ├── main.js           # 插件核心
│       ├── api.js            # API 客户端
│       ├── panels/           # 面板组件
│       └── styles/           # CSS 样式
└── scripts/                  # 安装/构建/启动脚本
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 文档解析 | Python, `python-docx`, `lxml` |
| 差异引擎 | `diff-match-patch` (Google) |
| 后端框架 | FastAPI + Uvicorn |
| Git 操作 | Git CLI (subprocess) |
| 插件前端 | HTML5, CSS3, JavaScript (IIFE) |
| Office 集成 | Office.js API |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/status` | 健康检查 |
| POST | `/api/init` | 初始化文档仓库 |
| POST | `/api/commit` | 手动提交版本 |
| GET | `/api/history` | 版本历史列表 |
| GET | `/api/diff` | 版本差异对比 |
| POST | `/api/rollback` | 回滚到指定版本 |
| GET | `/api/preview` | 版本内容预览 |
| POST | `/api/shutdown` | 关闭后端 |

## 文档存储说明

GitDoc 在每个文档同级目录创建 `.gitdoc/` 隐藏文件夹：

```
论文.docx                ← Word 编辑的文件
.gitdoc/
  ├── .git/              ← Git 仓库 (文档完整二进制历史)
  ├── cache/             ← 文本提取缓存 (JSON)
  ├── backups/           ← 回滚前安全备份 (.docx)
  └── config.json        ← 文档级配置
```

## 许可证

MIT License
