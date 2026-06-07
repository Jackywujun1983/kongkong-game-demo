import { motion } from "framer-motion";
import { Eye } from "lucide-react";

import type { GameSummary } from "../../types/domain";

interface GameCardProps {
  game: GameSummary;
  onOpen: (slug: string) => void;
}

export function GameCard({ game, onOpen }: GameCardProps) {
  const categoryNames = game.categories.length
    ? game.categories.map((category) => category.name).join(" / ")
    : game.category_name || "未分类";
  const gameSize = extractGameSize(game.summary);

  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className="game-card"
      initial={{ opacity: 0, y: 18 }}
      layout
      transition={{ duration: 0.25 }}
    >
      <img alt={`${game.title} 封面`} src={game.cover_url} />
      <div className="game-card__content">
        <h3>{game.title}</h3>
        <div className="game-card__facts">
          <div>
            <span>类型</span>
            <strong>{categoryNames}</strong>
          </div>
          {game.release_year ? (
            <div>
              <span>年份</span>
              <strong>{game.release_year}</strong>
            </div>
          ) : null}
        </div>
        <div className="tag-list game-card__tags">
          <span>{game.categories[0]?.name || categoryNames}</span>
          {gameSize ? <span>{gameSize}</span> : null}
        </div>
        <button
          className="icon-text-button"
          type="button"
          onClick={() => onOpen(game.slug)}
        >
          <Eye size={16} />
          查看详情
        </button>
      </div>
    </motion.article>
  );
}

function extractGameSize(text: string): string {
  const matchedSize = text.match(/资源大小：([^。，\n]+)/);
  const size = matchedSize?.[1]?.trim() || "";
  return size && size !== "未知" && size !== "未知大小" ? size : "";
}
