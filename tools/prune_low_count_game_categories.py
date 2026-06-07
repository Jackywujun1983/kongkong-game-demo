"""Prune game categories with too few linked games."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_MIN_GAME_COUNT = 5

sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATABASE_PATH  # noqa: E402
from app.database import initialize_database, refresh_category_stats  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Delete categories linked to fewer than N games.",
    )
    parser.add_argument(
        "--database",
        default=str(DATABASE_PATH),
        help="SQLite database path.",
    )
    parser.add_argument(
        "--min-game-count",
        default=DEFAULT_MIN_GAME_COUNT,
        type=int,
        help="Keep only categories linked to at least this many games.",
    )
    return parser.parse_args()


def main() -> None:
    """Prune low-count categories and print a summary."""
    args = parse_args()
    database_path = Path(args.database)
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        result = prune_low_count_categories(
            connection,
            min_game_count=args.min_game_count,
        )

    print(f"Minimum game count: {args.min_game_count}")
    print(f"Categories before: {result['categories_before']}")
    print(f"Categories removed: {result['categories_removed']}")
    print(f"Category links removed: {result['links_removed']}")
    print(f"Primary categories updated: {result['primary_categories_updated']}")
    print(f"Games left without category links: {result['games_without_links']}")
    print(f"Categories after: {result['categories_after']}")


def prune_low_count_categories(
    connection: sqlite3.Connection,
    min_game_count: int = DEFAULT_MIN_GAME_COUNT,
) -> dict[str, int]:
    """Delete categories linked to fewer than min_game_count games."""
    if min_game_count <= 1:
        raise ValueError("min_game_count must be greater than 1")

    category_rows = get_category_counts(connection)
    low_category_ids = [
        int(row["id"])
        for row in category_rows
        if int(row["game_count"]) < min_game_count
    ]
    if not low_category_ids:
        refresh_category_stats(connection)
        return build_result(connection, len(category_rows), 0, 0, 0)

    kept_category = get_fallback_category(connection, low_category_ids)
    if kept_category is None:
        raise RuntimeError("No category would remain after pruning")

    should_manage_transaction = not connection.in_transaction
    if should_manage_transaction:
        connection.execute("BEGIN")
    try:
        primary_categories_updated = update_legacy_primary_categories(
            connection,
            low_category_ids,
            fallback_category_id=int(kept_category["id"]),
        )
        links_removed = count_low_category_links(connection, low_category_ids)
        delete_low_category_links(connection, low_category_ids)
        delete_low_categories(connection, low_category_ids)
        refresh_category_stats(connection)

        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise RuntimeError(f"Foreign key check failed: {foreign_key_errors}")

        if should_manage_transaction:
            connection.commit()
    except Exception:
        if should_manage_transaction:
            connection.rollback()
        raise

    return build_result(
        connection,
        categories_before=len(category_rows),
        categories_removed=len(low_category_ids),
        links_removed=links_removed,
        primary_categories_updated=primary_categories_updated,
    )


def get_category_counts(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return categories with linked game counts."""
    return connection.execute(
        """
        SELECT c.id, c.name, COUNT(gc.game_id) AS game_count
        FROM categories c
        LEFT JOIN game_categories gc ON gc.category_id = c.id
        GROUP BY c.id
        ORDER BY game_count ASC, c.name
        """
    ).fetchall()


def get_fallback_category(
    connection: sqlite3.Connection,
    low_category_ids: list[int],
) -> sqlite3.Row | None:
    """Pick the most-used remaining category for the legacy games.category_id."""
    placeholders = ",".join("?" for _ in low_category_ids)
    return connection.execute(
        f"""
        SELECT c.id, c.name, COUNT(gc.game_id) AS game_count
        FROM categories c
        LEFT JOIN game_categories gc ON gc.category_id = c.id
        WHERE c.id NOT IN ({placeholders})
        GROUP BY c.id
        ORDER BY game_count DESC, c.name
        LIMIT 1
        """,
        low_category_ids,
    ).fetchone()


def update_legacy_primary_categories(
    connection: sqlite3.Connection,
    low_category_ids: list[int],
    fallback_category_id: int,
) -> int:
    """Move games.category_id away from categories that will be deleted."""
    placeholders = ",".join("?" for _ in low_category_ids)
    game_rows = connection.execute(
        f"""
        SELECT id
        FROM games
        WHERE category_id IN ({placeholders})
        ORDER BY id
        """,
        low_category_ids,
    ).fetchall()

    for game_row in game_rows:
        replacement_category_id = get_replacement_category_id(
            connection,
            game_id=int(game_row["id"]),
            low_category_ids=low_category_ids,
        )
        connection.execute(
            """
            UPDATE games
            SET category_id = ?
            WHERE id = ?
            """,
            (
                replacement_category_id or fallback_category_id,
                int(game_row["id"]),
            ),
        )

    return len(game_rows)


def get_replacement_category_id(
    connection: sqlite3.Connection,
    game_id: int,
    low_category_ids: list[int],
) -> int | None:
    """Return the first remaining linked category for one game."""
    placeholders = ",".join("?" for _ in low_category_ids)
    row = connection.execute(
        f"""
        SELECT category_id
        FROM game_categories
        WHERE game_id = ? AND category_id NOT IN ({placeholders})
        ORDER BY sort_order, category_id
        LIMIT 1
        """,
        [game_id, *low_category_ids],
    ).fetchone()
    if row is None:
        return None
    return int(row["category_id"])


def count_low_category_links(
    connection: sqlite3.Connection,
    low_category_ids: list[int],
) -> int:
    """Count links that will be deleted."""
    placeholders = ",".join("?" for _ in low_category_ids)
    return int(
        connection.execute(
            f"""
            SELECT COUNT(*)
            FROM game_categories
            WHERE category_id IN ({placeholders})
            """,
            low_category_ids,
        ).fetchone()[0]
    )


def delete_low_category_links(
    connection: sqlite3.Connection,
    low_category_ids: list[int],
) -> None:
    """Delete low-count category links."""
    placeholders = ",".join("?" for _ in low_category_ids)
    connection.execute(
        f"""
        DELETE FROM game_categories
        WHERE category_id IN ({placeholders})
        """,
        low_category_ids,
    )


def delete_low_categories(
    connection: sqlite3.Connection,
    low_category_ids: list[int],
) -> None:
    """Delete low-count categories."""
    placeholders = ",".join("?" for _ in low_category_ids)
    connection.execute(
        f"""
        DELETE FROM categories
        WHERE id IN ({placeholders})
        """,
        low_category_ids,
    )


def build_result(
    connection: sqlite3.Connection,
    categories_before: int,
    categories_removed: int,
    links_removed: int,
    primary_categories_updated: int,
) -> dict[str, int]:
    """Build a cleanup summary."""
    return {
        "categories_before": categories_before,
        "categories_removed": categories_removed,
        "links_removed": links_removed,
        "primary_categories_updated": primary_categories_updated,
        "games_without_links": int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM games g
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM game_categories gc
                    WHERE gc.game_id = g.id
                )
                """
            ).fetchone()[0]
        ),
        "categories_after": int(
            connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        ),
    }


if __name__ == "__main__":
    main()
