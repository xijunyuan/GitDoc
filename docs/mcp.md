# GitDoc MCP Server

让 AI 编程助手（Claude Code、Cursor、GitHub Copilot 等）直接读取、对比和分析 Word 文档。

## 是什么

MCP（Model Context Protocol）是 AI 助手与外部工具之间的标准通信协议。GitDoc MCP Server 将 GitDoc 的文档解析、词级差异对比和版本管理能力封装为 MCP 工具，使 AI 可以：

- 读取 `.docx` 文件的结构化文本内容
- 对比同一文档不同 Git 版本之间的词级差异
- 查看文档的提交历史
- 对比任意两个 `.docx` 文件的差异

## 系统要求

- Python 3.10+
- Git for Windows（Git 相关工具需要）
- 已安装 GitDoc 后端依赖（`pip install -r backend/requirements.txt`）

## 安装

### 方式一：一键安装（推荐）

双击运行 **`scripts\install_mcp.bat`**，自动检测 Python 环境并安装 MCP 依赖。

### 方式二：手动安装

```bash
cd backend
pip install -r requirements.txt
```

核心 MCP 依赖：`mcp>=1.13.0`

## 配置

GitDoc MCP Server 支持两种传输模式：**stdio**（本地使用）和 **HTTP**（远程/团队使用）。

### Claude Code

在项目目录下执行：

```bash
claude mcp add gitdoc -- python f:/GitDoc/backend/mcp_server.py
```

之后在 Claude Code 中可以直接调用 GitDoc 工具。

### Claude Desktop

编辑配置文件 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "gitdoc": {
      "command": "python",
      "args": ["f:\\GitDoc\\backend\\mcp_server.py"]
    }
  }
}
```

### Cursor

在 Cursor 设置中添加 MCP Server，命令为：

```
python f:\GitDoc\backend\mcp_server.py
```

### 其他 MCP 客户端

任何支持 MCP 协议的客户端都可以通过 stdio 连接：

```bash
python backend/mcp_server.py
```

或通过 HTTP 连接（先启动服务）：

```bash
python backend/mcp_server.py --transport http
# 服务启动在 http://127.0.0.1:18522/mcp
```

## 工具参考

### read_docx

解析任意 `.docx` 文件，返回结构化文本内容。

```
参数:
  path: string — .docx 文件的绝对路径

返回:
  path:        文件路径
  block_count: 内容块数量
  blocks:      结构化块列表 [{ type, text, index, style }, ...]
  full_text:   拼接后的完整纯文本
```

**不需要 Git 仓库**，可以对任何 `.docx` 文件使用。

### get_history

获取已追踪文档的 Git 提交历史。

```
参数:
  docx_path:  string — 文档绝对路径
  max_count:  int (默认 50) — 最大返回条数

返回:
  docx_path:   文档路径
  total_count: 提交总数
  commits:     [{ hash, short_hash, author, timestamp, message }, ...]
```

需要文档已被 GitDoc 初始化（存在 `.gitdoc/.git`）。

### diff_versions

对比同一文档的两个 Git 版本，返回词级差异。

```
参数:
  docx_path:  string — 文档绝对路径
  from_hash:  string — 旧版本 commit hash（支持短 hash）
  to_hash:    string — 新版本 commit hash（支持短 hash）

返回:
  from_hash:  旧版本完整 hash
  to_hash:    新版本完整 hash
  blocks:     [{ block_index, block_type, segments: [{ operation, text }] }]
  stats:      { insertions, deletions, equal }
```

operation: `"insert"`（新增）、`"delete"`（删除）、`"equal"`（未变）

### preview_version

获取文档在某个 Git 版本时的纯文本内容。

```
参数:
  docx_path:   string — 文档绝对路径
  commit_hash: string — 要预览的 commit hash

返回:
  hash:        完整 commit hash
  text:        纯文本内容
  block_count: 内容块数量
```

### diff_files

对比任意两个 `.docx` 文件，返回词级差异。

```
参数:
  file1: string — 旧文件绝对路径
  file2: string — 新文件绝对路径

返回:
  file1:  旧文件路径
  file2:  新文件路径
  blocks: [{ block_index, block_type, segments: [{ operation, text }] }]
  stats:  { insertions, deletions, equal }
```

**不需要 Git 仓库**，可以对比任意两个 Word 文件。

## 使用场景

### 场景一：AI 读需求文档写代码

```
用户: 读一下 docs/PRD_v2.docx，根据第三章的接口定义写对应的 TypeScript 类型

Claude: [调用 read_docx] → 提取第三章内容 → 生成类型定义
```

### 场景二：自动追踪文档变更

```
用户: 产品经理更新了需求文档，帮我看看改了哪些地方

Claude: [调用 get_history] → [调用 diff_versions] 
→ "v3 版本相比 v2：第三章新增了 phone 字段，第四章删除了 status 枚举值"
```

### 场景三：文档审查

```
用户: 对比合同初稿和终稿，列出所有实质性修改

Claude: [调用 diff_files] → 逐段展示增删改 → 生成变更摘要
```

### 场景四：CI/CD 文档门禁

在 GitHub Actions 中使用 HTTP 模式：

```yaml
- name: Check Doc Changes
  run: |
    python backend/mcp_server.py --transport http &
    sleep 2
    # 对比 PR 中的文档变更并生成评论
```

## 故障排除

### `pip install mcp` 失败

确保 Python 版本 ≥ 3.10：
```bash
python --version
```

### MCP 连接失败（stdio 模式）

检查 GitDoc 后端依赖是否完整安装：
```bash
cd backend
pip install -r requirements.txt
python -c "from mcp_server import mcp; print('OK')"
```

### Git 工具返回 "No GitDoc repository"

需要先用 GitDoc Word Add-in 初始化文档仓库（在 Word 中打开文档后会自动初始化），或调用 GitDoc REST API：
```
POST http://127.0.0.1:18521/api/init
Body: { "docx_path": "C:\\path\\to\\document.docx" }
```

### HTTP 模式端口被占用

默认端口 18522，如需修改，编辑 `backend/mcp_server.py` 中 `FastMCP` 构造函数的 `port` 参数。

### 文件路径格式

Windows 下请使用正斜杠或双反斜杠：
- ✅ `f:/GitDoc/docs/doc.docx`
- ✅ `f:\\GitDoc\\docs\\doc.docx`
- ❌ `f:\GitDoc\docs\doc.docx`（反斜杠会被转义）
