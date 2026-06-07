# Render Free 部署方案

本文档用于将空空如也GameHub 部署到 Render Free。当前方案使用一个 Python Web Service 同时托管前端静态页面和后端 API，SQLite 数据库文件随代码发布。

## 1. 方案结论

```text
Render Free Web Service
Python Runtime
backend/main.py
frontend 静态页面由后端服务托管
SQLite 数据库：backend/gamehub.sqlite3
```

访问入口：

```text
https://你的服务名.onrender.com/
```

API 示例：

```text
https://你的服务名.onrender.com/api/health
https://你的服务名.onrender.com/api/games?page=1&page_size=48
https://你的服务名.onrender.com/api/categories
```

## 2. 前提准备

- 一个 GitHub 账号。
- 一个 Render 账号。
- 项目代码已推送到 GitHub。
- `backend/gamehub.sqlite3` 必须提交到仓库，因为线上游戏数据来自该文件。
- 当前项目不需要安装第三方 Python 包，使用 Python 标准库即可运行。

## 3. 项目内已准备的部署配置

仓库根目录提供 `render.yaml`：

```yaml
services:
  - type: web
    name: kongkong-gamehub
    runtime: python
    plan: free
    buildCommand: python --version
    startCommand: python backend/main.py --host 0.0.0.0 --port $PORT --database backend/gamehub.sqlite3
    healthCheckPath: /api/health
```

关键点：

- `--host 0.0.0.0`：云服务必须监听外部地址。
- `--port $PORT`：Render 会注入运行端口。
- `--database backend/gamehub.sqlite3`：使用随仓库发布的 SQLite 数据库。
- `/api/health`：健康检查路径。

## 4. GitHub 提交前检查

确认主数据库没有被忽略：

```bash
git status --short backend/gamehub.sqlite3
```

如果输出中能看到 `backend/gamehub.sqlite3`，说明可以提交。

提交部署相关文件：

```bash
git add .gitignore render.yaml backend/gamehub.sqlite3 docs/部署/Render\ Free部署方案.md
git commit -m "Add Render Free deployment config"
git push
```

Windows PowerShell 如果路径转义不方便，可以直接使用：

```powershell
git add .gitignore render.yaml backend/gamehub.sqlite3 "docs/部署/Render Free部署方案.md"
git commit -m "Add Render Free deployment config"
git push
```

## 5. Render 创建服务

方式一：使用 Blueprint。

1. 登录 Render。
2. 点击 `New`。
3. 选择 `Blueprint`。
4. 连接 GitHub 仓库。
5. 选择包含 `render.yaml` 的仓库。
6. Render 会读取配置并创建 `kongkong-gamehub` 服务。
7. 确认套餐为 `Free`。
8. 点击部署。

方式二：手动创建 Web Service。

1. 登录 Render。
2. 点击 `New`。
3. 选择 `Web Service`。
4. 连接 GitHub 仓库。
5. Runtime 选择 `Python`。
6. Instance Type 选择 `Free`。
7. Build Command 填：

```bash
python --version
```

8. Start Command 填：

```bash
python backend/main.py --host 0.0.0.0 --port $PORT --database backend/gamehub.sqlite3
```

9. Health Check Path 填：

```text
/api/health
```

10. 点击部署。

## 6. 部署后验证

部署成功后，Render 会给出类似地址：

```text
https://kongkong-gamehub.onrender.com
```

依次验证：

```text
/
/api/health
/api/categories
/api/games?page=1&page_size=5
```

预期结果：

- `/` 可以打开首页。
- `/api/health` 返回 `{"status":"ok","service":"gamehub-api"}`。
- `/api/categories` 返回分类列表，并包含 `game_count`。
- `/api/games` 返回游戏分页列表。

## 7. Render Free 限制

- 空闲一段时间后服务会休眠，首次访问会变慢。
- 免费服务不适合正式生产环境。
- 本地运行时写入的文件不持久，重启或重新部署后可能丢失。
- 当前 SQLite 数据库适合作为随代码发布的只读数据源。
- 如果后续增加用户注册、论坛、后台写入等功能，需要升级到持久数据库。

## 8. 后续更新流程

本地修改代码或数据后：

```bash
python backend/main.py --host 127.0.0.1 --port 8000
```

本地验证：

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/api/health
```

运行测试：

```bash
cd backend
python -m unittest discover -s tests
```

提交并推送：

```bash
git add .
git commit -m "Update gamehub"
git push
```

Render 会根据仓库设置自动重新部署。

## 9. 后续升级建议

当项目需要长期稳定运行时，建议升级为：

```text
Render Paid Web Service
PostgreSQL
对象存储保存图片或附件
独立域名
```

如果主要面向中国大陆用户，Render 仅建议作为临时演示环境，正式部署仍建议使用国内云服务器。
