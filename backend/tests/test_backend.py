"""Backend smoke tests using only the Python standard library."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import initialize_database, refresh_category_stats
from app.repositories import (
    get_game,
    list_ads,
    list_categories,
    search_games,
)


class BackendRepositoryTests(unittest.TestCase):
    """Verify core repository behavior."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.sqlite3"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_games_can_be_searched(self) -> None:
        self._insert_game(
            title="测试星图边境",
            slug="test-star-map-frontier",
            category_slug="action-adventure",
            tags=["动作", "测试"],
        )

        result = search_games(query="星图", database_path=self.database_path)

        self.assertGreaterEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["slug"], "test-star-map-frontier")
        self.assertEqual(result["items"][0]["size"], "12 GB")
        self.assertNotIn("details", result["items"][0])

    def test_game_detail_includes_category_and_tags(self) -> None:
        self._insert_game(
            title="测试纸月",
            slug="test-paper-moon",
            category_slug="indie",
            tags=["独立", "解谜"],
        )

        game = get_game("test-paper-moon", self.database_path)

        self.assertIsNotNone(game)
        assert game is not None
        self.assertEqual(game["category_slug"], "indie")
        self.assertEqual(game["categories"][0]["slug"], "indie")
        self.assertIn("download_url", game)
        self.assertTrue(game["download_url"].endswith("/test-paper-moon"))
        self.assertIn("解谜", game["tags"])
        self.assertEqual(game["size"], "12 GB")

    def test_category_filter_matches_any_linked_category(self) -> None:
        self._insert_game(
            title="测试纸月",
            slug="test-paper-moon",
            category_slug="indie",
            tags=["独立", "解谜"],
        )
        self._insert_game(
            title="测试遗迹",
            slug="test-relic",
            category_slug="role-playing",
            tags=["角色扮演", "探索"],
        )

        by_slugs = search_games(
            category="indie,role-playing",
            database_path=self.database_path,
        )
        by_name = search_games(
            category="独立佳作",
            database_path=self.database_path,
        )

        by_slugs_slugs = {game["slug"] for game in by_slugs["items"]}
        by_name_slugs = {game["slug"] for game in by_name["items"]}
        self.assertIn("test-paper-moon", by_slugs_slugs)
        self.assertIn("test-relic", by_slugs_slugs)
        self.assertIn("test-paper-moon", by_name_slugs)

    def test_categories_and_ads_are_seeded(self) -> None:
        ads = list_ads(database_path=self.database_path)
        connection = sqlite3.connect(self.database_path)
        try:
            category_count = connection.execute(
                "SELECT COUNT(*) FROM categories"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertGreaterEqual(category_count, 5)
        self.assertEqual(len(ads), 2)

    def test_categories_include_game_count_and_sort_by_count(self) -> None:
        for index in range(10):
            self._insert_game(
                title=f"Indie Sort Test {index}",
                slug=f"indie-sort-test-{index}",
                category_slug="indie",
                tags=["sort"],
            )
        for index in range(12):
            self._insert_game(
                title=f"Role Sort Test {index}",
                slug=f"role-sort-test-{index}",
                category_slug="role-playing",
                tags=["sort"],
            )

        connection = sqlite3.connect(self.database_path)
        try:
            refresh_category_stats(connection)
            connection.commit()
        finally:
            connection.close()

        categories = list_categories(self.database_path)

        self.assertEqual(categories[0]["slug"], "role-playing")
        self.assertEqual(categories[0]["game_count"], 12)
        self.assertEqual(categories[1]["slug"], "indie")
        self.assertEqual(categories[1]["game_count"], 10)
        self.assertIsInstance(categories[0]["is_visible"], bool)

    def test_category_visibility_depends_on_linked_game_count(self) -> None:
        for index in range(9):
            self._insert_game(
                title=f"Visibility Test {index}",
                slug=f"visibility-test-{index}",
                category_slug="indie",
                tags=["visibility"],
            )

        connection = sqlite3.connect(self.database_path)
        try:
            refresh_category_stats(connection)
            connection.commit()
        finally:
            connection.close()

        categories = list_categories(self.database_path)
        category_slugs = {category["slug"] for category in categories}
        self.assertNotIn("indie", category_slugs)

        self._insert_game(
            title="Visibility Test 9",
            slug="visibility-test-9",
            category_slug="indie",
            tags=["visibility"],
        )
        connection = sqlite3.connect(self.database_path)
        try:
            refresh_category_stats(connection)
            connection.commit()
        finally:
            connection.close()

        categories = list_categories(self.database_path)
        category_slugs = {category["slug"] for category in categories}
        self.assertIn("indie", category_slugs)

    def test_removed_account_and_forum_tables_are_absent(self) -> None:
        removed_tables = {
            "users",
            "sessions",
            "forum_posts",
            "forum_comments",
        }
        connection = sqlite3.connect(self.database_path)
        try:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        finally:
            connection.close()

        table_names = {row[0] for row in rows}
        self.assertFalse(removed_tables & table_names)

    def test_legacy_seed_games_are_not_initialized(self) -> None:
        result = search_games(database_path=self.database_path)

        self.assertEqual(result["total"], 0)

    def _insert_game(
        self,
        title: str,
        slug: str,
        category_slug: str,
        tags: list[str],
    ) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.row_factory = sqlite3.Row
            category_id = connection.execute(
                "SELECT id FROM categories WHERE slug = ?",
                (category_slug,),
            ).fetchone()["id"]
            cursor = connection.execute(
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
                    size,
                    summary,
                    details,
                    platforms,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    slug,
                    category_id,
                    "Test Studio",
                    2026,
                    8.5,
                    "/assets/covers/test.png",
                    f"https://gamehub.example.com/downloads/{slug}",
                    "12 GB",
                    f"{title} 测试简介",
                    f"{title} 测试详情",
                    json.dumps(["PC"], ensure_ascii=False),
                    json.dumps(tags, ensure_ascii=False),
                ),
            )
            connection.execute(
                """
                INSERT INTO game_categories (game_id, category_id, sort_order)
                VALUES (?, ?, ?)
                """,
                (cursor.lastrowid, category_id, 0),
            )
            connection.commit()
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
