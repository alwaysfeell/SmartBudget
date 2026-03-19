# SmartBudget

**Інформаційна система підтримки прийняття рішень щодо споживчих витрат**

Дипломний проект | Python + Flask + SQLite + Bootstrap 5

---

## Стек технологій

|Шар|Технологія|
|-|-|
|Backend|Python 3.10+ / Flask 3.x|
|База даних|SQLite (через вбудований `sqlite3`)|
|Аналіз|pandas 2.x|
|Frontend|HTML5 + CSS3 + Bootstrap 5.3|
|Графіки|Chart.js 4.x (CDN)|

---

## Архітектура (MVC)

Проект побудований за патерном **Model–View–Controller**:

|Шар|Папка/файл|Відповідальність|
|-|-|-|
|Model|`models/`|Бізнес-логіка, алгоритми аналізу, робота з БД|
|View|`templates/`|HTML-шаблони (Jinja2 + Bootstrap)|
|Controller|`controllers/`|HTTP-маршрути (Blueprint), виклик моделей|

---

## Структура проекту

```
smartbudget/
├── app.py                  # Точка входу: Flask init + реєстрація Blueprint
├── config.py               # Налаштування (SECRET\_KEY, DATABASE, DEBUG)
├── database.py             # Підключення до БД, ініціалізація, seed-дані
├── requirements.txt
├── .gitignore
├── LICENSE
│
├── models/                 # Бізнес-логіка (Model)
│   ├── utils.py            # Спільні хелпери (rows\_to\_df, month\_short, get\_budget)
│   ├── stats.py            # Загальна статистика для дашборду
│   ├── charts.py           # Дані для графіків Chart.js
│   ├── prices.py           # Порівняння цін по магазинах
│   ├── advice.py           # Генерація рекомендацій (6 алгоритмів)
│   └── dss/                # Ядро DSS
│       ├── forecast.py     # Прогноз витрат (МНК + сезонність)
│       ├── scenarios.py    # Сценарний аналіз A/B/C
│       ├── budget\_rule.py  # Правило 50/30/20
│       └── quality.py      # Оцінка якості даних
│
├── controllers/            # HTTP-маршрути (Controller)
│   ├── main.py             # GET /  та  GET /api/charts
│   ├── expenses.py         # GET|POST /expenses/\*
│   ├── analysis.py         # GET /analysis/\*
│   ├── recommendations.py  # GET /recommendations
│   ├── dss.py              # GET /dss
│   ├── profile.py          # GET|POST /profile/\*
│   └── goals.py            # GET|POST /goals/\*
│
└── templates/              # HTML-шаблони (View)
    ├── base.html
    ├── index.html
    ├── expenses.html
    ├── analysis.html
    ├── recommendations.html
    ├── dss.html
    ├── goals.html
    └── profile.html
```

---

## Встановлення та запуск

### 1\. Розпакувати проект

```bash
cd smartbudget
```

### 2\. Створити віртуальне середовище

```bash
python -m venv venv
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate
```

### 3\. Встановити залежності

```bash
pip install -r requirements.txt
```

### 4\. Налаштування змінних середовища (опціонально)

Створіть файл `.env` у корені проєкту:

```env
SECRET\_KEY=your-secret-key-here
DATABASE=smartbudget.db
DEBUG=false
```

> Файл `.env` не додається до репозиторію (є в `.gitignore`)

### 5\. Запустити застосунок

```bash
python app.py
```

### 6\. Відкрити у браузері

```
http://localhost:5000
```

БД та демо-дані створюються автоматично при першому запуску (`smartbudget.db` не зберігається в репозиторії).

---

## Функціонал

### Дашборд (`/`)

* Карточки: бюджет, витрати, потенційна економія, кількість покупок
* Стовпчаста діаграма витрат по тижнях (розбита по категоріях)
* Кругова діаграма часток категорій
* Таблиця останніх 5 покупок
* Прогрес-бар використання бюджету
* AI-порада — динамічно через AJAX

### Витрати (`/expenses`)

* Додавання покупки: назва, категорія, ціна, кількість, магазин, дата
* Серверна валідація назви, дати, ціни
* Фільтр по категорії, видалення записів

### Аналіз цін (`/analysis`)

* Порівняльна таблиця цін по магазинах
* Підсвічування мінімальної ціни
* Фільтр по категорії та магазину
* AJAX-генерація поради

### Рекомендації (`/recommendations`)

* Персональні поради на основі 6 алгоритмів
* Графік реальної та потенційної економії
* Топ товарів з найбільшою різницею цін

### DSS — підтримка рішень (`/dss`)

* **Прогноз** на 3 місяці (лінійна регресія МНК + сезонні коефіцієнти)
* **Сценарний аналіз**: A (оптимістичний), B (базовий), C (песимістичний +7% інфляція)
* **Правило 50/30/20**: розподіл витрат по кошиках із відхиленнями
* **Якість даних**: scoring-метрики покриття, різноманіття, глибини історії

### Цілі (`/goals`)

* Фінансові цілі з прогрес-баром накопичення
* Калькулятор строку досягнення цілі (AJAX)
* Поповнення та видалення цілей

### Профіль (`/profile`)

* Редагування імені, email, міста
* Налаштування місячного бюджету та валюти

---
## База даних (SQLite)
### Таблиця `expenses`
|Поле|Тип|Опис|
|-|-|-|
|id|INTEGER|Первинний ключ (auto)|
|name|TEXT|Назва товару|
|category|TEXT|Категорія|
|price|REAL|Ціна за одиницю|
|store|TEXT|Магазин|
|date|TEXT|Дата покупки (YYYY-MM-DD)|
|qty|INTEGER|Кількість|
|created\_at|TEXT|Час запису|

### Таблиця `users`

|Поле|Тип|Опис|
|-|-|-|
|id|INTEGER|завжди = 1|
|first\_name|TEXT|Ім'я|
|last\_name|TEXT|Прізвище|
|email|TEXT|Email|
|city|TEXT|Місто|
|budget|REAL|Місячний бюджет|
|currency|TEXT|Символ валюти|

### Таблиця `goals`

|Поле|Тип|Опис|
|-|-|-|
|id|INTEGER|Первинний ключ (auto)|
|title|TEXT|Назва цілі|
|target\_amount|REAL|Цільова сума|
|saved\_amount|REAL|Накопичено|
|monthly\_save|REAL|Плановий місячний внесок|
|deadline|TEXT|Дата дедлайну|
|category|TEXT|Категорія|
|icon|TEXT|Іконка|
|color|TEXT|Колір|
|created\_at|TEXT|Час створення|

---

## API ендпоінти

|Метод|URL|Опис|
|-|-|-|
|GET|`/`|Дашборд|
|GET|`/api/charts`|JSON: дані для графіків|
|GET|`/expenses/`|Список витрат|
|POST|`/expenses/add`|Додати витрату|
|POST|`/expenses/delete/<id>`|Видалити витрату|
|GET|`/analysis/`|Аналіз цін|
|GET|`/analysis/advice`|JSON: порада системи|
|GET|`/recommendations`|Рекомендації|
|GET|`/dss`|DSS-аналітика|
|GET|`/goals/`|Фінансові цілі|
|POST|`/goals/add`|Додати ціль|
|POST|`/goals/deposit/<id>`|Поповнити ціль|
|POST|`/goals/delete/<id>`|Видалити ціль|
|POST|`/goals/calc`|JSON: розрахунок калькулятора|
|GET|`/profile`|Особистий кабінет|

---

## Ліцензія

Цей проєкт розповсюджується під ліцензією [MIT](LICENSE).

