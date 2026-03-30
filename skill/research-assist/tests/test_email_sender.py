from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from codex_research_assist.email_sender import send_email


class EmailSenderPathTest(unittest.TestCase):
    def test_send_email_preserves_visible_attachment_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            attachment = root / "digest.html"
            attachment.write_text("<html></html>", encoding="utf-8")

            smtp_client = MagicMock()
            smtp_cm = MagicMock()
            smtp_cm.__enter__.return_value = smtp_client
            smtp_cm.__exit__.return_value = False

            with patch("codex_research_assist.email_sender.smtplib.SMTP_SSL", return_value=smtp_cm):
                result = send_email(
                    subject="Digest",
                    body_text="text",
                    body_html="<p>html</p>",
                    sender="bot@example.com",
                    recipients=["user@example.com"],
                    smtp_server="smtp.example.com",
                    smtp_port=465,
                    smtp_user="bot@example.com",
                    smtp_pass="secret",
                    attachments=[attachment],
                )

        self.assertEqual(result["attachments"], [attachment.as_posix()])
        smtp_client.login.assert_called_once_with("bot@example.com", "secret")
        smtp_client.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
