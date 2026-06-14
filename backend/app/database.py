"""空空如也 GameHub API 的 SQLite 表结构、迁移和初始数据。"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import DATABASE_PATH


LEGACY_SEED_GAME_SLUGS = (
    "star-harbor-frontier",
    "neon-backstreet",
    "kingdom-workshop",
    "paper-moon-traveler",
    "final-arena",
    "relic-tuner",
)


@contextmanager
def create_connection(
    database_path: Path = DATABASE_PATH,
) -> Iterator[sqlite3.Connection]:
    """创建 SQLite 连接，并在使用结束后自动提交和关闭。"""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """创建数据表、执行轻量迁移，并刷新派生统计数据。"""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with create_connection(database_path) as connection:
        _create_schema(connection)
        _seed_data(connection)
        refresh_category_stats(connection)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 SQLite 行对象转换为普通字典。"""
    return {key: row[key] for key in row.keys()}


def decode_json_list(value: str | None) -> list[str]:
    """解析 SQLite 中以 JSON 字符串保存的列表。"""
    if not value:
        return []
    loaded_value = json.loads(value)
    if not isinstance(loaded_value, list):
        return []
    return [str(item) for item in loaded_value]


def _create_schema(connection: sqlite3.Connection) -> None:
    """为新 SQLite 数据库创建当前版本的表结构。"""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            game_count INTEGER NOT NULL DEFAULT 0,
            is_visible INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            studio TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            rating REAL NOT NULL,
            cover_url TEXT NOT NULL,
            download_url TEXT NOT NULL DEFAULT '',
            size TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL,
            details TEXT NOT NULL,
            platforms TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        );

        CREATE TABLE IF NOT EXISTS game_categories (
            game_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (game_id, category_id),
            FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placement TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL,
            target_url TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    _migrate_schema(connection)


def _migrate_schema(connection: sqlite3.Connection) -> None:
    """对旧版本数据库执行追加字段和关系表补齐迁移。"""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS game_categories (
            game_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (game_id, category_id),
            FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
        """
    )
    game_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(games)").fetchall()
    }
    if "download_url" not in game_columns:
        # 旧版种子数据库没有下载地址字段，使用 slug 生成稳定的占位地址。
        connection.execute(
            "ALTER TABLE games ADD COLUMN download_url TEXT NOT NULL DEFAULT ''"
        )
        connection.execute(
            """
            UPDATE games
            SET download_url = 'https://gamehub.example.com/downloads/' || slug
            WHERE download_url = ''
            """
        )
    if "size" not in game_columns:
        connection.execute("ALTER TABLE games ADD COLUMN size TEXT NOT NULL DEFAULT ''")

    _backfill_game_size(connection)

    category_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(categories)").fetchall()
    }
    if "is_visible" not in category_columns:
        connection.execute(
            "ALTER TABLE categories ADD COLUMN is_visible INTEGER NOT NULL DEFAULT 1"
        )
    if "game_count" not in category_columns:
        connection.execute(
            "ALTER TABLE categories ADD COLUMN game_count INTEGER NOT NULL DEFAULT 0"
        )

    relation_count = connection.execute(
        "SELECT COUNT(*) FROM game_categories"
    ).fetchone()[0]
    if relation_count == 0:
        # 旧版数据库只有单一主类型字段，这里回填多类型关系表。
        connection.execute(
            """
            INSERT OR IGNORE INTO game_categories (game_id, category_id, sort_order)
            SELECT id, category_id, 0
            FROM games
            WHERE category_id IS NOT NULL
            """
        )
    _remove_legacy_seed_games(connection)
    _remove_account_and_forum_tables(connection)
    refresh_category_stats(connection)


def refresh_category_stats(
    connection: sqlite3.Connection,
    min_visible_game_count: int = 10,
) -> None:
    """刷新分类的派生数量和前端展示标记。

    `game_count` 保存 `game_categories` 中关联到该类型的去重游戏数量。
    关联游戏数小于 `min_visible_game_count` 的类型会从 `/api/categories`
    中隐藏，但仍保留在游戏详情和按类型查询中，避免丢失真实元数据。
    """
    connection.execute(
        """
        UPDATE categories
        SET
            game_count = (
                SELECT COUNT(DISTINCT game_categories.game_id)
                FROM game_categories
                WHERE game_categories.category_id = categories.id
            ),
            is_visible = CASE
            WHEN (
                SELECT COUNT(DISTINCT game_categories.game_id)
                FROM game_categories
                WHERE game_categories.category_id = categories.id
            ) < ?
            THEN 0
            ELSE 1
        END
        """,
        (min_visible_game_count,),
    )


def refresh_category_visibility(
    connection: sqlite3.Connection,
    min_visible_game_count: int = 10,
) -> None:
    """兼容旧调用名称，内部刷新分类数量和展示标记。"""
    refresh_category_stats(connection, min_visible_game_count)


def _remove_legacy_seed_games(connection: sqlite3.Connection) -> None:
    """删除已经不属于当前导入目录的旧版演示游戏。"""
    placeholders = ",".join("?" for _ in LEGACY_SEED_GAME_SLUGS)
    connection.execute(
        f"""
        DELETE FROM games
        WHERE slug IN ({placeholders})
        """,
        LEGACY_SEED_GAME_SLUGS,
    )


def _remove_account_and_forum_tables(connection: sqlite3.Connection) -> None:
    """从旧数据库中删除已下线的账户和论坛模块表。"""
    connection.executescript(
        """
        DROP TABLE IF EXISTS forum_comments;
        DROP TABLE IF EXISTS forum_posts;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS users;
        """
    )
    connection.execute("DELETE FROM ads WHERE placement = ?", ("forum_feed",))


def _backfill_game_size(connection: sqlite3.Connection) -> None:
    """从旧详情文本中回填 games.size。"""
    rows = connection.execute(
        """
        SELECT id, summary, details
        FROM games
        WHERE size = ''
        """
    ).fetchall()
    updates = []
    for row in rows:
        size = _extract_game_size(row["details"], row["summary"])
        if size:
            updates.append((size, row["id"]))
    if not updates:
        return

    connection.executemany(
        """
        UPDATE games
        SET size = ?
        WHERE id = ? AND size = ''
        """,
        updates,
    )


def _extract_game_size(*sources: str) -> str:
    """从历史文本字段中提取资源大小。"""
    for source in sources:
        match = re.search(r"资源大小[:：]\s*([^。，,\n]+)", source or "")
        if not match:
            continue
        size = match.group(1).strip()
        if size and size not in {"未知", "未知大小", "未标注"}:
            return size
    return ""


def _seed_data(connection: sqlite3.Connection) -> None:
    """为空开发数据库写入默认分类和广告占位数据。"""
    category_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if category_count:
        return

    categories = [
        ("动作冒险", "action-adventure", "高节奏战斗、探索和电影化叙事。"),
        ("角色扮演", "role-playing", "角色成长、装备构筑和沉浸式剧情体验。"),
        ("策略模拟", "strategy-sim", "资源调度、战术规划和长期经营。"),
        ("独立佳作", "indie", "风格鲜明、机制新颖的小团队作品。"),
        ("多人竞技", "multiplayer", "强调对抗、协作和赛季化运营。"),
    ]
    connection.executemany(
        """
        INSERT INTO categories (name, slug, description)
        VALUES (?, ?, ?)
        """,
        categories,
    )

    ads = [
        (
            "home_top",
            "预留广告位 A",
            "首页顶部横幅，可接入发行商活动、平台促销或新品预约。",
            "/assets/ads/home-top.png",
            "#",
            1,
        ),
        (
            "sidebar",
            "预留广告位 B",
            "详情页侧边栏广告位，适合垂类推荐和周边活动。",
            "/assets/ads/sidebar.png",
            "#",
            1,
        ),
    ]
    connection.executemany(
        """
        INSERT INTO ads (
            placement,
            title,
            description,
            image_url,
            target_url,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ads,
    )
