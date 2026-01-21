import os
import re
from typing import Iterable

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


LINK_PATTERN = re.compile(r"(https?://[^\s)]+)")


def text_to_html(content: str) -> str:
    lines = content.splitlines()
    html_lines = []
    in_list = False
    for line in lines:
        line = LINK_PATTERN.sub(r'<a href="\1">\1</a>', line)
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.strip():
                html_lines.append(f"<strong>{line}</strong>")
            else:
                html_lines.append("<br>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def send_email(subject: str, content: str, recipients: Iterable[str]) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    if not api_key or not from_email:
        raise RuntimeError("SENDGRID_API_KEY and FROM_EMAIL are required to send")

    recipients = list(recipients)
    message = Mail(
        from_email=from_email,
        to_emails=recipients,
        subject=subject,
        plain_text_content=content,
        html_content=text_to_html(content),
    )
    sg = SendGridAPIClient(api_key)
    print(f"SendGrid: sending to {', '.join(recipients)} with subject '{subject}'")
    response = sg.send(message)
    print(f"SendGrid status: {response.status_code}")
