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


def test_openrouter_default_path_keeps_params():
    # Default openrouter routing: no via_openai, so api stays "openrouter"
    # and uses the custom openrouter_query() path. Inference params must
    # reach the request body; secrets must not.
    os.environ["OPENROUTER_API_KEY"] = "or-test"
    q = APIQuery(model="google/gemma-4-26b-a4b-it:free", api="openrouter",
                 max_tokens=16, temperature=0.6, top_p=0.95, max_retries=0)
    assert q.api == "openrouter"          # NOT collapsed to openai
    assert q.base_url == "https://openrouter.ai/api/v1"
    assert q.api_key == "or-test"
    # openrouter_query() posts json={'model':..., 'messages':..., **q.kwargs}
    assert q.kwargs["temperature"] == 0.6
    assert q.kwargs["top_p"] == 0.95
    assert q.kwargs["max_tokens"] == 16   # injected via max_tokens_param
    # cost bookkeeping and secrets must not leak into the request payload
    assert "read_cost" not in q.kwargs and "write_cost" not in q.kwargs
    assert "base_url" not in q.kwargs and "api_key" not in q.kwargs


def test_openrouter_batch_allowed_through_gate():
    os.environ["OPENROUTER_API_KEY"] = "or-test"
    q = APIQuery(model="google/gemini-3.7-flash:batch", api="openrouter",
                 max_tokens=16, max_retries=0, batch_processing=True)
    assert q.api == "openrouter"
    assert q.batch_processing is True   # gate must NOT silently force this False


def test_parse_openrouter_batch_results():
    os.environ["OPENROUTER_API_KEY"] = "or-test"
    q = APIQuery(model="google/gemini-3.7-flash:batch", api="openrouter", max_retries=0)

    batch = {
        "id": "batch_1",
        "status": "completed",
        "results": [
            {
                "custom_id": "apiquery-0",
                "response": {
                    "status_code": 200,
                    "body": {
                        "choices": [{"message": {"content": "hi"}}],
                        "usage": {"prompt_tokens": 3, "completion_tokens": 1},
                    },
                },
                "error": None,
            },
            {
                "custom_id": "apiquery-1",
                "response": {"status_code": 500, "body": {}},
                "error": None,
            },
            # index 2 missing entirely from results -> must still be flagged for retry
        ],
    }
    outputs, repeat_indices = q._parse_openrouter_batch_results(batch, num_queries=3)

    assert outputs[0] == {"output": "hi", "input_tokens": 3, "output_tokens": 1}
    assert outputs[1] is None
    assert outputs[2] is None
    assert sorted(repeat_indices) == [1, 2]


def test_parse_openrouter_batch_results_reasoning_fallback():
    # Live-captured shape (2026-08-21, google/gemini-3.7-flash:batch): reasoning-mandatory
    # models can return content: null with the answer under `reasoning` when finish_reason
    # is "length" (token budget spent on reasoning before the final answer was emitted).
    os.environ["OPENROUTER_API_KEY"] = "or-test"
    q = APIQuery(model="google/gemini-3.7-flash:batch", api="openrouter", max_retries=0)

    batch = {
        "id": "batch_2",
        "status": "completed",
        "results": [
            {
                "custom_id": "apiquery-0",
                "response": {
                    "status_code": 200,
                    "body": {
                        "choices": [{"message": {
                            "content": None,
                            "reasoning": "thinking about it...",
                        }}],
                        "usage": {"prompt_tokens": 7, "completion_tokens": 60},
                    },
                },
                "error": None,
            },
        ],
    }
    outputs, repeat_indices = q._parse_openrouter_batch_results(batch, num_queries=1)
    assert outputs[0]["output"] == "thinking about it...</think>"
    assert repeat_indices == []


if __name__ == "__main__":
    test_groq_resolves_and_keeps_params()
    test_opencode_resolves_and_keeps_params()
    test_openrouter_default_path_keeps_params()
    test_openrouter_batch_allowed_through_gate()
    test_parse_openrouter_batch_results()
    test_parse_openrouter_batch_results_reasoning_fallback()
    print("OK")
