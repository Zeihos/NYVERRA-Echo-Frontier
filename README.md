# NYVERRA: Echo Frontier

**Private development repository — UE5.8 / Windows / multiplayer / PvPvE / seasonal wipes.**

## Состав

- `NYVERRA.uproject`, `Source/`, `Config/`, `Content/`, `Tools/` и прочие файлы корня — актуальные исходники **Alpha 0.52** (без временного Python-кэша).
- `History/UE5_Alpha_Archives/` — все **52 исходных ZIP-архива Alpha 0.1–0.52**, сохранённые без изменений.
- `History/Early_2D_Prototype/` — оригинальный ранний 2D-прототип, для истории, **не** основная игра.
- `Documentation/` — утверждённые GDD v1.0 и техническое задание v1.0 в формате DOCX.
- `HISTORY_CHECKSUMS_SHA256.txt` — контрольные суммы версий для проверки архива.
- `PUSH_TO_GITHUB_PRIVATE.bat` — отправка локальных файлов в **уже созданный** приватный GitHub-репозиторий.

## Состояние проекта

Alpha 0.52 содержит **экспериментальные исходники** Unreal Engine. Полная компиляция в UE5.8, мультиплеерные тесты и запуск на Windows **не подтверждены**. Отсутствует готовый сохранённый `.umap` игрового уровня. Не заявлять готовность к релизу до реальной проверки.

## Разработка

1. Установить Unreal Engine 5.8, Visual Studio с C++ toolchain.
2. Открыть `NYVERRA.uproject` и выполнить сборку модуля редактора.
3. Записать журнал компиляции и исправить ошибки, если они появятся.
4. Создать и сохранить тестовую `.umap` карту, затем проверить игру с двумя клиентами.

## GitHub

**Репозиторий для отправки:** `Zeihos/NYVERRA-Echo-Frontier` (Private). Запустите `PUSH_TO_GITHUB_PRIVATE.bat` после распаковки всего архива. Инструкции см. `GITHUB_UPLOAD_INSTRUCTIONS_RU.txt`.
