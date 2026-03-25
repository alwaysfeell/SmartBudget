# Логування та обробка помилок — SmartBudget

## Огляд

SmartBudget використовує стандартний модуль `logging` Python з трьома обробниками:

| Обробник | Файл | Ротація | Рівень |
|---|---|---|---|
| Console | stdout | — | LOG_LEVEL |
| RotatingFileHandler | `logs/smartbudget.log` | 5 MB × 5 копій | LOG_LEVEL |
| TimedRotatingFileHandler | `logs/errors.log` | щодня, 30 днів | ERROR |

---

## Рівні логування

| Рівень | Коли використовується |
|---|---|
| DEBUG | HTTP-запити, SQL-деталі, алгоритмічні кроки |
| INFO | Старт/зупинка, ініціалізація БД, успішні операції |
| WARNING | 404, невалідні форми, некритичні відхилення |
| ERROR | Виняток перехоплено, операція не завершилась |
| CRITICAL | Недоступна БД, неможливо запустити застосунок |

---

## Зміна рівня без перекомпіляції

```bash
# Через змінну оточення
LOG_LEVEL=DEBUG python app.py

# Через .env файл (рекомендовано для production)
echo "LOG_LEVEL=WARNING" >> .env
```
---

## Унікальні ідентифікатори помилок

Кожна ERROR-подія отримує унікальний `error_id` (8 символів, UUID4):

```
2025-03-20 14:32:01 | ERROR    | app | Unexpected error | error_id=A3F7C1B2 | type=KeyError | path=/expenses
```

Цей ID показується користувачеві на сторінці помилки та зберігається в `logs/errors.log`.

---

## Запуск та перегляд логів

```bash
# Перегляд основного логу в реальному часі
tail -f logs/smartbudget.log

# Перегляд лише помилок
tail -f logs/errors.log

# Фільтрація за рівнем
grep "| ERROR" logs/smartbudget.log

# Пошук за error_id
grep "error_id=A3F7C1B2" logs/smartbudget.log
```
---

## Структура рядка логу

```
2025-03-20 14:32:01 | INFO     | controllers.expenses | Expense saved | id=42 | user=1
│                     │          │                       │
│                     │          │                       └── Повідомлення + контекст
│                     │          └── Ім'я модуля (__name__)
│                     └── Рівень (вирівняний до 8 символів)
└── Дата та час (ISO формат)
```
---

## make-цілі

```bash
make logs      # переглянути останні 50 рядків smartbudget.log
make logsclean # видалити всі файли логів
```
