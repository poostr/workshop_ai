export type ApiErrorCode =
  | "ERR_INSUFFICIENT_QTY"
  | "ERR_INVALID_STAGE_TRANSITION"
  | "ERR_DUPLICATE_TYPE_NAME"
  | "ERR_INVALID_STAGE"
  | "ERR_INVALID_IMPORT_FORMAT";

export interface ApiErrorResponse {
  code: ApiErrorCode | string;
  detail?: string;
}
