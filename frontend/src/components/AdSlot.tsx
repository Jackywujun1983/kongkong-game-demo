import type { AdItem } from "../types/domain";

interface AdSlotProps {
  ad?: AdItem;
  compact?: boolean;
}

export function AdSlot({ ad, compact = false }: AdSlotProps) {
  if (!ad) {
    return (
      <section className={`ad-slot ${compact ? "ad-slot--compact" : ""}`}>
        <span>广告位预留</span>
      </section>
    );
  }

  return (
    <a
      className={`ad-slot ${compact ? "ad-slot--compact" : ""}`}
      href={ad.target_url}
      style={{ backgroundImage: `url(${ad.image_url})` }}
    >
      <span>{ad.title}</span>
      <strong>{ad.description}</strong>
    </a>
  );
}

