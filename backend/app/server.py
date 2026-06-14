"""空空如也 GameHub REST API 的 HTTP 服务。"""

from __future__ import annotations

import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from app.config import DATABASE_PATH, DEFAULT_HOST, DEFAULT_PORT, FRONTEND_DIR, PIC_DIR
from app.database import initialize_database
from app.repositories import (
    get_game,
    list_ads,
    list_categories,
    search_games,
)


class GameHubRequestHandler(BaseHTTPRequestHandler):
    """实现空空如也 GameHub API 的请求处理器。"""

    database_path: Path = DATABASE_PATH
    frontend_dir: Path = FRONTEND_DIR
    pic_dir: Path = PIC_DIR

    def do_OPTIONS(self) -> None:
        """返回 CORS 预检请求响应头。"""
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:
        """处理只读 API 和前端静态资源请求。"""
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        query = parse_qs(parsed_url.query)

        if route == "/":
            self._send_frontend_file("/preview.html")
            return

        if route.startswith("/pic/"):
            self._send_pic_file(route)
            return

        if not route.startswith("/api/"):
            self._send_frontend_file(route)
            return

        if route == "/api/health":
            self._send_json({"status": "ok", "service": "gamehub-api"})
            return

        if route == "/api/categories":
            self._send_json({"items": list_categories(self.database_path)})
            return

        if route == "/api/games":
            self._send_json(
                search_games(
                    query=_first_query_value(query, "query"),
                    category=_query_values(query, "category"),
                    page=_safe_int(_first_query_value(query, "page"), 1),
                    page_size=_safe_int(
                        _first_query_value(query, "page_size"),
                        12,
                    ),
                    database_path=self.database_path,
                )
            )
            return

        game_match = re.fullmatch(r"/api/games/([\w-]+)", route)
        if game_match:
            game = get_game(game_match.group(1), self.database_path)
            if game is None:
                self._send_error("Game not found", HTTPStatus.NOT_FOUND)
                return
            self._send_json(game)
            return

        if route == "/api/ads":
            self._send_json(
                {
                    "items": list_ads(
                        placement=_first_query_value(query, "placement"),
                        database_path=self.database_path,
                    )
                }
            )
            return

        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        """处理写入类 API；当前项目暂未开放写入端点。"""
        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        """关闭默认访问日志，减少开发终端噪音。"""
        return

    def _send_json(
        self,
        payload: dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(
        self,
        message: str,
        status: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> None:
        self._send_json({"error": message}, status)

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status.value)
        self._send_common_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )

    def _send_frontend_file(self, route: str) -> None:
        requested_path = unquote(route).lstrip("/")
        if requested_path in {"", "index.html"}:
            requested_path = "preview.html"

        static_path = (self.frontend_dir / requested_path).resolve()
        frontend_root = self.frontend_dir.resolve()
        if not static_path.is_file() or not static_path.is_relative_to(frontend_root):
            self._send_error("Page not found", HTTPStatus.NOT_FOUND)
            return

        content = static_path.read_bytes()
        content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
        if static_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"

        self.send_response(HTTPStatus.OK.value)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_pic_file(self, route: str) -> None:
        requested_path = unquote(route.removeprefix("/pic/"))
        static_path = (self.pic_dir / requested_path).resolve()
        pic_root = self.pic_dir.resolve()
        if not static_path.is_file() or not static_path.is_relative_to(pic_root):
            self._send_error("Image not found", HTTPStatus.NOT_FOUND)
            return

        content = static_path.read_bytes()
        content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"

        self.send_response(HTTPStatus.OK.value)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    database_path: Path = DATABASE_PATH,
) -> None:
    """初始化存储并启动 API 服务。"""
    initialize_database(database_path)
    GameHubRequestHandler.database_path = database_path
    GameHubRequestHandler.frontend_dir = FRONTEND_DIR
    GameHubRequestHandler.pic_dir = PIC_DIR
    server = ThreadingHTTPServer((host, port), GameHubRequestHandler)
    print(f"空空如也GameHub site running at http://{host}:{port}/")
    print(f"空空如也GameHub API running at http://{host}:{port}/api")
    server.serve_forever()


def _first_query_value(
    query: dict[str, list[str]],
    key: str,
    default: str = "",
) -> str:
    """获取单值查询参数的第一个值。"""
    values = query.get(key)
    if not values:
        return default
    return values[0]


def _query_values(query: dict[str, list[str]], key: str) -> list[str]:
    """获取重复查询参数的全部值，例如多个 category。"""
    return query.get(key, [])


def _safe_int(value: str, default: int) -> int:
    """解析整数查询参数；输入无效时返回默认值。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
