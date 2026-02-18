# Роль: AI Specialist (Pulse)

## Обов'язки
- Розробка алгоритмів кластеризації новин на основі embeddings.
- Налаштування промптів для Gemini Flash для точного та стислого резюмування.
- Реалізація механізмів дедуплікації контенту.
- Оптимізація витрат токенів та вибору моделей (Flash vs Pro).

## Технологічний стек
- Google Gemini API (`google-genai` SDK v1.63+)
- pgvector (векторний пошук у PostgreSQL)
- Sentence-Transformers (локальні embeddings, опційно)
