"""Test Gemini connectivity without printing the API key."""

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify GEMINI_API_KEY and model against the Gemini API (no secrets printed)."

    def handle(self, *args, **options):
        api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
        model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

        if not api_key:
            self.stderr.write(self.style.ERROR("GEMINI_API_KEY is empty. Check storyteller_django/.env"))
            return

        if api_key.startswith("AQ."):
            key_kind = "AQ (new format)"
        elif api_key.startswith("AIza"):
            key_kind = "AIza (legacy)"
        else:
            key_kind = "unknown prefix"

        self.stdout.write(f"Key: {key_kind}, length={len(api_key)}")
        self.stdout.write(f"Model: {model}")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": "Reply with exactly: OK"}]}],
            "generationConfig": {"maxOutputTokens": 16},
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            self.stdout.write(self.style.SUCCESS(f"HTTP {response.status}: {text.strip()[:80]}"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            self.stderr.write(self.style.ERROR(f"HTTP {exc.code}"))
            try:
                err = json.loads(body).get("error", {})
                self.stderr.write(f"status: {err.get('status', '?')}")
                self.stderr.write(f"message: {err.get('message', body[:400])}")
            except json.JSONDecodeError:
                self.stderr.write(body[:400])
