import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


@register_action("email.send")
class EmailSendAction(BaseAction):
    """
    Sends an email message via SMTP (e.g. Gmail SMTP).
    Supports plain text, HTML formatted body, CC, BCC, attachments, and dry-run mode.
    """
    accepted_parameters = ('to', 'cc', 'bcc', 'subject', 'body', 'html', 'attachments', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'use_tls', 'dry_run')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        to_addr = parameters.get("to")
        subject = str(parameters.get("subject", "Kinenix Notification"))
        body = str(parameters.get("body", ""))
        html = parameters.get("html")
        cc_addr = parameters.get("cc")
        bcc_addr = parameters.get("bcc")
        attachments = parameters.get("attachments") or []

        # Convert recipients to lists
        recipients = self._to_list(to_addr)
        if not recipients:
            raise ValueError("Action 'email.send' requires at least one recipient in 'to' parameter.")

        cc_list = self._to_list(cc_addr)
        bcc_list = self._to_list(bcc_addr)
        all_recipients = recipients + cc_list + bcc_list

        # SMTP server: any provider (Gmail by default, Outlook / Microsoft 365, a company server)
        smtp_host = parameters.get("smtp_host") or os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(parameters.get("smtp_port") or os.getenv("SMTP_PORT", 587))
        smtp_user, smtp_password = self._credentials(parameters)
        use_tls = bool(parameters.get("use_tls", True))
        dry_run = bool(parameters.get("dry_run", False))
        channel = f"SMTP {smtp_host}:{smtp_port}"

        # Resolve attachments first, so a dry run also catches a missing file
        flow_dir = context.get_variable("__flow_dir__")
        base_dir = Path(flow_dir) if flow_dir else Path.cwd()
        attachment_paths: List[Path] = []
        for att_path_str in attachments if isinstance(attachments, list) else [attachments]:
            att_path = Path(att_path_str)
            if not att_path.is_absolute():
                att_path = (base_dir / att_path_str).resolve()
            if not att_path.is_file():
                raise FileNotFoundError(f"Email attachment file not found: {att_path_str}")
            attachment_paths.append(att_path)

        # Check Dry Run / Test mode
        if dry_run or not (smtp_user and smtp_password):
            if not dry_run and not (smtp_user and smtp_password):
                # If credentials are not set and dry_run not explicitly set to false, raise helpful guidance
                raise ValueError(
                    "SMTP credentials missing. Please supply 'smtp_user' and 'smtp_password' in parameters, "
                    "or set SMTP_USER and SMTP_PASSWORD (any provider) or GMAIL_USER and GMAIL_APP_PASSWORD. "
                    "(To test without sending real email, pass 'dry_run': true)."
                )

            return {
                "status": "simulated",
                "channel": channel,
                "to": recipients,
                "cc": cc_list,
                "subject": subject,
                "attachments_count": len(attachment_paths),
                "timestamp": datetime.now().isoformat(),
                "note": "Dry run execution: email verified and formatted without external SMTP dispatch."
            }

        # Build MIME Message: text and HTML are alternatives of one body; attachments sit beside that body
        if body and html:
            content = MIMEMultipart("alternative")
            content.attach(MIMEText(body, "plain", "utf-8"))
            content.attach(MIMEText(str(html), "html", "utf-8"))
        else:
            content = MIMEText(str(html), "html", "utf-8") if html else MIMEText(body, "plain", "utf-8")

        msg = MIMEMultipart("mixed")
        msg["From"] = smtp_user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        msg.attach(content)

        for att_path in attachment_paths:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att_path.read_bytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{att_path.name}"'
            )
            msg.attach(part)

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, all_recipients, msg.as_string())

        return {
            "status": "sent",
            "channel": channel,
            "to": recipients,
            "cc": cc_list,
            "subject": subject,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def _credentials(parameters: Dict[str, Any]) -> Tuple[str, str]:
        """User and password from parameters, else an environment pair: SMTP_* first, then GMAIL_*.

        Pairs are not mixed, so a Gmail user is never sent with another provider's password.
        """
        if parameters.get("smtp_user") or parameters.get("smtp_password"):
            return parameters.get("smtp_user") or "", parameters.get("smtp_password") or ""
        if os.getenv("SMTP_USER"):
            return os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")
        return os.getenv("GMAIL_USER", ""), os.getenv("GMAIL_APP_PASSWORD", "")

    def _to_list(self, val: Any) -> List[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(item).strip() for item in val if str(item).strip()]
        if isinstance(val, str):
            return [s.strip() for s in val.split(",") if s.strip()]
        return [str(val).strip()]
