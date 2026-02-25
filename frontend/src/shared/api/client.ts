import type {
  ApiErrorResponse,
  ExportResponse,
  ImportRequest,
  ImportResponse,
  TypeCreateRequest,
  TypeHistoryResponse,
  TypeListItem,
  TypeListResponse,
  TypeMoveRequest,
} from "./types";

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

  public async listTypes(): Promise<TypeListResponse> {
    return this.request<TypeListResponse>("/types");
  }

  public async createType(body: TypeCreateRequest): Promise<TypeListItem> {
    return this.request<TypeListItem>("/types", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  public async getType(typeId: number): Promise<TypeListItem> {
    return this.request<TypeListItem>(`/types/${typeId}`);
  }

  public async moveType(
    typeId: number,
    body: TypeMoveRequest,
  ): Promise<TypeListItem> {
    return this.request<TypeListItem>(`/types/${typeId}/move`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  public async getTypeHistory(
    typeId: number,
  ): Promise<TypeHistoryResponse> {
    return this.request<TypeHistoryResponse>(`/types/${typeId}/history`);
  }

  public async exportState(): Promise<ExportResponse> {
    return this.request<ExportResponse>("/export");
  }

  public async importState(data: ImportRequest): Promise<ImportResponse> {
    return this.request<ImportResponse>("/import", {
      method: "POST",
      body: JSON.stringify(data),
    });
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
      const message = payload?.message ?? "Request failed";

      throw new ApiClientError(message, code);
    }

    return (await response.json()) as T;
  }
}

export const apiClient = new ApiClient();
