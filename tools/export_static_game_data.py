"""Export SQLite game data for the GitHub Pages static site."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "backend" / "gamehub.sqlite3"
OUTPUT_PATH = PROJECT_DIR / "frontend" / "public" / "game-data.js"
DEFAULT_COVER_PATH = "./public/assets/covers/default-game-cover.jpg"
LEGACY_PLACEHOLDER_PATH = "./public/assets/covers/game-placeholder.png"
ABSOLUTE_LEGACY_PLACEHOLDER_PATH = "/public/assets/covers/game-placeholder.png"


def main() -> None:
    """Export categories and games into frontend/public/game-data.js."""
    payload = build_static_payload(DATABASE_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "window.GAMEHUB_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(
        f"Exported {len(payload['games'])} games and "
        f"{len(payload['categories'])} categories to {OUTPUT_PATH}"
    )


def build_static_payload(database_path: Path) -> dict[str, Any]:
    """Build a static payload that matches the frontend fallback data shape."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        categories = list_categories(connection)
        games = list_games(connection)

    return {
        "categories": [
            [category["slug"], category["name"], category["game_count"]]
            for category in categories
        ],
        "games": games,
    }


def list_categories(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return visible categories in the same order as the API."""
    return connection.execute(
        """
        SELECT id, name, slug, description, game_count, is_visible
        FROM categories
        WHERE is_visible = 1
        ORDER BY game_count DESC, name
        """
    ).fetchall()


def list_games(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return games with their full category metadata for static rendering."""
    rows = connection.execute(
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
        ORDER BY g.rating DESC, g.release_year DESC
        """
    ).fetchall()
    games = [map_game_row(row) for row in rows]
    attach_categories(connection, games)
    return games


def map_game_row(row: sqlite3.Row) -> dict[str, Any]:
    """Map a SQLite game row to the static frontend game shape."""
    categories = []
    category_slug = row["category_slug"] or ""
    category_name = row["category_name"] or "未分类"
    if category_slug:
        categories.append(
            {
                "slug": category_slug,
                "name": category_name,
                "description": "",
                "game_count": 0,
                "is_visible": True,
            }
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "slug": row["slug"],
        "category": category_slug,
        "categoryName": category_name,
        "categories": categories,
        "studio": row["studio"],
        "year": row["release_year"],
        "rating": float(row["rating"] or 0),
        "cover": normalize_cover_url(row["cover_url"]),
        "summary": row["summary"],
        "details": row["details"],
        "downloadUrl": row["download_url"],
        "platforms": decode_json_list(row["platforms"]),
        "tags": decode_json_list(row["tags"]),
    }


def attach_categories(connection: sqlite3.Connection, games: list[dict[str, Any]]) -> None:
    """Attach all categories for each game."""
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
        categories_by_game.setdefault(int(row["game_id"]), []).append(
            {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "description": row["description"],
                "game_count": row["game_count"],
                "is_visible": bool(row["is_visible"]),
            }
        )

    for game in games:
        game_categories = categories_by_game.get(int(game["id"]), [])
        if not game_categories:
            continue
        game["categories"] = game_categories
        game["category"] = game_categories[0]["slug"]
        game["categoryName"] = " / ".join(
            category["name"] for category in game_categories
        )


def decode_json_list(value: str | None) -> list[str]:
    """Decode JSON list values stored in SQLite text columns."""
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded]


def normalize_cover_url(value: str | None) -> str:
    """Return the default cover when a game has no usable cover URL."""
    cover_url = (value or "").strip()
    if not cover_url or cover_url in {
        LEGACY_PLACEHOLDER_PATH,
        ABSOLUTE_LEGACY_PLACEHOLDER_PATH,
    }:
        return DEFAULT_COVER_PATH
    if cover_url.startswith("/public/"):
        return f".{cover_url}"
    if cover_url.startswith("public/"):
        return f"./{cover_url}"
    return cover_url


if __name__ == "__main__":
    main()
