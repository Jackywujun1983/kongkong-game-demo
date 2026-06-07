"""Import fufu_quark_only.csv rows into the games table."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_CSV_PATH = ROOT_DIR / "data" / "fufu_quark_only.csv"
DEFAULT_COVER_URL = "/public/assets/covers/default-game-cover.jpg"
DEFAULT_STUDIO = "未知"
DEFAULT_RATING = 0.0
DEFAULT_PLATFORM = "PC"
GAME_TYPE_ALIASES: dict[str, str] = {}

sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATABASE_PATH  # noqa: E402
from app.database import initialize_database, refresh_category_stats  # noqa: E402
from prune_low_count_game_categories import (  # noqa: E402
    DEFAULT_MIN_GAME_COUNT,
    prune_low_count_categories,
)


FIELD_TYPE = "类型"
FIELD_TITLE = "游戏名称"
FIELD_GAME_TYPE = "游戏类型"
FIELD_DOWNLOAD_URL = "url_or_filename"
FIELD_SIZE = "大小"
FIELD_PUBLISHED_AT = "发布时间"
FIELD_YEAR = "年份"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Import fufu Quark game data.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH), help="CSV file path.")
    parser.add_argument(
        "--database",
        default=str(DATABASE_PATH),
        help="SQLite database path.",
    )
    parser.add_argument(
        "--min-category-game-count",
        default=DEFAULT_MIN_GAME_COUNT,
        type=int,
        help="Delete categories linked to fewer than this many games after import.",
    )
    return parser.parse_args()


def main() -> None:
    """Import CSV rows into SQLite."""
    args = parse_args()
    csv_path = Path(args.csv)
    database_path = Path(args.database)

    initialize_database(database_path)
    rows = read_csv_rows(csv_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        category_ids = ensure_categories(connection, rows)
        inserted_count, updated_count = upsert_games(connection, rows, category_ids)
        prune_result = prune_low_count_categories(
            connection,
            min_game_count=args.min_category_game_count,
        )
        refresh_category_stats(connection)

    print(f"CSV rows: {len(rows)}")
    print(f"Inserted games: {inserted_count}")
    print(f"Updated games: {updated_count}")
    print(f"Categories removed: {prune_result['categories_removed']}")
    print(f"Categories after: {prune_result['categories_after']}")


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    """Read CSV rows using the source file encoding."""
    text = csv_path.read_bytes().decode("gb18030")
    reader = csv.DictReader(text.splitlines())
    required_fields = {
        FIELD_TYPE,
        FIELD_TITLE,
        FIELD_GAME_TYPE,
        FIELD_DOWNLOAD_URL,
        FIELD_SIZE,
        FIELD_PUBLISHED_AT,
        FIELD_YEAR,
    }
    missing_fields = required_fields - set(reader.fieldnames or [])
    if missing_fields:
        missing_text = ", ".join(sorted(missing_fields))
        raise ValueError(f"CSV missing required fields: {missing_text}")
    return [
        {key: (value or "").strip() for key, value in row.items()}
        for row in reader
        if row.get(FIELD_TITLE, "").strip()
    ]


def ensure_categories(
    connection: sqlite3.Connection,
    rows: list[dict[str, str]],
) -> dict[str, int]:
    """Create categories from the CSV game type field."""
    category_names = sorted(
        {
            category_name
            for row in rows
            for category_name in get_game_type_names(row)
        }
    )
    for category_name in category_names:
        slug = make_category_slug(category_name)
        description = f"来自 fufu_quark_only.csv 的游戏类型：{category_name}"
        connection.execute(
            """
            INSERT INTO categories (name, slug, description)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                description = excluded.description
            """,
            (category_name, slug, description),
        )

    category_rows = connection.execute(
        """
        SELECT id, name, slug
        FROM categories
        """
    ).fetchall()
    return {row["name"]: int(row["id"]) for row in category_rows}


def upsert_games(
    connection: sqlite3.Connection,
    rows: list[dict[str, str]],
    category_ids: dict[str, int],
) -> tuple[int, int]:
    """Insert or update games from CSV rows."""
    inserted_count = 0
    updated_count = 0

    for row in rows:
        game_payload = build_game_payload(row, category_ids)
        exists = connection.execute(
            "SELECT 1 FROM games WHERE slug = ?",
            (game_payload["slug"],),
        ).fetchone()
        if exists:
            updated_count += 1
        else:
            inserted_count += 1

        connection.execute(
            """
            INSERT INTO games (
                title,
                slug,
                category_id,
                studio,
                release_year,
                rating,
                cover_url,
                download_url,
                summary,
                details,
                platforms,
                tags
            )
            VALUES (
                :title,
                :slug,
                :category_id,
                :studio,
                :release_year,
                :rating,
                :cover_url,
                :download_url,
                :summary,
                :details,
                :platforms,
                :tags
            )
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                category_id = excluded.category_id,
                studio = excluded.studio,
                release_year = excluded.release_year,
                rating = excluded.rating,
                cover_url = excluded.cover_url,
                download_url = excluded.download_url,
                summary = excluded.summary,
                details = excluded.details,
                platforms = excluded.platforms,
                tags = excluded.tags
            """,
            game_payload,
        )
        game_row = connection.execute(
            "SELECT id FROM games WHERE slug = ?",
            (game_payload["slug"],),
        ).fetchone()
        sync_game_categories(
            connection,
            int(game_row["id"]),
            game_payload["category_ids"],
        )

    return inserted_count, updated_count


def build_game_payload(
    row: dict[str, str],
    category_ids: dict[str, int],
) -> dict[str, Any]:
    """Build a games table payload from one CSV row."""
    resource_category_name = row[FIELD_TYPE] or "未分类"
    title = row[FIELD_TITLE]
    game_types = get_game_type_names(row)
    download_url = row[FIELD_DOWNLOAD_URL]
    size = row[FIELD_SIZE] or "未知大小"
    published_at = row[FIELD_PUBLISHED_AT] or "未知发布时间"
    release_year = parse_release_year(row[FIELD_YEAR], published_at)
    tags = [*game_types, resource_category_name]
    game_category_ids = [category_ids[category_name] for category_name in game_types]

    summary = (
        f"{title}，资源分类：{resource_category_name}，"
        f"游戏类型：{row[FIELD_GAME_TYPE] or '未标注'}，资源大小：{size}。"
    )
    details = (
        f"资源名称：{title}\n"
        f"资源分类：{resource_category_name}\n"
        f"游戏类型：{row[FIELD_GAME_TYPE] or '未标注'}\n"
        f"资源大小：{size}\n"
        f"发布时间：{published_at}\n"
        f"下载地址：{download_url}"
    )

    return {
        "title": title,
        "slug": make_game_slug(title, download_url),
        "category_id": game_category_ids[0],
        "category_ids": game_category_ids,
        "studio": DEFAULT_STUDIO,
        "release_year": release_year,
        "rating": DEFAULT_RATING,
        "cover_url": DEFAULT_COVER_URL,
        "download_url": download_url,
        "summary": summary,
        "details": details,
        "platforms": json.dumps([DEFAULT_PLATFORM], ensure_ascii=False),
        "tags": json.dumps(tags, ensure_ascii=False),
    }


def sync_game_categories(
    connection: sqlite3.Connection,
    game_id: int,
    category_ids: list[int],
) -> None:
    """Replace a game's category links."""
    connection.execute("DELETE FROM game_categories WHERE game_id = ?", (game_id,))
    connection.executemany(
        """
        INSERT INTO game_categories (game_id, category_id, sort_order)
        VALUES (?, ?, ?)
        """,
        [
            (game_id, category_id, sort_order)
            for sort_order, category_id in enumerate(category_ids)
        ],
    )


def get_game_type_names(row: dict[str, str]) -> list[str]:
    """Return ordered unique game type names for one CSV row."""
    game_types = split_game_types(row[FIELD_GAME_TYPE])
    return game_types or ["未分类"]


def split_game_types(value: str) -> list[str]:
    """Split the CSV game type field into tags."""
    names = []
    seen = set()
    for item in value.split("|"):
        name = item.strip()
        name = GAME_TYPE_ALIASES.get(name, name)
        if not is_valid_game_type_name(name) or name in seen:
            continue
        names.append(name)
        seen.add(name)
    return names


def is_valid_game_type_name(name: str) -> bool:
    """Return whether a CSV game type value is suitable as a category."""
    if not name or len(name) > 30:
        return False
    invalid_fragments = ("大小：", "相关攻略", "种子：", "资源大小", "http")
    return not any(fragment in name for fragment in invalid_fragments)


def parse_release_year(year_value: str, published_at: str) -> int:
    """Parse a release year from CSV fields."""
    if year_value.isdigit():
        return int(year_value)

    matched_year = re.search(r"(19|20)\d{2}", published_at)
    if matched_year:
        return int(matched_year.group(0))

    return 0


def make_category_slug(category_name: str) -> str:
    """Create a deterministic category slug."""
    digest = hashlib.sha1(category_name.encode("utf-8")).hexdigest()[:12]
    return f"fufu-category-{digest}"


def make_game_slug(title: str, download_url: str) -> str:
    """Create a deterministic game slug."""
    digest = hashlib.sha1(f"{title}|{download_url}".encode("utf-8")).hexdigest()[:16]
    return f"fufu-game-{digest}"


if __name__ == "__main__":
    main()
