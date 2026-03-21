# Генерація документації — SmartBudget

## Інструмент: Sphinx + Napoleon

Для генерації HTML-документації з docstrings використовується **Sphinx** із розширенням **Napoleon** (підтримка Google/NumPy стилю docstrings).

## Встановлення залежностей

```bash
pip install sphinx sphinx-rtd-theme
```

## Структура конфігурації

```
docs_sphinx/
├── conf.py          # Налаштування Sphinx
├── index.rst        # Головна сторінка
└── modules/         # RST-файли для кожного модуля
```

## Запуск генерації

```bash
# З кореня проєкту
sphinx-build -b html docs_sphinx docs_html
```

Або через Makefile:
```bash
make docs
```

## Перегляд документації

Відкрийте `docs_html/index.html` у браузері.

## Перевірка якості документації

```bash
# pydocstyle — перевірка стилю docstrings
pip install pydocstyle
pydocstyle models/ controllers/ database.py

# Або через Makefile
make doccheck
```

## Оновлення документації

При будь-якій зміні публічного інтерфейсу функцій/класів — оновіть docstring та перегенеруйте:
```bash
make docs
```
