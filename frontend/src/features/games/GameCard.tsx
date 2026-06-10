import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import type { SyntheticEvent } from "react";

import type { GameSummary } from "../../types/domain";

const DEFAULT_COVER_URL = "/assets/covers/default-game-cover.jpg";
const LEGACY_PLACEHOLDER_URL = "/assets/covers/game-placeholder.png";

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
      <img
        alt={`${game.title} 封面`}
        src={normalizeCoverUrl(game.cover_url)}
        onError={useDefaultCover}
      />
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
        {gameSize ? (
          <div className="tag-list game-card__tags">
            <span>{gameSize}</span>
          </div>
        ) : null}
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

function useDefaultCover(event: SyntheticEvent<HTMLImageElement>): void {
  event.currentTarget.onerror = null;
  event.currentTarget.src = DEFAULT_COVER_URL;
}

function normalizeCoverUrl(coverUrl: string): string {
  const normalizedCoverUrl = coverUrl.trim();
  if (
    !normalizedCoverUrl ||
    normalizedCoverUrl === LEGACY_PLACEHOLDER_URL ||
    normalizedCoverUrl === "/public/assets/covers/game-placeholder.png" ||
    normalizedCoverUrl === "./public/assets/covers/game-placeholder.png"
  ) {
    return DEFAULT_COVER_URL;
  }
  if (normalizedCoverUrl.startsWith("/public/")) {
    return normalizedCoverUrl.replace("/public", "");
  }
  if (normalizedCoverUrl.startsWith("./public/")) {
    return normalizedCoverUrl.replace("./public", "");
  }
  return normalizedCoverUrl;
}
