import re
import time

from google import genai
from google.genai import types


def _is_rate_limit(e):
    s = str(e)
    return any(k in s for k in ("429", "RESOURCE_EXHAUSTED", "quota", "rate limit"))


def _is_overloaded(e):
    s = str(e)
    return any(k in s for k in ("503", "UNAVAILABLE", "high demand", "temporary"))


def _is_model_unavailable(e):
    s = str(e).lower()
    return any(
        k in s
        for k in (
            "404",
            "not_found",
            "not found",
            "no longer available",
            "permission_denied",
            "model does not exist",
        )
    )


def _extract_retry_delay(e):
    m = re.search(r"retry\s*(?:in|after)\s*(\d+(?:\.\d+)?)s?", str(e), re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 0.0


def wait_before_retry(e, attempt, base=2.0):
    delay = _extract_retry_delay(e)
    if not delay:
        delay = base * (2 ** attempt)
    delay = min(delay, 30)
    print(f"  (model busy, retrying in {delay:.0f}s...)")
    time.sleep(delay)


class AIClient:
    def __init__(self, api_key, cfg=None):
        self.cfg = cfg or {}
        self.client = genai.Client(api_key=api_key)
        self._working = {}

    def _candidates(self, requested):
        seen = set()
        yield requested
        seen.add(requested)
        for m in self.cfg.get("model_fallbacks", []):
            if m not in seen:
                seen.add(m)
                yield m

    def _candidate_list(self, requested):
        base = list(self._candidates(requested))
        cached = self._working.get("_default")
        if cached and cached in base:
            return [cached] + [m for m in base if m != cached]
        return base

    def build_config(self, system_instruction):
        kwargs = {
            "response_mime_type": "text/plain",
            "system_instruction": [types.Part.from_text(text=system_instruction)],
        }
        thinking = self.cfg.get("thinking")
        if thinking:
            try:
                kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)
            except Exception:
                pass
        return types.GenerateContentConfig(**kwargs)

    def _contents(self, question, history=None):
        contents = []
        if history:
            for msg in history:
                contents.append(
                    types.Content(
                        role=msg.get("role", "user"),
                        parts=[types.Part.from_text(text=msg.get("text", ""))],
                    )
                )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=question)],
            )
        )
        return contents

    def _run_stream(self, candidates, question, history, system_instruction, max_retries):
        cycles = max(2, max_retries)
        attempt = 0
        while True:
            tried_any = False
            for i, effective in enumerate(candidates):
                try:
                    for chunk in self.client.models.generate_content_stream(
                        model=effective,
                        contents=self._contents(question, history),
                        config=self.build_config(system_instruction),
                    ):
                        yield chunk.text
                    self._mark_working_for(effective)
                    return
                except Exception as e:
                    tried_any = True
                    if _is_model_unavailable(e):
                        self._working.pop(effective, None)
                        print(f"  (model {effective} unavailable, trying next...)")
                        continue
                    if _is_overloaded(e) or _is_rate_limit(e):
                        if i < len(candidates) - 1:
                            print(f"  (model {effective} busy, trying next...)")
                            continue
                        # Last candidate was busy: wait, then loop the cycle again.
                        if attempt < cycles:
                            wait_before_retry(e, attempt)
                            attempt += 1
                            break
                        raise
                    raise
            if not tried_any:
                return
            if attempt >= cycles:
                raise RuntimeError("All models are busy. Try again in a moment.")

    def _run_quick(self, candidates, question, history, system_instruction, max_retries):
        cycles = max(2, max_retries)
        attempt = 0
        while True:
            tried_any = False
            for i, effective in enumerate(candidates):
                try:
                    response = self.client.models.generate_content(
                        model=effective,
                        contents=self._contents(question, history),
                        config=self.build_config(system_instruction),
                    )
                    self._mark_working_for(effective)
                    return response.text
                except Exception as e:
                    tried_any = True
                    if _is_model_unavailable(e):
                        self._working.pop(effective, None)
                        print(f"  (model {effective} unavailable, trying next...)")
                        continue
                    if _is_overloaded(e) or _is_rate_limit(e):
                        if i < len(candidates) - 1:
                            print(f"  (model {effective} busy, trying next...)")
                            continue
                        if attempt < cycles:
                            wait_before_retry(e, attempt)
                            attempt += 1
                            break
                        raise
                    raise
            if not tried_any:
                return None
            if attempt >= cycles:
                raise RuntimeError("All models are busy. Try again in a moment.")

    def _mark_working_for(self, model):
        for key in list(self._working):
            if self._working[key] == model:
                return
        # remember model globally
        self._working["_default"] = model

    def stream(self, model, question, system_instruction, max_retries=3, history=None):
        candidates = self._candidate_list(model)
        yield from self._run_stream(
            candidates, question, history, system_instruction, max_retries
        )

    def quick(self, model, question, system_instruction, max_retries=3, history=None):
        candidates = self._candidate_list(model)
        return self._run_quick(
            candidates, question, history, system_instruction, max_retries
        )
