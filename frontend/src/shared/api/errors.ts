import type { TFunction } from "i18next";

import { ApiClientError } from "./client";

/**
 * Maps an unknown caught error to a user-facing localized message.
 * ApiClientError codes are resolved via i18n `errors.<code>` keys;
 * unrecognised codes fall back to the raw server message.
 */
export function getLocalizedErrorMessage(
  err: unknown,
  t: TFunction,
): string {
  if (err instanceof ApiClientError) {
    return t(`errors.${err.code}`, { defaultValue: err.message });
  }
  return t("errors.ERR_UNKNOWN");
}
