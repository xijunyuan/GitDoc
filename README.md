# GitDoc 安装与使用指南

> **GitDoc** — 基于 Git 的 Word 文档版本控制工具。自动记录每次保存，支持差异对比、一键回滚，无需学习 Git。

---

## 一、安装步骤

### 1. 安装 Git for Windows

- 下载地址：https://git-scm.com/download/win
- 安装到 `D:\Git\`（或其他路径）

### 2. 克隆 GitDoc 项目

```bash
git clone https://github.com/xijunyuan/GitDoc.git
```

### 3. 安装 Python 依赖

```bash
cd GitDoc\backend
pip install -r requirements.txt
```

> 需要 Python 3.10+，依赖包括：FastAPI、GitPython、python-docx、diff-match-patch、watchdog 等。

### 4. 生成 SSL 证书（只需一次）

双击 `scripts\gen_cert.bat`，弹出 UAC 窗口点「是」。

> 如果证书是 DER 格式导致后端启动失败，需要手动重新生成为 PEM 格式（见文末附录）。

### 5. 信任 SSL 证书（只需一次）

如果 `gen_cert.bat` 没有自动信任证书，手动执行：

```powershell
certutil -addstore -user "Root" "scripts\certs\localhost.crt"
```

---

## 二、启动后端（每次使用前）

双击 `scripts\start_backend.bat`，看到以下输出表示成功：

```
GitDoc Backend v0.1.0
Frontend:  https://localhost:18521
Port:      http://127.0.0.1:18521
```

**不要关掉这个窗口！** 让它一直在后台运行。

> 备用手动启动：
> ```bash
> cd backend
> python main.py
> ```

---

## 三、使用方式

### 方式 A：浏览器端（推荐，所有 Office 版本通用）

1. 打开浏览器（Chrome / Edge），访问：
   ```
   https://localhost:18521/
   ```

2. 首次访问会提示「连接不是私密连接」，点击 **「高级」→「继续前往」**

3. 在输入框中填入 `.docx` 文件的**完整路径**，例如：
   ```
   C:\Users\lenovo\Desktop\报告\Chap8-10.docx
   ```

4. 随后在 Word 中正常编辑文档，每次 `Ctrl+S` 保存时，GitDoc 会自动记录一个新版本

5. 在浏览器界面可以：
   - 📋 查看所有版本历史（时间轴）
   - 🔍 对比任意两个版本的差异（词级高亮：绿增红删）
   - ⏪ 一键回滚到任意历史版本
   - 👁 预览历史版本内容

### 方式 B：Word 内置加载项（需要 Office 支持侧载）

> ⚠️ Office 365 家庭版可能不支持此方式，请使用方式 A。

1. 双击 `scripts\install_addin.bat`
2. 打开 Word，**插入 → 我的加载项 → 共享文件夹**
3. 选择 **「GitDoc - 文档版本管理」** → **「添加」**
4. Word 右侧出现 GitDoc 面板，打开任意 `.docx` 文件即可使用

---

## 四、重要注意事项

### 文件格式

| 格式 | 版本控制 | 文本对比 | 回滚 |
|------|:--:|:--:|:--:|
| `.docx`（Word 2007+） | ✅ | ✅ | ✅ |
| `.doc`（Word 97-2003） | ✅ | ❌ | ✅ |

> **强烈建议使用 `.docx` 格式**。如果是 `.doc` 文件，请在 Word 中「另存为」`.docx` 格式。

### 路径说明

- 路径中包含中文、空格均支持，无需转义
- 路径格式示例：`C:\Users\用户名\Desktop\文件夹\文档.docx`

### 存储说明

GitDoc 在文档同级目录创建 `.gitdoc/` 隐藏文件夹：

```
文档.docx
.gitdoc/
  ├── .git/         ← Git 仓库（完整历史）
  ├── cache/        ← 文本缓存
  ├── backups/      ← 回滚前安全备份
  └── .gitignore
```

- 删除 `.gitdoc/` 文件夹会**丢失所有历史版本**
- `.gitdoc/` 会自动被 Git 忽略，不会影响项目仓库

---

## 五、常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 后端无法启动 | 端口 18521 被占用 | 关闭其他 GitDoc 实例 |
| 后端启动报 SSL 错误 | 证书格式不匹配 | 重新生成 PEM 格式证书（见附录） |
| 页面报「Git 未安装」 | 后端进程的 PATH 里没有 Git | 确保 Git 在系统 PATH 中，重启后端 |
| 保存后无版本记录 | 后端刚重启需重新初始化 | 刷新页面，重新输入文档路径 |
| 差异对比不显示 | 只有 `.docx` 支持文本对比 | 将 `.doc` 另存为 `.docx` |
| 页面无法连接 | 后端未启动 | 双击 `start_backend.bat` |

### 快速自检

```powershell
# 检查后端是否在运行
python -c "import urllib.request; print(urllib.request.urlopen('https://127.0.0.1:18521/api/status').read())"

# 检查 Git 是否可用
git --version
```

---

## 六、命令行接口

除了浏览器界面，也可以直接调用 API：

| 操作 | API |
|------|-----|
| 初始化 | `POST /api/init` |
| 手动提交 | `POST /api/commit` |
| 版本历史 | `GET /api/history?docx_path=<路径>` |
| 差异对比 | `GET /api/diff?from_hash=&to_hash=&docx_path=` |
| 版本回滚 | `POST /api/rollback` |
| 内容预览 | `GET /api/preview?commit_hash=&docx_path=` |
| 健康检查 | `GET /api/status` |

---

## 附录：手动生成 PEM 格式 SSL 证书

如果 `gen_cert.bat` 生成的证书不可用，用 Python 重新生成：

```python
from cryptography import x509, hazmat
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime, ipaddress

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

with open('localhost.key', 'wb') as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
cert = x509.CertificateBuilder() \
    .subject_name(subject).issuer_name(issuer) \
    .public_key(key.public_key()) \
    .serial_number(x509.random_serial_number()) \
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc)) \
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)) \
    .add_extension(x509.SubjectAlternativeName([
        x509.DNSName('localhost'),
        x509.IPAddress(ipaddress.IPv4Address('127.0.0.1'))
    ]), critical=False) \
    .sign(key, hashes.SHA256())

with open('localhost.crt', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

# 信任证书
# certutil -addstore -user "Root" localhost.crt
```
