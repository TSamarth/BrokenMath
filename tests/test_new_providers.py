"""Self-check: groq/opencode collapse to the OpenAI-compatible client with the
right base_url + env key, and DO NOT drop inference params in the collapse."""
import os

from sycophancy.api import APIQuery


def test_groq_resolves_and_keeps_params():
    os.environ["GROQ_API_KEY"] = "gk-test"
    q = APIQuery(model="openai/gpt-oss-120b", api="groq", max_tokens=16,
                 temperature=0.6, top_p=0.95, max_retries=0)
    assert q.api == "openai"
    assert q.base_url == "https://api.groq.com/openai/v1"
    assert q.api_key == "gk-test"
    # collapse must NOT render inference params useless
    assert q.kwargs["temperature"] == 0.6
    assert q.kwargs["top_p"] == 0.95
    assert q.kwargs["max_tokens"] == 16   # default max_tokens_param, not rewritten
    # secrets must not leak into the request payload
    assert "base_url" not in q.kwargs and "api_key" not in q.kwargs


def test_opencode_resolves_and_keeps_params():
    os.environ["OPENCODE_ZEN_API_KEY"] = "oc-test"
    q = APIQuery(model="grok-code-fast-1", api="opencode", max_tokens=16,
                 temperature=0.6, top_p=0.95, max_retries=0)
    assert q.api == "openai"
    assert q.base_url == "https://opencode.ai/zen/v1"
    assert q.api_key == "oc-test"
    assert q.kwargs["temperature"] == 0.6
    assert q.kwargs["top_p"] == 0.95
    assert q.kwargs["max_tokens"] == 16
    assert "base_url" not in q.kwargs and "api_key" not in q.kwargs


if __name__ == "__main__":
    test_groq_resolves_and_keeps_params()
    test_opencode_resolves_and_keeps_params()
    print("OK")
