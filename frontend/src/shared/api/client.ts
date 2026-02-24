import type { ApiErrorResponse } from "./types";

const DEFAULT_API_BASE_URL = "/api/v1";

export class ApiClientError extends Error {
  public readonly code: string;

  public constructor(message: string, code: string) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
  }
}

export class ApiClient {
  public constructor(private readonly baseUrl = DEFAULT_API_BASE_URL) {}

  public async getStatus(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/status");
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
      ...init,
    });

    if (!response.ok) {
      const payload = (await response
        .json()
        .catch(() => null)) as ApiErrorResponse | null;
      const code = payload?.code ?? "ERR_UNKNOWN";
      const detail = payload?.detail ?? "Request failed";

      throw new ApiClientError(detail, code);
    }

    return (await response.json()) as T;
  }
}

export const apiClient = new ApiClient();
