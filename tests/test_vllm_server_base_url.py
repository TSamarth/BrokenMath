"""Self-check: vllm_server api honors per-model base_url/api_key, falls back to localhost."""
from sycophancy.api import APIQuery


def test_remote_base_url_and_api_key():
    q = APIQuery(model="dummy", api="vllm_server", base_url="http://remote:1234/v1",
                 api_key="my-key", max_tokens=16)
    assert q.base_url == "http://remote:1234/v1"
    assert q.api_key == "my-key"
    assert q.api == "openai"
    assert "base_url" not in q.kwargs
    assert "api_key" not in q.kwargs


def test_default_localhost_fallback():
    q = APIQuery(model="dummy", api="vllm_server", max_tokens=16)
    assert q.base_url == "http://localhost:8000/v1"
    assert q.api_key == "token-abc123"


if __name__ == "__main__":
    test_remote_base_url_and_api_key()
    test_default_localhost_fallback()
    print("OK")
