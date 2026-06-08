from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from writings.gemini_assist import (
    WritingAssistError,
    _build_new_story_context,
    _build_prompt,
    _gemini_error_message,
    _models_to_try,
    _parse_assist_response,
    generate_new_story_assist,
)


class ModelFallbackTests(SimpleTestCase):
    def test_preferred_model_first_with_dedup(self):
        self.assertEqual(
            _models_to_try("gemini-2.5-flash"),
            ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        )

    def test_custom_model_is_prepended(self):
        result = _models_to_try("custom-model")
        self.assertEqual(result[0], "custom-model")
        self.assertIn("gemini-2.5-flash", result)


class ContextAndPromptTests(SimpleTestCase):
    def test_new_story_context_includes_title_and_categories(self):
        context = _build_new_story_context(title="Quest", categories=["A", "B", "  "])
        self.assertIn("Title: Quest", context)
        self.assertIn("Categories: A, B", context)
        self.assertIn("brand-new", context)

    def test_new_story_context_defaults_when_empty(self):
        context = _build_new_story_context()
        self.assertIn("Title: Not set yet", context)

    def test_prompt_uses_romanian_language_label(self):
        prompt = _build_prompt(
            mode="suggestion",
            lang="ro",
            context="Title: X",
            draft_text="",
            is_new_story=True,
        )
        self.assertIn("Romanian", prompt)
        self.assertIn("Title: X", prompt)

    def test_prompt_uses_english_for_en(self):
        prompt = _build_prompt(
            mode="game", lang="en", context="ctx", draft_text="draft text"
        )
        self.assertIn("English", prompt)
        self.assertIn("draft text", prompt)


class ErrorMessageTests(SimpleTestCase):
    def test_uses_message_from_payload(self):
        body = '{"error": {"message": "Quota exceeded", "status": "RESOURCE_EXHAUSTED"}}'
        message = _gemini_error_message(429, body, "gemini-2.5-flash")
        self.assertTrue(message.startswith("Gemini (429):"))
        self.assertIn("Quota exceeded", message)

    def test_api_key_branch_when_no_message(self):
        message = _gemini_error_message(403, "{}", "gemini-2.5-flash")
        self.assertIn("GEMINI_API_KEY", message)

    def test_model_not_found_branch(self):
        body = '{"error": {"status": "NOT_FOUND"}}'
        message = _gemini_error_message(404, body, "gemini-x")
        self.assertIn("gemini-x", message)


class ParseResponseTests(SimpleTestCase):
    def test_parses_title_and_content(self):
        data = {
            "candidates": [
                {"content": {"parts": [{"text": "My Title\nLine one\nLine two"}]}}
            ]
        }
        result = _parse_assist_response(data=data, mode="suggestion", lang="en")
        self.assertEqual(result["mode"], "suggestion")
        self.assertEqual(result["title"], "My Title")
        self.assertIn("Line one", result["content"])

    def test_raises_on_unexpected_payload(self):
        with self.assertRaises(WritingAssistError):
            _parse_assist_response(data={"candidates": []}, mode="game", lang="ro")


class InvokeGuardTests(SimpleTestCase):
    @override_settings(GEMINI_API_KEY="")
    def test_missing_key_raises_not_configured(self):
        with self.assertRaises(WritingAssistError) as ctx:
            generate_new_story_assist(mode="suggestion", lang="ro", title="x")
        self.assertEqual(ctx.exception.status_code, 503)

    @override_settings(GEMINI_API_KEY="totally-invalid")
    def test_bad_key_prefix_raises(self):
        with self.assertRaises(WritingAssistError) as ctx:
            generate_new_story_assist(mode="suggestion", lang="ro", title="x")
        self.assertEqual(ctx.exception.status_code, 503)

    @override_settings(GEMINI_API_KEY="AQ.fake-key-for-tests")
    @patch("writings.gemini_assist._call_gemini")
    def test_successful_generation_with_mocked_api(self, mock_call):
        mock_call.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "Idea\nTry a flashback opening."}]}}
            ]
        }
        result = generate_new_story_assist(
            mode="suggestion", lang="ro", title="Quest", categories=["Adventure"]
        )
        self.assertEqual(result["title"], "Idea")
        self.assertIn("flashback", result["content"])
        mock_call.assert_called_once()
