---
description: 查询当前 Codex 余额/用量入口，并用中文说明
---

Run `codex-balance --json`.

Read the JSON and answer in concise Chinese:

- If `auth_mode` is `chatgpt`, explain that ChatGPT-based Codex does not expose a direct numeric remaining balance in the CLI or public API, and point the user to the official Usage Dashboard using the URLs returned by the command.
- If `auth_mode` is `api_key`, explain that usage and credits should be checked in the OpenAI platform dashboard using the URLs returned by the command.
- If `auth_mode` is `logged_out` or `unknown`, say that the login/billing mode could not be determined reliably and show the returned URLs.

Rules:

- Do not edit files.
- Do not browse the web unless the user explicitly asks for verification.
- Keep the answer short.
- Include the primary URL explicitly in the reply.
