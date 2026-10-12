# Send Email Notification Component
> Description: Reusable shared subflow component for sending email notifications via Gmail / SMTP
> Version: 1.0.0

## Variables
- `to`: arttopix@example.com
- `subject`: Automated Notification from Kinenix
- `body`: Hello, this is an automated message from Kinenix.
- `html`: null
- `attachments`: []
- `dry_run`: false

## Steps

### step_send_email. Send Email Message (`email.send`)
- **output_var:** `send_result`
- **to:** ${to}
- **subject:** ${subject}
- **body:** ${body}
- **html:** ${html}
- **attachments:** ${attachments}
- **dry_run:** ${dry_run}

### step_return_status. Return Email Result (`flow.return`)
- **value:** {"status": "${send_result.status}", "channel": "${send_result.channel}", "to": "${to}", "subject": "${subject}", "timestamp": "${send_result.timestamp}"}
