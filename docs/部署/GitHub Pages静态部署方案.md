# GitHub Pages 静态部署方案

更新日期：2026-06-14

本文档用于将空空如也GameHub 发布为 GitHub Pages 静态站点。该方案不需要信用卡，也不运行 Python 后端。

## 1. 方案结论

```text
GitHub Pages
GitHub Actions
发布 frontend 目录
SQLite 数据库导出为 frontend/public/game-data.js
```

发布后的地址通常为：

```text
https://jackywujun1983.github.io/kongkong-game-demo/
```

## 2. 静态版能力边界

| 项目 | GitHub Pages 静态版 |
| --- | --- |
| 是否免费 | 免费 |
| 是否需要后端 | 不需要 |
| 是否支持 SQLite 运行时查询 | 不支持 |
| 数据来源 | 构建时导出的 `game-data.js` |
| 是否支持用户注册/论坛写入 | 不支持 |
| 国内访问 | 仍是境外服务，不保证所有网络稳定 |

## 3. 本次静态发布范围

本项目当前采用“静态页面 + 构建时导出数据”的发布方式。本次发布需要包含：

| 类型 | 文件或目录 | 说明 |
| --- | --- | --- |
| 页面入口 | `frontend/index.html`、`frontend/preview.html`、`frontend/detail.html` | GitHub Pages 实际访问页面 |
| 页面样式 | `frontend/public/site.css` | 当前最终 UI 风格 |
| 默认封面 | `frontend/public/assets/covers/default-game-cover.jpg` | 无封面或图片加载失败时的兜底图 |
| 静态数据 | `frontend/public/game-data.js` | API 不可用时首页和详情页读取的数据 |
| 数据源 | `backend/gamehub.sqlite3` | GitHub Actions 导出静态数据时读取的 SQLite 文件 |
| 导出脚本 | `tools/export_static_game_data.py` | 构建时生成 `game-data.js` |
| 工作流 | `.github/workflows/github-pages.yml` | 自动发布到 GitHub Pages |
| 部署文档 | `docs/部署/GitHub Pages静态部署方案.md` | 当前部署方案说明 |

以下内容不应作为正式静态站点发布内容：

- `frontend/*-preview.png`
- `frontend/static-server.*.log`
- `frontend/ui-prototype.html`
- `frontend/fresh-ui-prototype.html`
- `backend/*.bak-*`

## 4. 项目内已准备内容

### 4.1 静态数据导出脚本

```text
tools/export_static_game_data.py
```

作用：

- 读取 `backend/gamehub.sqlite3`。
- 导出可见分类。
- 导出全部游戏、详情、分类、下载地址、游戏大小和封面地址。
- 写入 `frontend/public/game-data.js`。

本地手动执行：

```cmd
python tools\export_static_game_data.py
```

### 4.2 GitHub Pages 工作流

```text
.github/workflows/github-pages.yml
```

作用：

- 每次推送 `main` 分支时自动运行。
- 也支持在 GitHub Actions 页面手动点击 `Run workflow`。
- 使用 Python 导出静态游戏数据。
- 只上传 `frontend` 目录作为 GitHub Pages 站点。
- 不发布 `backend`、`tools`、SQLite 原始数据库等项目文件。
- `frontend/public/assets/covers/default-game-cover.jpg` 会随静态站点一起发布，用于无封面或图片加载失败的兜底展示。

### 4.3 静态站点入口

```text
frontend/index.html
```

作用：

- GitHub Pages 打开根路径时自动进入 `preview.html`。

### 4.4 一键发布脚本

根目录入口：

```text
publish_static_site.cmd
publish_site.cmd
```

实际发布脚本：

```text
tools/publish_ui_update.cmd
```

作用：

- 暂存已跟踪的项目改动。
- 暂存正式页面、样式、文档、默认封面、静态数据和发布脚本。
- 提交当前 UI 更新。
- 推送到 `origin main`。
- 不主动提交截图、日志和原型临时文件。

## 5. 本地验证

先生成静态数据：

```cmd
python tools\export_static_game_data.py
```

确认文件存在：

```text
frontend/public/game-data.js
```

静态版页面会优先尝试访问 `/api`，在 GitHub Pages 上 API 不存在时自动切换到 `game-data.js` 本地兜底数据。

本地站点验证：

```cmd
启动站点.cmd
```

访问：

```text
http://127.0.0.1:8000/
```

## 6. 推送到 GitHub

推荐执行：

```cmd
cd /d E:\Codex_Space\PythonDemo && publish_static_site.cmd
```

如需自定义提交信息，可直接调用：

```cmd
cd /d E:\Codex_Space\PythonDemo && tools\publish_ui_update.cmd "Deploy GameHub static site"
```

如果只想手动执行 Git 命令，可按顺序运行：

```cmd
cd /d E:\Codex_Space\PythonDemo
python tools\export_static_game_data.py
git add -u -- .
git add .github\workflows\github-pages.yml publish_static_site.cmd publish_site.cmd tools\publish_ui_update.cmd backend\gamehub.sqlite3 frontend\public\game-data.js docs
git commit -m "Deploy GameHub static site"
git push origin main
```

## 7. 启用 GitHub Pages

进入 GitHub 仓库：

```text
https://github.com/Jackywujun1983/kongkong-game-demo
```

操作步骤：

1. 点击 `Settings`。
2. 左侧点击 `Pages`。
3. 在 `Build and deployment` 中找到 `Source`。
4. 选择 `GitHub Actions`。
5. 保存。

同时进入：

```text
Settings -> Actions -> General
```

确认：

- `Actions permissions` 允许运行 GitHub Actions。
- `Workflow permissions` 选择 `Read and write permissions`。

如果 `Workflow permissions` 不是写权限，部署阶段可能出现：

```text
HttpError: Requires authentication
401
```

## 8. 查看部署进度

进入仓库：

```text
Actions
```

找到工作流：

```text
Deploy Static Site to GitHub Pages
```

等待状态变成绿色成功。

状态含义：

| 状态 | 含义 |
| --- | --- |
| 绿色对勾 | 部署完成，可以访问最新页面 |
| 黄色圆点或转圈 | 正在构建或部署 |
| 红色叉 | 部署失败，需要点进去查看失败步骤 |

如果 `build` 成功但 `deploy` 失败，并出现 `401 Requires authentication`，优先检查第 7 节中的 `Workflow permissions`。

## 9. 访问地址

部署完成后访问：

```text
https://jackywujun1983.github.io/kongkong-game-demo/
```

如果页面没有立即出现，等待 1 到 3 分钟后刷新。

如果页面仍然显示旧样式：

- 先确认 Actions 最新一条是绿色。
- 使用带版本号的访问地址，例如 `preview.html?v=latest`。
- 浏览器执行强制刷新：`Ctrl + F5`。
- 当前静态页的 CSS 和默认封面引用已带资源版本号，用于减少 GitHub Pages/CDN 缓存影响。

## 10. 后续更新数据

当 SQLite 数据库更新后，重新导出静态数据并推送：

```cmd
python tools\export_static_game_data.py
git add frontend/public/game-data.js
git commit -m "Update static game data"
git push
```

GitHub Actions 会自动重新发布。

当前 UI 或文档更新，推荐直接执行：

```cmd
publish_static_site.cmd
```

## 11. 注意事项

- GitHub Pages 只能发布静态页面，不能运行 Python。
- `/api/health`、`/api/games` 等接口在 GitHub Pages 上不可用。
- 当前首页和详情页会在 API 不可用时使用 `frontend/public/game-data.js`。
- 当前默认封面图片属于静态资源，可以直接随 GitHub Pages 发布。
- GitHub Actions 会重新生成 `frontend/public/game-data.js`，因此 `backend/gamehub.sqlite3` 也必须随数据更新一起提交。
- 如果后续要恢复用户注册、论坛、后台写入等功能，需要重新部署后端服务。
