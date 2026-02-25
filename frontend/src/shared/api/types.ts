export type StageCode =
  | "IN_BOX"
  | "BUILDING"
  | "PRIMING"
  | "PAINTING"
  | "DONE";

export const STAGES: readonly StageCode[] = [
  "IN_BOX",
  "BUILDING",
  "PRIMING",
  "PAINTING",
  "DONE",
] as const;

export const STAGE_INDEX: Record<StageCode, number> = {
  IN_BOX: 0,
  BUILDING: 1,
  PRIMING: 2,
  PAINTING: 3,
  DONE: 4,
};

export type ApiErrorCode =
  | "ERR_INSUFFICIENT_QTY"
  | "ERR_INVALID_STAGE_TRANSITION"
  | "ERR_DUPLICATE_TYPE_NAME"
  | "ERR_INVALID_STAGE"
  | "ERR_INVALID_IMPORT_FORMAT"
  | "ERR_VALIDATION";

export interface ApiErrorResponse {
  code: ApiErrorCode | string;
  message: string;
}

export interface TypeStageCounts {
  in_box: number;
  building: number;
  priming: number;
  painting: number;
  done: number;
}

export interface TypeListItem {
  id: number;
  name: string;
  counts: TypeStageCounts;
}

export interface TypeListResponse {
  items: TypeListItem[];
}

export interface TypeHistoryGroup {
  from_stage: StageCode;
  to_stage: StageCode;
  qty: number;
  timestamp: string;
}

export interface TypeHistoryResponse {
  items: TypeHistoryGroup[];
}

export interface ExportStageCount {
  stage: StageCode;
  count: number;
}

export interface ExportHistoryItem {
  from_stage: StageCode;
  to_stage: StageCode;
  qty: number;
  created_at: string;
}

export interface ExportTypeItem {
  name: string;
  stage_counts: ExportStageCount[];
  history: ExportHistoryItem[];
}

export interface ExportResponse {
  types: ExportTypeItem[];
}

export interface ImportStageCount {
  stage: StageCode;
  count: number;
}

export interface ImportHistoryItem {
  from_stage: StageCode;
  to_stage: StageCode;
  qty: number;
  created_at: string;
}

export interface ImportTypeItem {
  name: string;
  stage_counts: ImportStageCount[];
  history: ImportHistoryItem[];
}

export interface ImportRequest {
  types: ImportTypeItem[];
}

export interface ImportResponse {
  status: string;
}

export interface TypeCreateRequest {
  name: string;
}

export interface TypeMoveRequest {
  from_stage: StageCode;
  to_stage: StageCode;
  qty: number;
}
