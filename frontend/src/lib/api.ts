import type {
  DashboardSummary,
  Item,
  ItemCreateInput,
  ItemUpdateInput,
} from "../types/api";

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function buildUrl(path: string, searchParams?: URLSearchParams): string {
  const url = new URL(`${apiBaseUrl}${path}`);
  if (searchParams) {
    url.search = searchParams.toString();
  }
  return url.toString();
}

async function request<T>(path: string, init?: RequestInit, searchParams?: URLSearchParams): Promise<T> {
  const response = await fetch(buildUrl(path, searchParams), {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
        ? data.detail
        : `Request failed with status ${response.status}`;
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/dashboard/summary");
}

export async function fetchItems(filters?: { search?: string; category?: string }): Promise<Item[]> {
  const searchParams = new URLSearchParams();

  if (filters?.search) {
    searchParams.set("search", filters.search);
  }

  if (filters?.category) {
    searchParams.set("category", filters.category);
  }

  return request<Item[]>("/items", undefined, searchParams);
}

export async function createItem(payload: ItemCreateInput): Promise<Item> {
  return request<Item>("/items", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateItem(itemId: number, payload: ItemUpdateInput): Promise<Item> {
  return request<Item>(`/items/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteItem(itemId: number): Promise<void> {
  return request<void>(`/items/${itemId}`, {
    method: "DELETE",
  });
}
