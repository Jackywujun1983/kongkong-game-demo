# GitHub Pages 静态部署方案

本文档用于将空空如也GameHub 发布为 GitHub Pages 静态站点。该方案不需要 Render，不需要信用卡，也不运行 Python 后端。

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

## 2. 静态版和 Render 版的区别

| 项目 | GitHub Pages 静态版 | Render 版 |
| --- | --- | --- |
| 是否免费 | 免费 | 免费但可能要求绑卡验证 |
| 是否需要后端 | 不需要 | 需要 Python 服务 |
| 是否支持 SQLite 运行时查询 | 不支持 | 支持 |
| 数据来源 | 构建时导出的 `game-data.js` | `backend/gamehub.sqlite3` |
| 是否支持用户注册/论坛写入 | 不支持 | 可扩展 |
| 国内访问 | 通常比 Render 更容易打开，但仍是境外服务 | 不稳定 |

## 3. 项目内已准备内容

### 3.1 静态数据导出脚本

```text
tools/export_static_game_data.py
```

作用：

- 读取 `backend/gamehub.sqlite3`。
- 导出可见分类。
- 导出全部游戏、详情、分类、下载地址。
- 写入 `frontend/public/game-data.js`。

本地手动执行：

```bash
python tools/export_static_game_data.py
```

### 3.2 GitHub Pages 工作流

```text
.github/workflows/github-pages.yml
```

作用：

- 每次推送 `main` 分支时自动运行。
- 使用 Python 导出静态游戏数据。
- 只上传 `frontend` 目录作为 GitHub Pages 站点。
- 不发布 `backend`、`tools`、SQLite 原始数据库等项目文件。

### 3.3 静态站点入口

```text
frontend/index.html
```

作用：

- GitHub Pages 打开根路径时自动进入 `preview.html`。

## 4. 本地验证

先生成静态数据：

```bash
python tools/export_static_game_data.py
```

确认文件存在：

```text
frontend/public/game-data.js
```

静态版页面会优先尝试访问 `/api`，在 GitHub Pages 上 API 不存在时自动切换到 `game-data.js` 本地兜底数据。

## 5. 推送到 GitHub

执行：

```bash
git add .
git commit -m "Add GitHub Pages static deployment"
git push
```

## 6. 启用 GitHub Pages

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

## 7. 查看部署进度

进入仓库：

```text
Actions
```

找到工作流：

```text
Deploy Static Site to GitHub Pages
```

等待状态变成绿色成功。

## 8. 访问地址

部署完成后访问：

```text
https://jackywujun1983.github.io/kongkong-game-demo/
```

如果页面没有立即出现，等待 1 到 3 分钟后刷新。

## 9. 后续更新数据

当 SQLite 数据库更新后，重新导出静态数据并推送：

```bash
python tools/export_static_game_data.py
git add frontend/public/game-data.js
git commit -m "Update static game data"
git push
```

GitHub Actions 会自动重新发布。

## 10. 注意事项

- GitHub Pages 只能发布静态页面，不能运行 Python。
- `/api/health`、`/api/games` 等接口在 GitHub Pages 上不可用。
- 当前首页和详情页会在 API 不可用时使用 `frontend/public/game-data.js`。
- 如果后续要恢复用户注册、论坛、后台写入等功能，需要重新部署后端服务。
