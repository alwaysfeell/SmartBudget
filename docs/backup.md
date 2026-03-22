# Резервне копіювання SmartBudget

> Документ призначений для release engineer / DevOps.

---

## 1. Що потрібно резервувати

| Компонент | Шлях | Важливість |
|---|---|---|
| База даних SQLite | `/opt/smartbudget/data/smartbudget.db` | Критично |
| Конфігурація `.env` | `/opt/smartbudget/app/.env` | Критично |
| Nginx конфіг | `/etc/nginx/sites-available/smartbudget` | Важливо |
| systemd unit | `/etc/systemd/system/smartbudget.service` | Важливо |

Код (репозиторій GitHub) резервного копіювання **не потребує** — він зберігається у Git.

---

## 2. Ручне резервне копіювання

```bash
BACKUP_DIR="/opt/smartbudget/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# База даних
cp /opt/smartbudget/data/smartbudget.db \
    "$BACKUP_DIR/smartbudget_$TIMESTAMP.db"

# Конфігурація
cp /opt/smartbudget/app/.env \
    "$BACKUP_DIR/env_$TIMESTAMP.bak"

echo "Backup created: $BACKUP_DIR"
```

---

## 3. Автоматизований скрипт (scripts/backup.sh)

Файл `scripts/backup.sh` вже є у репозиторії. Встановіть у cron для щоденного виконання:

```bash
sudo crontab -e
# Щодня о 03:00:
0 3 * * * /bin/bash /opt/smartbudget/app/scripts/backup.sh >> /var/log/smartbudget/backup.log 2>&1
```

---

## 4. Відновлення з резервної копії

```bash
sudo systemctl stop smartbudget

# Відновити БД
cp /opt/smartbudget/backups/smartbudget_<timestamp>.db \
   /opt/smartbudget/data/smartbudget.db

sudo systemctl start smartbudget
curl -I http://localhost:5000
```

---

## 5. Ротація старих копій

```bash
# Видалити резервні копії старші за 30 днів
find /opt/smartbudget/backups -name "*.db" -mtime +30 -delete
find /opt/smartbudget/backups -name "*.bak" -mtime +30 -delete
```
