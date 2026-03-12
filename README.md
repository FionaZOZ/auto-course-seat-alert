# UCI Course Seat Alert

Automatically monitors UCI WebSoc for open seats in **ICS 51 (course code 35790)** and sends a Gmail notification when a seat opens up. Runs every 5 minutes via GitHub Actions.

## Setup

### 1. Generate a Gmail App Password

- Go to https://myaccount.google.com/apppasswords (需要先开启两步验证)
- Create a new app password, copy the 16-character code

### 2. Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**, add:

| Secret Name         | Value                        |
| ------------------- | ---------------------------- |
| `GMAIL_USER`        | your Gmail address           |
| `GMAIL_APP_PASSWORD`| the 16-char app password     |
| `NOTIFY_EMAIL`      | email to receive alerts      |

### 3. Push & Enable

```bash
git push origin main
```

Push 之后 GitHub Actions 会自动每 5 分钟检查一次。也可以在 Actions 页面手动触发测试。

### 4. Update Quarter

Edit `check_seat.py` line with `YearTerm` to match the current quarter:
- `2025-92` = 2025 Fall
- `2025-14` = 2025 Spring
- `2025-03` = 2025 Winter
