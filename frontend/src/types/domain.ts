export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  game_count: number;
  is_visible: boolean;
}

export interface GameSummary {
  id: number;
  title: string;
  slug: string;
  studio: string;
  release_year: number;
  rating: number;
  cover_url: string;
  download_url: string;
  summary: string;
  platforms: string[];
  tags: string[];
  category_name: string;
  category_slug: string;
  categories: Category[];
}

export interface GameDetail extends GameSummary {
  details: string;
}

export interface GameSearchResult {
  items: GameSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface AdItem {
  id: number;
  placement: string;
  title: string;
  description: string;
  image_url: string;
  target_url: string;
}
