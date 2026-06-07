# 空空如也GameHub Backend

Python 标准库实现的 REST API，使用 SQLite 存储游戏、分类、多类型关系和广告位预留数据。

账户注册、登录会话、论坛帖子和论坛评论模块已移除。

## 启动

```bash
python backend/main.py
```

前端页面：

```text
http://127.0.0.1:8000/
```

API 地址：

```text
http://127.0.0.1:8000/api
```

## 核心接口

- `GET /api/health`
- `GET /api/categories`
- `GET /api/games?query=&category=&page=&page_size=`
- `GET /api/games/{slug}`
- `GET /api/ads?placement=`

## 已移除接口

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/me`
- `GET /api/forum/posts`
- `POST /api/forum/posts`
- `GET /api/forum/posts/{id}`
- `POST /api/forum/posts/{id}/comments`

## 测试

```bash
cd backend
python -m unittest discover -s tests
```
