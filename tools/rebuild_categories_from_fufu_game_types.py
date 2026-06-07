"""Rebuild categories from the fufu CSV game type field."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_CSV_PATH = ROOT_DIR / "data" / "fufu_quark_only.csv"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR / "tools"))

from app.config import DATABASE_PATH  # noqa: E402
from app.database import initialize_database, refresh_category_stats  # noqa: E402
from import_fufu_quark_games import (  # noqa: E402
    FIELD_DOWNLOAD_URL,
    FIELD_TITLE,
    ensure_categories,
    get_game_type_names,
    make_game_slug,
    read_csv_rows,
    sync_game_categories,
)
from prune_low_count_game_categories import (  # noqa: E402
    DEFAULT_MIN_GAME_COUNT,
    prune_low_count_categories,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean categories and rebuild them from CSV game types.",
    )
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
        help="Delete categories linked to fewer than this many games after rebuild.",
    )
    return parser.parse_args()


def main() -> None:
    """Rebuild category rows and game-category links."""
    args = parse_args()
    csv_path = Path(args.csv)
    database_path = Path(args.database)

    initialize_database(database_path)
    rows = read_csv_rows(csv_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rebuild_result = rebuild_categories(connection, rows)
        prune_result = prune_low_count_categories(
            connection,
            min_game_count=args.min_category_game_count,
        )
        refresh_category_stats(connection)

    print(f"CSV rows: {len(rows)}")
    print(f"Categories rebuilt: {rebuild_result['category_count']}")
    print(f"CSV games relinked: {rebuild_result['csv_games_relinked']}")
    print(f"Other games relinked: {rebuild_result['other_games_relinked']}")
    print(f"Game-category links: {rebuild_result['link_count']}")
    print(f"Categories removed: {prune_result['categories_removed']}")
    print(f"Categories after: {prune_result['categories_after']}")


def rebuild_categories(
    connection: sqlite3.Connection,
    rows: list[dict[str, str]],
) -> dict[str, int]:
    """Clean category tables and relink games."""
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("BEGIN")
    try:
        connection.execute("DELETE FROM game_categories")
        connection.execute("DELETE FROM categories")
        connection.execute("DELETE FROM sqlite_sequence WHERE name = 'categories'")

        category_ids = ensure_categories(connection, rows)
        default_category_id = get_default_category_id(category_ids)

        csv_slugs = set()
        csv_games_relinked = 0
        for row in rows:
            slug = make_game_slug(row[FIELD_TITLE], row[FIELD_DOWNLOAD_URL])
            csv_slugs.add(slug)
            game_row = connection.execute(
                "SELECT id FROM games WHERE slug = ?",
                (slug,),
            ).fetchone()
            if game_row is None:
                continue

            game_category_ids = [
                category_ids[category_name]
                for category_name in get_game_type_names(row)
            ]
            update_game_categories(
                connection,
                int(game_row["id"]),
                game_category_ids,
            )
            csv_games_relinked += 1

        other_games_relinked = relink_non_csv_games(
            connection,
            csv_slugs,
            category_ids,
            default_category_id,
        )

        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise RuntimeError(f"Foreign key check failed: {foreign_key_errors}")

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")

    link_count = connection.execute("SELECT COUNT(*) FROM game_categories").fetchone()[0]
    return {
        "category_count": len(category_ids),
        "csv_games_relinked": csv_games_relinked,
        "other_games_relinked": other_games_relinked,
        "link_count": int(link_count),
    }


def get_default_category_id(category_ids: dict[str, int]) -> int:
    """Choose a deterministic fallback category for non-CSV seed games."""
    if "独立" in category_ids:
        return category_ids["独立"]
    first_category_name = sorted(category_ids)[0]
    return category_ids[first_category_name]


def relink_non_csv_games(
    connection: sqlite3.Connection,
    csv_slugs: set[str],
    category_ids: dict[str, int],
    default_category_id: int,
) -> int:
    """Relink old seed games that do not exist in the CSV."""
    relinked_count = 0
    game_rows = connection.execute(
        """
        SELECT id, slug, tags
        FROM games
        ORDER BY id
        """
    ).fetchall()
    for game_row in game_rows:
        if game_row["slug"] in csv_slugs:
            continue

        category_matches = [
            category_ids[tag]
            for tag in decode_tags(game_row["tags"])
            if tag in category_ids
        ]
        update_game_categories(
            connection,
            int(game_row["id"]),
            category_matches or [default_category_id],
        )
        relinked_count += 1
    return relinked_count


def update_game_categories(
    connection: sqlite3.Connection,
    game_id: int,
    category_ids: list[int],
) -> None:
    """Update the legacy primary category and the relation table."""
    connection.execute(
        """
        UPDATE games
        SET category_id = ?
        WHERE id = ?
        """,
        (category_ids[0], game_id),
    )
    sync_game_categories(connection, game_id, category_ids)


def decode_tags(value: str | None) -> list[str]:
    """Decode game tags from SQLite JSON text."""
    if not value:
        return []
    try:
        loaded_value = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded_value, list):
        return []
    return [str(item) for item in loaded_value]


if __name__ == "__main__":
    main()
