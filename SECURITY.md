# Security policy

This project handles WhatsApp numbers and describes the circumstances of a death.
Please treat any weakness in it seriously.

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Use GitHub's private
vulnerability reporting on this repository (the **Security** tab, then **Report a
vulnerability**), or contact the maintainers privately.

Include what you found, how to reproduce it and what an attacker could do with it.
You can expect an acknowledgement within a few days.

## Things that matter most here

- **Forged webhooks.** `/meta` verifies `X-Hub-Signature-256` and `/whatsapp`
  verifies the Twilio signature. Without `WHATSAPP_APP_SECRET` set, anyone who finds
  the URL can spend the token budget. A bypass of either check is a vulnerability.
- **Leaked credentials.** `.env` must never be committed. If a Groq key, a WhatsApp
  access token, an app secret or a verify token is ever exposed, revoke it at the
  provider first.
- **Personal data.** `cases.db` stores WhatsApp numbers, and `refusals.jsonl` can
  contain real questions. Both are gitignored and must stay off the repository, off
  screenshots and off issue reports. The tracker stores provenance and never message
  text.
- **Output that bypasses the validator.** Any route by which model text reaches a
  user without passing through `query.validate_answer`, or by which a contact
  number, figure or citation not grounded in the retrieved law reaches a user, is a
  safety defect and should be reported in the same way.

## Supported versions

Only the current `main` branch is supported. The project is a prototype and has not
been deployed to real families.
