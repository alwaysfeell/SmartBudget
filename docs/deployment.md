# Розгортання SmartBudget у production-середовищі

> Документ призначений для release engineer / DevOps.

---

## 1. Вимоги до апаратного забезпечення

| Параметр | Мінімум | Рекомендовано |
|---|---|---|
| Архітектура | x86_64 | x86_64 / ARM64 |
| CPU | 1 vCPU | 2 vCPU |
| RAM | 512 MB | 1 GB |
| Диск | 2 GB | 10 GB |
| ОС | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

---

## 2. Необхідне програмне забезпечення

```bash
sudo apt update && sudo apt install -y \
    python3.10 python3.10-venv python3-pip \
    git nginx
```

---

## 3. Налаштування мережі

| Порт | Протокол | Призначення |
|---|---|---|
| 80 | HTTP | Nginx (зовнішній) |
| 443 | HTTPS | Nginx TLS (якщо є сертифікат) |
| 5000 | HTTP | Gunicorn (лише localhost) |

Відкрийте порти 80/443 у firewall:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 4. Розгортання коду

### 4.1. Створення системного користувача

```bash
sudo useradd --system --home /opt/smartbudget --shell /bin/bash smartbudget
sudo mkdir -p /opt/smartbudget
sudo chown smartbudget:smartbudget /opt/smartbudget
```

### 4.2. Клонування репозиторію

```bash
sudo -u smartbudget git clone https://github.com/alwaysfeell/SmartBudget.git /opt/smartbudget/app
cd /opt/smartbudget/app
```

### 4.3. Віртуальне середовище та залежності

```bash
sudo -u smartbudget python3 -m venv /opt/smartbudget/venv
sudo -u smartbudget /opt/smartbudget/venv/bin/pip install -r requirements.txt
sudo -u smartbudget /opt/smartbudget/venv/bin/pip install gunicorn
```

### 4.4. Конфігурація середовища

```bash
sudo -u smartbudget tee /opt/smartbudget/app/.env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE=/opt/smartbudget/data/smartbudget.db
DEBUG=false
EOF
sudo mkdir -p /opt/smartbudget/data
sudo chown smartbudget:smartbudget /opt/smartbudget/data
```

---

## 5. Налаштування Gunicorn (systemd)

Створіть файл `/etc/systemd/system/smartbudget.service`:

```ini
[Unit]
Description=SmartBudget Flask Application
After=network.target

[Service]
User=smartbudget
WorkingDirectory=/opt/smartbudget/app
EnvironmentFile=/opt/smartbudget/app/.env
ExecStart=/opt/smartbudget/venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:5000 \
    --access-logfile /var/log/smartbudget/access.log \
    --error-logfile /var/log/smartbudget/error.log \
    app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/smartbudget
sudo chown smartbudget:smartbudget /var/log/smartbudget
sudo systemctl daemon-reload
sudo systemctl enable smartbudget
sudo systemctl start smartbudget
```

---

## 6. Налаштування Nginx

Створіть `/etc/nginx/sites-available/smartbudget`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /opt/smartbudget/app/static;
        expires 7d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/smartbudget /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Перевірка працездатності

```bash
# Статус процесу
sudo systemctl status smartbudget

# HTTP-відповідь
curl -I http://localhost:5000

# Логи
sudo journalctl -u smartbudget -f
tail -f /var/log/smartbudget/error.log
```

Якщо `curl` повертає `HTTP/1.1 200 OK` — розгортання успішне.

---

## 8. База даних SQLite

SmartBudget використовує SQLite — окремого сервера БД не потрібно. База створюється автоматично при першому запиті. Файл зберігається за шляхом, вказаним у змінній `DATABASE`.

```bash
# Ручна ініціалізація БД
sudo -u smartbudget /opt/smartbudget/venv/bin/python -c \
    "from database import init_db; init_db()"
```