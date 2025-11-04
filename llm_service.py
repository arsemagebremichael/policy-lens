import os
import json
import time
from typing import Dict, Any, Optional
from litellm import completion
from pydantic import ValidationError
from models import PolicyBriefResponse

os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

_CACHE = {}
_CACHE_TTL = 600 

def _get_cache_key(document: str, audience: str, language: str) -> str:
    return f"{hash(document)}:{audience}:{language}"

def _get_cached(key: str) -> Optional[Dict]:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["timestamp"] < _CACHE_TTL):
        return entry["data"]
    _CACHE.pop(key, None)
    return None

def _set_cache(key: str, data: Dict):
    _CACHE[key] = {"timestamp": time.time(), "data": data}

def generate_policy_brief(document: str, audience: str, language: str) -> Dict[str, Any]:
    cache_key = _get_cache_key(document, audience, language)
    cached = _get_cached(cache_key)
    if cached:
        return cached

    lang_names = {"en": "English", "sw": "Swahili", "am": "Amharic"}
    lang_name = lang_names.get(language, "English")

    prompt = f"""You are PolicyLens, an expert public policy analyst.
Audience: {audience}
Language: {lang_name}

Document:
{document}

Respond in valid JSON with:
- "summary": one-sentence overview
- "key_obligations": list of 2-4 items
- "effective_date": "YYYY-MM-DD" or "unknown"
- "confidence": "high", "medium", or "low"

Only output JSON. No extra text.
"""

    try:
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
            fallbacks=["openai/gpt-4o-mini"] if os.getenv("OPENAI_API_KEY") else []
        )

        raw_text = response["choices"][0]["message"]["content"].strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:].split("```")[0]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:].split("```")[0]

        parsed = json.loads(raw_text)
        validated = PolicyBriefResponse(**parsed)
        result = validated.model_dump()
        _set_cache(cache_key, result)
        return result

    except (json.JSONDecodeError, ValidationError, KeyError):
        return {
            "summary": "Could not generate structured summary.",
            "key_obligations": ["Document may be too vague or complex."],
            "effective_date": "unknown",
            "confidence": "low"
        }
    except Exception:
        return {
            "summary": "LLM service unavailable.",
            "key_obligations": ["Try again later."],
            "effective_date": "unknown",
            "confidence": "low"
        }