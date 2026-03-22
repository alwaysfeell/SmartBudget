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

## Developer Quick Start
 
> Покрокова інструкція для розробника зі свіжою ОС — від нуля до запущеного проєкту.
 
### 1. Необхідні залежності та програмне забезпечення
 
Перед початком встановіть наступні програми:
 
| Програма | Мінімальна версія | Де завантажити |
|-|-|-|
| Python | 3.10+ | https://python.org/downloads |
| Git | будь-яка | https://git-scm.com/downloads |
 
**Встановлення Python (Windows):**
1. Перейдіть на https://python.org/downloads і завантажте останній Python 3.x
2. Запустіть інсталятор — **обов'язково поставте галочку «Add Python to PATH»**
3. Перевірте встановлення у командному рядку:
```
python --version
```
 
**Встановлення Python (macOS/Linux):**
```bash
# macOS (через Homebrew)
brew install python@3.10
 
# Ubuntu / Debian
sudo apt update && sudo apt install python3.10 python3.10-venv python3-pip git -y
```
 
Перевірте встановлення:
```bash
python3 --version
git --version
```

---
 
### 2. Клонування репозиторію
 
```bash
git clone https://github.com/alwaysfeell/SmartBudget.git
cd SmartBudget
```
 
Після цього ви знаходитесь у кореневій папці проєкту.

---
 
### 3. Налаштування середовища розробки
 
Створіть ізольоване віртуальне середовище Python, щоб залежності проєкту не конфліктували з системними пакетами:
 
**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
 
**Windows (cmd):**
```
python -m venv venv
venv\Scripts\activate
```
 
**Windows (PowerShell):**
```
python -m venv venv
venv\Scripts\Activate.ps1
```
 
Після активації у терміналі з'явиться префікс `(venv)` — це означає, що середовище активоване і всі наступні команди `pip` встановлюватимуть пакети лише у нього.
 
> **Важливо:** активуйте `venv` кожного разу при поверненні до роботи над проєктом.

---
 
### 4. Встановлення та конфігурація залежностей
 
Встановіть усі необхідні Python-пакети:
 
```bash
pip install -r requirements.txt
```
 
Для розробки (лінтери, перевірка типів, документація) — додатково:
 
```bash
pip install -r requirements-dev.txt
```
 
Або одразу все через Makefile:
 
```bash
make install
```
 
Перевірте, що Flask встановлено коректно:
 
```bash
python -c "import flask; print(flask.__version__)"
```
 
**Налаштування змінних середовища (опціонально):**
 
За замовчуванням проєкт запускається з налаштуваннями з `config.py`. Якщо потрібно змінити поведінку — створіть файл `.env` у корені проєкту:
 
```env
SECRET_KEY=your-secret-key-here
DATABASE=smartbudget.db
DEBUG=true
```
 
> Файл `.env` вже додано до `.gitignore` — він не потрапить у репозиторій.

---
 
### 5. Створення та налаштування бази даних
 
SmartBudget використовує SQLite — **окремої установки сервера БД не потрібно**. База даних створюється автоматично при першому запуску застосунку.
 
Файл бази: `smartbudget.db` у корені проєкту (не зберігається у репозиторії, є в `.gitignore`).
 
При запуску автоматично виконується:
- Створення таблиць `expenses`, `users`, `goals`
- Заповнення тестовими (seed) даними для демонстрації
 
Якщо потрібно скинути базу вручну:
```bash
rm smartbudget.db
python app.py   # база створиться знову
```

---
### 6. Запуск проєкту у режимі розробки
 
```bash
make run
```
 
Або без Makefile:
 
```bash
python app.py
```
 
Відкрийте браузер і перейдіть за адресою:
 
```
http://127.0.0.1:5000
```
 
Ви побачите дашборд SmartBudget із демо-даними. Flask автоматично перезапускається при зміні файлів (режим `DEBUG=true`).

---

### 7. Базові команди та операції
 
| Команда | Призначення |
|-|-|
| `make run` | Запустити Flask у dev-режимі |
| `make lint` | Статичний аналіз коду (lint.py) |
| `make typecheck` | Перевірка типів (mypy) |
| `make check` | Lint + typecheck разом |
| `make docs` | Згенерувати HTML-документацію (Sphinx) |
| `make doccheck` | Перевірити якість docstrings (pydocstyle) |
| `make clean` | Видалити `__pycache__` |
| `make install` | Встановити всі залежності (prod + dev) |
 
**Запуск лінтера вручну:**
```bash
python lint.py .
```
 
**Перевірка типів вручну:**
```bash
mypy app.py models/ controllers/
```
 
**Генерація документації вручну:**
```bash
sphinx-build -b html docs_sphinx docs_html
# Відкрийте docs_html/index.html у браузері
```

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
 
## Документування коду
 
Стандарт проєкту — **Google-style docstrings** (PEP 257).
 
### Правила для розробників
 
- Кожна публічна функція та метод повинні мати docstring
- Docstring містить: короткий опис, блок `Args:` з параметрами, блок `Returns:` з типом та описом
- Алгоритмічні функції (forecast, generate_advice) — додатково описувати блок `Algorithm:`
- При зміні сигнатури функції — оновити docstring в тому ж коміті
- Приватні функції (починаються з `_`) — docstring за бажанням
 
### Приклад правильного docstring
 
```python
def get_stats(db) -> dict:
    """Return budget statistics for the current and previous month.
 
    Args:
        db: Active SQLite database connection (flask.g.db).
 
    Returns:
        dict: Keys: budget, spent, spent_prev, pct_change,
              remaining, budget_pct, savings, total_purchases.
    """
```
 
### Генерація HTML-документації
 
```bash
# Встановити інструменти (одноразово)
pip install sphinx sphinx-rtd-theme pydocstyle
 
# Згенерувати документацію
sphinx-build -b html docs_sphinx docs_html
 
# Або через Makefile
make docs
 
# Перевірити якість docstrings
make doccheck
```
 
Документація генерується у папку `docs_html/` — відкрийте `docs_html/index.html` у браузері.  
Детальна інструкція: [docs/generate_docs.md](docs/generate_docs.md)
---
 
## Ліцензія

Цей проєкт розповсюджується під ліцензією [MIT](LICENSE).