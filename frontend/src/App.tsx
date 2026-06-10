import { AnimatePresence, motion } from "framer-motion";
import { Gamepad2, Loader2, Search, SlidersHorizontal } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { CategoryRail } from "./features/games/CategoryRail";
import { GameCard } from "./features/games/GameCard";
import {
  getCategories,
  searchGames,
} from "./services/api";
import type {
  Category,
  GameSummary,
} from "./types/domain";

export default function App() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [games, setGames] = useState<GameSummary[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const [categoryItems, gameResult] =
          await Promise.all([
            getCategories(),
            searchGames({ pageSize: 12 }),
          ]);
        setCategories(categoryItems);
        setGames(gameResult.items);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "加载失败");
      } finally {
        setIsLoading(false);
      }
    }

    loadInitialData();
  }, []);

  useEffect(() => {
    async function loadGames() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const result = await searchGames({
          category: selectedCategory,
          query: activeQuery,
          pageSize: 12,
        });
        setGames(result.items);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "检索失败");
      } finally {
        setIsLoading(false);
      }
    }

    loadGames();
  }, [activeQuery, selectedCategory]);

  function handleOpenGame(slug: string) {
    window.location.href = `/detail.html?slug=${encodeURIComponent(slug)}`;
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActiveQuery(searchTerm.trim());
  }

  function handleSelectCategory(category: string) {
    setSearchTerm("");
    setActiveQuery("");
    setSelectedCategory(category);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand-mark" href="/preview.html" aria-label="返回首页">
          <Gamepad2 size={24} />
          <span>空空如也GameHub</span>
        </a>
        <form className="search-form" onSubmit={handleSearch}>
          <Search size={18} />
          <input
            aria-label="检索游戏"
            placeholder="搜索游戏、工作室、标签"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <button className="primary-button" type="submit">
            检索
          </button>
        </form>
      </header>

      <div className="dashboard-layout dashboard-layout--focused">
        <aside className="left-rail">
          <CategoryRail
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={handleSelectCategory}
          />
        </aside>

        <section className="content-region">
          <div className="content-toolbar">
            <div className="section-heading">
              <SlidersHorizontal size={18} />
              <span>游戏库</span>
            </div>
            <span>{games.length} 项结果</span>
          </div>

          {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}

          {isLoading ? (
            <div className="loading-state">
              <Loader2 size={24} />
              <span>加载中</span>
            </div>
          ) : null}

          {!isLoading && games.length === 0 ? (
            <div className="empty-state">暂无匹配游戏</div>
          ) : null}

          <motion.div className="game-grid" layout>
            <AnimatePresence>
              {games.map((game) => (
                <GameCard game={game} key={game.slug} onOpen={handleOpenGame} />
              ))}
            </AnimatePresence>
          </motion.div>
        </section>
      </div>
    </main>
  );
}
