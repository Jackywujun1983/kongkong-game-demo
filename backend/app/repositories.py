"""空空如也 GameHub API 的数据库访问函数。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config import DATABASE_PATH
from app.database import create_connection, decode_json_list, row_to_dict


def list_categories(database_path: Path = DATABASE_PATH) -> list[dict[str, Any]]:
    """返回可展示分类，并按关联游戏数量降序排序。"""
    with create_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, slug, description, game_count, is_visible
            FROM categories
            WHERE is_visible = 1
            ORDER BY game_count DESC, name
            """
        ).fetchall()
    categories = [row_to_dict(row) for row in rows]
    for category in categories:
        category["is_visible"] = bool(category["is_visible"])
    return categories


def search_games(
    query: str = "",
    category: str | list[str] = "",
    page: int = 1,
    page_size: int = 12,
    database_path: Path = DATABASE_PATH,
) -> dict[str, Any]:
    """按关键词和一个或多个分类名称或 slug 查询游戏。"""
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 50)
    offset = (safe_page - 1) * safe_page_size
    filters = []
    parameters: list[Any] = []
    category_values = _normalize_category_values(category)

    if query:
        keyword = f"%{query.lower()}%"
        filters.append(
            """
            (
                LOWER(g.title) LIKE ?
                OR LOWER(g.summary) LIKE ?
                OR LOWER(g.tags) LIKE ?
                OR LOWER(g.studio) LIKE ?
            )
            """
        )
        parameters.extend([keyword, keyword, keyword, keyword])

    if category_values:
        placeholders = ",".join("?" for _ in category_values)
        filters.append(
            f"""
            EXISTS (
                SELECT 1
                FROM game_categories fgc
                JOIN categories fc ON fc.id = fgc.category_id
                WHERE fgc.game_id = g.id
                    AND (
                        fc.slug IN ({placeholders})
                        OR fc.name IN ({placeholders})
                    )
            )
            """
        )
        parameters.extend([*category_values, *category_values])

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with create_connection(database_path) as connection:
        total = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM games g
            {where_clause}
            """,
            parameters,
        ).fetchone()[0]
        rows = connection.execute(
            f"""
            SELECT
                g.id,
                g.title,
                g.slug,
                g.studio,
                g.release_year,
                g.rating,
                g.cover_url,
                g.download_url,
                g.summary,
                g.platforms,
                g.tags,
                pc.name AS category_name,
                pc.slug AS category_slug
            FROM games g
            LEFT JOIN categories pc ON pc.id = g.category_id
            {where_clause}
            ORDER BY g.rating DESC, g.release_year DESC
            LIMIT ? OFFSET ?
            """,
            [*parameters, safe_page_size, offset],
        ).fetchall()
        games = [_map_game_row(row) for row in rows]
        _attach_game_categories(connection, games)

    return {
        "items": games,
        "page": safe_page,
        "page_size": safe_page_size,
        "total": total,
    }


def _normalize_category_values(category: str | list[str]) -> list[str]:
    """规范化重复参数或逗号分隔的分类筛选值。

    HTTP 层可能把重复的 `category` 参数传成列表，旧链接也可能使用一个
    逗号分隔的字符串。这里同时兼容两种形式，并在保持顺序的前提下去重。
    """
    if not category:
        return []

    raw_values = category if isinstance(category, list) else [category]
    values = []
    seen = set()
    for raw_value in raw_values:
        for item in str(raw_value).split(","):
            value = item.strip()
            if not value or value in seen:
                continue
            values.append(value)
            seen.add(value)
    return values


def get_game(slug: str, database_path: Path = DATABASE_PATH) -> dict[str, Any] | None:
    """按 slug 返回单个游戏，并包含它关联的全部分类。"""
    with create_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                g.id,
                g.title,
                g.slug,
                g.studio,
                g.release_year,
                g.rating,
                g.cover_url,
                g.download_url,
                g.summary,
                g.details,
                g.platforms,
                g.tags,
                pc.name AS category_name,
                pc.slug AS category_slug
            FROM games g
            LEFT JOIN categories pc ON pc.id = g.category_id
            WHERE g.slug = ?
            """,
            (slug,),
        ).fetchone()
        if row is None:
            return None
        game = _map_game_row(row, include_details=True)
        _attach_game_categories(connection, [game])
    return game


def list_ads(
    placement: str = "",
    database_path: Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """返回启用中的广告，可按广告位筛选。"""
    parameters: list[Any] = []
    where_clause = "WHERE is_active = 1"
    if placement:
        where_clause += " AND placement = ?"
        parameters.append(placement)

    with create_connection(database_path) as connection:
        rows = connection.execute(
            f"""
            SELECT id, placement, title, description, image_url, target_url
            FROM ads
            {where_clause}
            ORDER BY id
            """,
            parameters,
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def _map_game_row(
    row: sqlite3.Row,
    include_details: bool = False,
) -> dict[str, Any]:
    """将 games 表查询行转换为 API 响应结构。"""
    game = row_to_dict(row)
    game["platforms"] = decode_json_list(game.get("platforms"))
    game["tags"] = decode_json_list(game.get("tags"))
    if not include_details:
        game.pop("details", None)
    game["categories"] = []
    return game


def _attach_game_categories(
    connection: sqlite3.Connection,
    games: list[dict[str, Any]],
) -> None:
    """为每个游戏响应补全分类元数据。

    这里会保留隐藏分类，因为游戏详情和搜索结果应该展示游戏真实拥有的
    元数据。`is_visible` 只控制分类是否出现在前端筛选栏中。
    """
    if not games:
        return

    game_ids = [int(game["id"]) for game in games]
    placeholders = ",".join("?" for _ in game_ids)
    rows = connection.execute(
        f"""
        SELECT
            gc.game_id,
            c.id,
            c.name,
            c.slug,
            c.description,
            c.game_count,
            c.is_visible
        FROM game_categories gc
        JOIN categories c ON c.id = gc.category_id
        WHERE gc.game_id IN ({placeholders})
        ORDER BY gc.game_id, gc.sort_order, c.name
        """,
        game_ids,
    ).fetchall()

    categories_by_game: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        category = {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "description": row["description"],
            "game_count": row["game_count"],
            "is_visible": bool(row["is_visible"]),
        }
        categories_by_game.setdefault(int(row["game_id"]), []).append(category)

    for game in games:
        game_categories = categories_by_game.get(int(game["id"]), [])
        game["categories"] = game_categories
        if game_categories:
            primary_category = game_categories[0]
            game["category_name"] = primary_category["name"]
            game["category_slug"] = primary_category["slug"]
        else:
            game["category_name"] = ""
            game["category_slug"] = ""
