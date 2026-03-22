# Оновлення SmartBudget

> Документ призначений для release engineer / DevOps.

---

## 1. Підготовка до оновлення

### 1.1. Резервне копіювання

Перед будь-яким оновленням обов'язково зробіть резервну копію:

```bash
# Резервна копія бази даних
sudo -u smartbudget cp /opt/smartbudget/data/smartbudget.db \
    /opt/smartbudget/data/smartbudget.db.bak.$(date +%Y%m%d_%H%M%S)

# Резервна копія конфігурації
sudo cp /opt/smartbudget/app/.env \
    /opt/smartbudget/app/.env.bak.$(date +%Y%m%d_%H%M%S)
```

Або за допомогою скрипту:

```bash
bash /opt/smartbudget/app/scripts/backup.sh
```

### 1.2. Перевірка сумісності

```bash
cd /opt/smartbudget/app
sudo -u smartbudget git fetch origin
# Переглянути зміни перед оновленням
sudo -u smartbudget git log HEAD..origin/main --oneline
# Переглянути зміни в requirements.txt
sudo -u smartbudget git diff HEAD origin/main -- requirements.txt
```

### 1.3. Планування часу простою

SmartBudget — статичний Flask-додаток без кластеризації. Час простою при оновленні: **~30–60 секунд** (перезапуск Gunicorn). Рекомендований час оновлення: нічні години або вихідні.

---

## 2. Процес оновлення

### 2.1. Зупинка служби

```bash
sudo systemctl stop smartbudget
```

### 2.2. Розгортання нового коду

```bash
cd /opt/smartbudget/app
sudo -u smartbudget git pull origin main
```

### 2.3. Оновлення залежностей

```bash
sudo -u smartbudget /opt/smartbudget/venv/bin/pip install -r requirements.txt
```

### 2.4. Міграція даних (за потреби)

SmartBudget використовує SQLite і не має ORM-міграцій. Якщо нова версія змінює схему БД — у release notes буде вказано SQL-скрипт. Приклад:

```bash
sudo -u smartbudget /opt/smartbudget/venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('/opt/smartbudget/data/smartbudget.db')
# Застосувати SQL-зміни з release notes
conn.execute('ALTER TABLE expenses ADD COLUMN tags TEXT DEFAULT NULL')
conn.commit()
conn.close()
print('Migration complete')
"
```

### 2.5. Оновлення конфігурації

Якщо з'явились нові змінні середовища (перевіряйте CHANGELOG):

```bash
sudo nano /opt/smartbudget/app/.env
# Додати нові змінні
```

### 2.6. Запуск служби

```bash
sudo systemctl start smartbudget
sudo systemctl status smartbudget
```

---

## 3. Перевірка після оновлення

```bash
# HTTP-відповідь
curl -I http://localhost:5000

# Версія (якщо є endpoint)
curl http://localhost:5000/api/health

# Логи на наявність помилок
sudo journalctl -u smartbudget --since "5 minutes ago"
```

---

## 4. Процедура відкату (rollback)

Якщо оновлення пройшло невдало:

### 4.1. Відкат коду

```bash
sudo systemctl stop smartbudget
cd /opt/smartbudget/app

# Переглянути попередні коміти
sudo -u smartbudget git log --oneline -10

# Відкатитись до попереднього коміту
sudo -u smartbudget git checkout <попередній-хеш>

# Відновити залежності попередньої версії
sudo -u smartbudget /opt/smartbudget/venv/bin/pip install -r requirements.txt
```

### 4.2. Відновлення бази даних

```bash
sudo systemctl stop smartbudget
sudo -u smartbudget cp \
    /opt/smartbudget/data/smartbudget.db.bak.<timestamp> \
    /opt/smartbudget/data/smartbudget.db
```

### 4.3. Відновлення конфігурації

```bash
sudo cp /opt/smartbudget/app/.env.bak.<timestamp> \
    /opt/smartbudget/app/.env
```

### 4.4. Запуск після відкату

```bash
sudo systemctl start smartbudget
curl -I http://localhost:5000
```
