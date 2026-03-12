import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.parse import urlencode


NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

WEBSOC_URL = "https://www.reg.uci.edu/perl/WebSoc"
YEAR_TERM = "2025-92"  # 2025 Fall — update each quarter

# ── Monitor list ──────────────────────────────────────────────
# Each entry: (course_codes_for_query, label, list of codes to watch)
WATCH_LIST = [
    {
        "label": "ICS 51",
        "query_codes": "35790",
        "watch": ["35790"],
    },
    {
        "label": "PHILOS 1 Discussions",
        "query_codes": "30301-30308",
        "watch": ["30301", "30302", "30303", "30304",
                  "30305", "30306", "30307", "30308"],
    },
]


def fetch_websoc(course_codes: str) -> str:
    """Query WebSoc and return raw HTML."""
    params = urlencode({
        "YearTerm": YEAR_TERM,
        "CourseCodes": course_codes,
        "Submit": "Display Web Results",
    })
    req = Request(
        f"{WEBSOC_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0 (SeatAlert)"},
    )
    return urlopen(req, timeout=30).read().decode("utf-8", errors="replace")


def parse_courses(html: str, codes: list[str]) -> list[dict]:
    """Parse WebSoc HTML and extract info for the given course codes."""
    results = []
    for code in codes:
        # Match the row containing this course code through to the Status cell
        row_pattern = re.compile(
            rf'>{code}\s*</td>'
            r'(.*?)'
            r'<td[^>]*>\s*(\w+)\s*</td>\s*</tr>',
            re.DOTALL,
        )
        match = row_pattern.search(html)
        if not match:
            print(f"  [WARN] Could not find code {code}")
            continue

        row_html = match.group(0)
        status = match.group(2).strip()

        # Extract all numbers in <td> cells — typically: Max, Enr, WL, etc.
        nums = re.findall(r'<td[^>]*>\s*(\d+)\s*</td>', row_html)
        # Find section type & time from the row
        sec_match = re.search(r'(Lec|Dis|Lab)\b', row_html)
        sec_type = sec_match.group(1) if sec_match else "?"
        time_match = re.search(r'(\w[\w:]+\s*-\s*[\w:]+\s*[APM]*)', row_html)
        time_str = time_match.group(1).strip() if time_match else "?"

        results.append({
            "code": code,
            "type": sec_type,
            "time": time_str,
            "max": nums[0] if len(nums) > 0 else "?",
            "enrolled": nums[1] if len(nums) > 1 else "?",
            "waitlist": nums[2] if len(nums) > 2 else "?",
            "status": status,
        })
    return results


def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = NOTIFY_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
    print("  ✉ Email sent!")


def main():
    open_courses: list[dict] = []

    for group in WATCH_LIST:
        label = group["label"]
        print(f"\n── {label} ──")
        html = fetch_websoc(group["query_codes"])
        courses = parse_courses(html, group["watch"])

        for c in courses:
            flag = " ← OPEN!" if c["status"].upper() == "OPEN" else ""
            print(f"  {c['code']} ({c['type']}) {c['time']}  "
                  f"{c['enrolled']}/{c['max']}  WL:{c['waitlist']}  "
                  f"[{c['status']}]{flag}")
            if c["status"].upper() == "OPEN":
                c["label"] = label
                open_courses.append(c)

    if not open_courses:
        print("\nNo open seats found. Will check again next run.")
        return

    # ── Build email ──
    lines = ["有空位了！快去选课！\n"]
    for c in open_courses:
        lines.append(
            f"• {c['label']} — Code {c['code']} ({c['type']}) {c['time']}\n"
            f"  Enrolled: {c['enrolled']}/{c['max']}  WL: {c['waitlist']}  "
            f"Status: {c['status']}"
        )
    lines.append(f"\nWebReg: https://www.reg.uci.edu/registrar/soc/webreg.html")
    body = "\n".join(lines)

    n = len(open_courses)
    send_email(f"🎉 {n} course seat(s) open — go enroll now!", body)


if __name__ == "__main__":
    if "--test-email" in sys.argv:
        send_email(
            "✅ Seat Alert 测试邮件",
            "如果你收到这封邮件，说明邮件通知配置成功！\n\n"
            "系统会每 5 分钟检查一次以下课程：\n"
            + "\n".join(f"• {g['label']} ({g['query_codes']})" for g in WATCH_LIST)
            + "\n\n有空位时会自动发邮件通知你。",
        )
    else:
        main()
