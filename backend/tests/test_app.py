import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi import HTTPException

import main


class ClipNotesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env_patch = patch.dict(os.environ, {
            "APP_PASSWORD": "unit-test-password",
            "SESSION_SECRET": "unit-test-session-secret-which-is-long-enough",
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "",
            "LARK_APP_ID": "",
            "LARK_APP_SECRET": "",
            "LARK_RECEIVE_ID": "",
        })
        cls.env_patch.start()
        cls.client = TestClient(main.app)
        response = cls.client.post("/api/login", json={"password": "unit-test-password"})
        if response.status_code != 200:
            raise RuntimeError(f"Test login failed: {response.text}")
        cls.auth = {"Authorization": f"Bearer {response.json()['access_token']}"}

    @classmethod
    def tearDownClass(cls):
        cls.env_patch.stop()

    def test_direct_caption_retrieval_parses_readable_track(self):
        import json

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.status_code = 200
            def raise_for_status(self):
                return None

        player = {"captions": {"playerCaptionsTracklistRenderer": {"captionTracks": [{"languageCode": "en", "baseUrl": "https://www.youtube.com/api/timedtext?x=1"}]}}}
        page = "ytInitialPlayerResponse = " + json.dumps(player) + ";"
        captions = "<transcript><text start=\"1.5\">Hello &amp; welcome.</text></transcript>"
        with patch.object(main.httpx, "get", side_effect=[FakeResponse(page), FakeResponse(captions)]):
            result = main.fetch_direct_transcript("https://youtu.be/abcdefghijk")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["transcript"], "[00:00:01] Hello & welcome.")

    def test_vtt_parser_handles_youtube_blank_cues_and_tags(self):
        from pathlib import Path
        import tempfile
        vtt = chr(10).join(["WEBVTT", "", "00:00:01.000 --> 00:00:02.000", "", "Hello <c>world</c>.", "", "00:00:02.000 --> 00:00:03.000", "", "Hello world.", ""])
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "captions.en.vtt"
            path.write_text(vtt, encoding="utf-8")
            cues = main.parse_vtt(path)
        self.assertEqual(cues, [("00:00:01", "Hello world.")])

    def test_health_is_public_and_does_not_expose_secrets(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["login_configured"])
        self.assertNotIn("APP_PASSWORD", response.text)

    def test_rejects_non_youtube_url(self):
        response = self.client.post("/api/summarize", headers=self.auth, json={"youtube_url": "https://example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid YouTube", response.json()["detail"])

    def test_requires_login(self):
        response = self.client.post("/api/summarize", json={"youtube_url": "https://youtu.be/abcdefghijk"})
        self.assertEqual(response.status_code, 401)

    def test_reports_no_transcript_and_does_not_call_summarizer(self):
        with patch.object(main, "fetch_transcript", side_effect=HTTPException(status_code=404, detail="No readable captions were retrieved.")), \
             patch.object(main, "generate_summary") as summarize:
            response = self.client.post("/api/summarize", headers=self.auth, json={"youtube_url": "https://youtu.be/abcdefghijk"})
        self.assertEqual(response.status_code, 404)
        summarize.assert_not_called()

    def test_returns_summary_only_after_transcript_is_readable(self):
        fake_transcript = "[00:00:01] The speaker explains the first step.\n[00:00:05] The speaker gives the result."
        with patch.object(main, "fetch_transcript", return_value={"transcript": fake_transcript, "language": "en", "caption_file": "captions.en.vtt"}), \
             patch.object(main, "generate_summary", return_value="## Short summary\nA transcript-grounded summary.") as summarize:
            response = self.client.post("/api/summarize", headers=self.auth, json={"youtube_url": "https://youtu.be/abcdefghijk"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript_status"], "Available")
        self.assertEqual(response.json()["transcript_text"], fake_transcript)
        summarize.assert_called_once_with(fake_transcript, "English")

    def test_lark_requires_explicit_approval(self):
        response = self.client.post("/api/send-to-lark", headers=self.auth, json={"approval_confirmed": False, "summary_markdown": "A summary"})
        self.assertEqual(response.status_code, 400)

    def test_lark_stays_disabled_without_credentials(self):
        response = self.client.post("/api/send-to-lark", headers=self.auth, json={"approval_confirmed": True, "summary_markdown": "A summary"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
