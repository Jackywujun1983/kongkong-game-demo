import { AnimatePresence, motion } from "framer-motion";
import { Calendar, HardDrive, Star, X } from "lucide-react";
import type { SyntheticEvent } from "react";

import type { GameDetail } from "../../types/domain";

const DEFAULT_COVER_URL = "/assets/covers/default-game-cover.jpg";
const LEGACY_PLACEHOLDER_URL = "/assets/covers/game-placeholder.png";

interface GameDetailPanelProps {
  game: GameDetail | null;
  onClose: () => void;
}

export function GameDetailPanel({ game, onClose }: GameDetailPanelProps) {
  const categoryNames = game?.categories.length
    ? game.categories.map((category) => category.name).join(" / ")
    : game?.category_name || "未分类";
  const gameSize = game ? extractGameSize(game.summary || game.details) : "";

  return (
    <AnimatePresence>
      {game ? (
        <motion.aside
          animate={{ opacity: 1, x: 0 }}
          className="detail-panel"
          exit={{ opacity: 0, x: 32 }}
          initial={{ opacity: 0, x: 32 }}
          transition={{ duration: 0.24 }}
        >
          <button
            aria-label="关闭详情"
            className="icon-button detail-panel__close"
            type="button"
            onClick={onClose}
          >
            <X size={18} />
          </button>
          <img
            alt={`${game.title} 封面`}
            src={normalizeCoverUrl(game.cover_url)}
            onError={useDefaultCover}
          />
          <div className="detail-panel__body">
            <span className="eyebrow">{categoryNames}</span>
            <h2>{game.title}</h2>
            <div className="download-address">
              <span className="download-address-label">下载地址</span>
              {game.download_url ? (
                <span className="detail-download-link">{game.download_url}</span>
              ) : (
                <span>暂无下载地址</span>
              )}
            </div>
            <div className="detail-stats">
              <span>
                <Star size={16} />
                {game.rating.toFixed(1)}
              </span>
              <span>
                <Calendar size={16} />
                {game.release_year}
              </span>
              <span>
                <HardDrive size={16} />
                {gameSize || "未标注"}
              </span>
            </div>
          </div>
        </motion.aside>
      ) : null}
    </AnimatePresence>
  );
}

function extractGameSize(text: string): string {
  const matchedSize = text.match(/资源大小：([^。，\n]+)/);
  const size = matchedSize ? matchedSize[1].trim() : "";
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
