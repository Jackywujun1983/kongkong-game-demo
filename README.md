# 空空如也GameHub 游戏信息检索网站

空空如也GameHub 是一个前后端分离源码组织的游戏信息检索网站，当前聚焦游戏检索、分类筛选、游戏列表、分页和详情页展示。广告数据能力在后端保留为预留接口，当前前端不展示广告布局。

本地默认使用一个 Python 服务同时托管前端页面和后端 API，降低启动成本。

## 技术架构

```text
空空如也GameHub
├── backend/   Python HTTP API + SQLite
├── frontend/  静态页面 + React/Vite 工程源码
├── docs/      需求、技术、数据库和页面布局文档
└── tools/     数据导入和本地资源生成脚本
```

## 项目文档

- `docs/需求文档.md`
- `docs/技术文档.md`
- `docs/数据库设计文档.md`
- `docs/前端页面布局文档.md`
- `docs/游戏类型枚举文档.md`
- `docs/部署/Render Free部署方案.md`
- `docs/部署/GitHub Pages静态部署方案.md`
- `docs/规范/Python编码规范.md`
- `docs/规范/前端主流开发框架规范.md`
- `docs/规范/测试规范.md`

## 本地运行

推荐方式：

```bash
启动站点.cmd
```

或：

```bash
tools\run_site.cmd
```

访问地址：

```text
http://127.0.0.1:8000/
```

后端健康检查：

```text
http://127.0.0.1:8000/api/health
```

## 测试

```bash
cd backend
python -m unittest discover -s tests
```

## 规范约束

本项目必须遵守：

- `docs/规范/Python编码规范.md`
- `docs/规范/前端主流开发框架规范.md`
- `docs/规范/测试规范.md`
- `AGENTS.md`
