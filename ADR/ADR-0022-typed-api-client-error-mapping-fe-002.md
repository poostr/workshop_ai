# ADR-0022: Типизированный API-клиент и централизованный маппинг ошибок (FE-002)

## Статус

Принято.

## Контекст

После FE-001 API-клиент содержал полный набор методов для всех endpoint'ов v1, а i18n-словари включали маппинг всех кодов ошибок backend. Однако оставались два недочёта:

1. Метод `importState` принимал `data: unknown` — отсутствовала типизация тела запроса на импорт.
2. Паттерн извлечения локализованного сообщения из ошибки (`if (err instanceof ApiClientError) ... t(\`errors.${err.code}\`) ... else t("errors.ERR_UNKNOWN")`) дублировался в трёх страницах.

## Решения

### 1. Типизация ImportRequest

Добавлены интерфейсы `ImportRequest`, `ImportTypeItem`, `ImportStageCount`, `ImportHistoryItem` в `shared/api/types.ts`, зеркалящие Pydantic-схемы backend (`ImportRequest`, `ImportTypeItem`, `ImportStageCount`, `ImportHistoryItem`). Сигнатура `importState` обновлена с `unknown` на `ImportRequest`.

Альтернатива — переиспользование `ExportResponse` как типа входа для импорта (структуры идентичны) — отклонена, чтобы сохранить семантическое разделение: экспорт = ответ сервера, импорт = запрос клиента. При расхождении контрактов в будущем изменения затронут только один из типов.

### 2. Централизованный хелпер `getLocalizedErrorMessage`

Выделена функция `getLocalizedErrorMessage(err: unknown, t: TFunction): string` в `shared/api/errors.ts`. Она инкапсулирует логику определения типа ошибки и маппинга кода через i18n:

- `ApiClientError` → `t(\`errors.${code}\`, { defaultValue: message })`
- Прочее → `t("errors.ERR_UNKNOWN")`

Все три страницы (`MainPage`, `CreateTypePage`, `TypeDetailsPage`) переведены на использование этого хелпера, исключив дублирование.

## Последствия

- Добавление нового кода ошибки требует изменения только в i18n-словарях — обработка в компонентах уже универсальна.
- При вызове `importState` TypeScript гарантирует корректную структуру тела запроса.
- Единая точка маппинга ошибок упрощает тестирование и расширение (например, добавление toast-нотификаций).
