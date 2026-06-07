import { API_BASE_URL } from "../config/env";
import type {
  AdItem,
  Category,
  GameDetail,
  GameSearchResult,
} from "../types/domain";

interface ApiListResponse<T> {
  items: T[];
}

interface GameSearchParams {
  query?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getCategories(): Promise<Category[]> {
  const response = await apiRequest<ApiListResponse<Category>>("/categories");
  return response.items;
}

export async function searchGames(
  params: GameSearchParams = {},
): Promise<GameSearchResult> {
  const searchParams = new URLSearchParams();
  if (params.query) {
    searchParams.set("query", params.query);
  }
  if (params.category) {
    searchParams.set("category", params.category);
  }
  if (params.page) {
    searchParams.set("page", String(params.page));
  }
  if (params.pageSize) {
    searchParams.set("page_size", String(params.pageSize));
  }

  const queryString = searchParams.toString();
  return apiRequest<GameSearchResult>(
    `/games${queryString ? `?${queryString}` : ""}`,
  );
}

export function getGame(slug: string): Promise<GameDetail> {
  return apiRequest<GameDetail>(`/games/${slug}`);
}

export async function getAds(placement?: string): Promise<AdItem[]> {
  const queryString = placement ? `?placement=${encodeURIComponent(placement)}` : "";
  const response = await apiRequest<ApiListResponse<AdItem>>(`/ads${queryString}`);
  return response.items;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as {
      error?: string;
    };
    throw new ApiError(
      errorPayload.error ?? "Request failed",
      response.status,
    );
  }

  return (await response.json()) as T;
}
