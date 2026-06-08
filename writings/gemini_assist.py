import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL_FALLBACKS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)


class WritingAssistError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _gemini_error_message(http_status: int, body: str, model: str) -> str:
    """Turn Gemini HTTP errors into actionable messages (never include API keys)."""
    try:
        payload = json.loads(body)
        detail = payload.get("error", {})
        message = (detail.get("message") or "").strip()
        status = (detail.get("status") or "").strip()
    except (json.JSONDecodeError, AttributeError, TypeError):
        message = ""
        status = ""

    if message:
        return f"Gemini ({http_status}): {message[:400]}"

    lowered = message.lower()
    if http_status in (401, 403) or "api key" in lowered or "api_key" in lowered:
        return (
            "Cheia API Gemini nu este acceptată. Verifică GEMINI_API_KEY în .env "
            "(chei noi încep cu AQ., cele vechi cu AIzaSy) și repornește Django."
        )
    if "not found" in lowered or status == "NOT_FOUND":
        return (
            f"Modelul «{model}» nu este disponibil. Setează în .env "
            f"GEMINI_MODEL=gemini-2.5-flash și repornește Django."
        )
    if "deprecated" in lowered or "shut down" in lowered:
        return (
            "Modelul Gemini folosit a fost retras. Folosește GEMINI_MODEL=gemini-2.5-flash în .env."
        )
    return "AI service rejected the request. Check your API key and model name."


def _models_to_try(preferred: str) -> list[str]:
    ordered: list[str] = []
    for name in (preferred, *GEMINI_MODEL_FALLBACKS):
        if name and name not in ordered:
            ordered.append(name)
    return ordered


def _call_gemini(*, api_key: str, model: str, prompt: str, mode: str) -> dict:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85 if mode == "game" else 0.7,
            "maxOutputTokens": 512,
        },
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

    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def _build_new_story_context(
    *,
    title: str = "",
    categories: list | None = None,
) -> str:
    parts = [f"Title: {title.strip() or 'Not set yet'}"]
    category_names = [str(name).strip() for name in (categories or []) if str(name).strip()]
    if category_names:
        parts.append(f"Categories: {', '.join(category_names)}")
    parts.append("Status: brand-new story — no prior segments yet.")
    return "\n".join(parts)


def _build_context(story, writings, max_writings: int = 5) -> str:
    parts = [f"Title: {story.title or 'Untitled'}"]
    category_names = list(story.categories.values_list("name", flat=True))
    if category_names:
        parts.append(f"Categories: {', '.join(category_names)}")
    recent = list(writings.order_by("created", "id"))[-max_writings:]
    if recent:
        parts.append("Recent story segments:")
        for index, writing in enumerate(recent, start=1):
            text = (writing.text or "").strip()
            if len(text) > 1200:
                text = text[:1200] + "…"
            author = getattr(writing.author, "author_name", None) or "Unknown"
            parts.append(f"{index}. ({author}): {text}")
    return "\n".join(parts)


def _build_prompt(
    *,
    mode: str,
    lang: str,
    context: str,
    draft_text: str,
    is_new_story: bool = False,
) -> str:
    language = "Romanian" if lang == "ro" else "English"
    draft_section = ""
    if draft_text.strip():
        draft_section = f"\nWriter's current draft:\n{draft_text.strip()[:1500]}\n"

    if is_new_story:
        if mode == "game":
            task = (
                "Propose ONE short creativity exercise (30–60 seconds) to help write the opening. "
                "Use one of: fill-in-the-blank sentence, 3 random words to include, or a 'what if' question. "
                "Do not write the full opening chapter."
            )
        else:
            task = (
                "Suggest TWO brief directions (1–2 sentences each) for how to begin this story. "
                "Do not write the full opening chapter."
            )
    elif mode == "game":
        task = (
            "Propose ONE short creativity exercise (30–60 seconds) to help continue the story. "
            "Use one of: fill-in-the-blank sentence, 3 random words to include, or a 'what if' question. "
            "Do not write the next chapter."
        )
    else:
        task = (
            "Suggest TWO brief directions (1–2 sentences each) for how the story could continue. "
            "Do not write the full next chapter."
        )

    return (
        f"You are a creative writing coach for a collaborative fiction app. "
        f"Reply only in {language}. Be concise and encouraging.\n\n"
        f"Story context:\n{context}\n"
        f"{draft_section}\n"
        f"{task}\n\n"
        f"Format: a short title line, then the content. No markdown headers."
    )


def _parse_assist_response(*, data: dict, mode: str, lang: str) -> dict:
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise WritingAssistError(
            "AI returned an unexpected response.",
            status_code=502,
        ) from exc

    text = (text or "").strip()
    if not text:
        raise WritingAssistError("AI returned an empty response.", status_code=502)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    title = lines[0][:120] if lines else ("Joc creativ" if mode == "game" and lang == "ro" else "Creative game")
    content = "\n".join(lines[1:]) if len(lines) > 1 else text

    return {
        "mode": mode,
        "title": title,
        "content": content,
    }


def _invoke_gemini_assist(*, mode: str, lang: str, prompt: str) -> dict:
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        raise WritingAssistError("AI assist is not configured.", status_code=503)

    if not (api_key.startswith("AIza") or api_key.startswith("AQ.")):
        raise WritingAssistError(
            "GEMINI_API_KEY nu pare o cheie Google AI Studio. "
            "Creează una la https://aistudio.google.com/app/apikey.",
            status_code=503,
        )

    data = None
    last_error: WritingAssistError | None = None

    for candidate_model in _models_to_try(model):
        try:
            data = _call_gemini(
                api_key=api_key,
                model=candidate_model,
                prompt=prompt,
                mode=mode,
            )
            if candidate_model != model:
                logger.info("Gemini assist used fallback model %s", candidate_model)
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if settings.DEBUG:
                logger.warning(
                    "Gemini HTTP %s model=%s body=%s",
                    exc.code,
                    candidate_model,
                    body[:500],
                )
            err = WritingAssistError(
                _gemini_error_message(exc.code, body, candidate_model),
                status_code=502,
            )
            last_error = err
            if exc.code == 404:
                continue
            raise err from exc
        except urllib.error.URLError as exc:
            raise WritingAssistError(
                "Could not reach the AI service. Try again later.",
                status_code=503,
            ) from exc

    if data is None:
        raise last_error or WritingAssistError(
            "AI service rejected the request.",
            status_code=502,
        )

    return _parse_assist_response(data=data, mode=mode, lang=lang)


def generate_writing_assist(
    *,
    mode: str,
    lang: str,
    story,
    writings,
    draft_text: str = "",
) -> dict:
    context = _build_context(story, writings)
    prompt = _build_prompt(
        mode=mode,
        lang=lang,
        context=context,
        draft_text=draft_text,
        is_new_story=False,
    )
    return _invoke_gemini_assist(mode=mode, lang=lang, prompt=prompt)


def generate_new_story_assist(
    *,
    mode: str,
    lang: str,
    title: str = "",
    categories: list | None = None,
    draft_text: str = "",
) -> dict:
    context = _build_new_story_context(title=title, categories=categories)
    prompt = _build_prompt(
        mode=mode,
        lang=lang,
        context=context,
        draft_text=draft_text,
        is_new_story=True,
    )
    return _invoke_gemini_assist(mode=mode, lang=lang, prompt=prompt)
