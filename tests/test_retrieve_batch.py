"""Self-check: retrieve_batch() completes on a finished batch without hanging
(regression for the breakpoint() left in api.py:1252 that blocked all
batch_processing runs)."""
import os
from unittest.mock import MagicMock, patch

from sycophancy.api import APIQuery


def _fake_line(custom_id, status_code=200):
    import json
    return json.dumps({
        "custom_id": custom_id,
        "response": {
            "status_code": status_code,
            "body": {
                "choices": [{"message": {"content": "42"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        },
    }).encode()


def test_retrieve_batch_completes_without_hanging():
    os.environ["OPENAI_API_KEY"] = "sk-test"
    q = APIQuery(model="gpt-5-mini", api="openai", max_tokens=16, max_retries=0)

    batch = MagicMock()
    batch.request_counts = {"completed": 2, "failed": 0}
    batch.status = "completed"
    batch.output_file_id = "file-1"

    file_response = MagicMock()
    file_response.iter_lines.return_value = [
        _fake_line("apiquery-0"),
        _fake_line("apiquery-1"),
    ]

    fake_client = MagicMock()
    fake_client.batches.retrieve.return_value = batch
    fake_client.files.content.return_value = file_response

    with patch("sycophancy.api.OpenAI", return_value=fake_client), \
         patch("sycophancy.api.time.sleep"):
        outputs = q.retrieve_batch(queries=[("q0", None), ("q1", None)], batch_id="batch-1")

    assert len(outputs) == 2
    assert outputs[0]["output"] == "42"
    assert outputs[1]["output"] == "42"


if __name__ == "__main__":
    test_retrieve_batch_completes_without_hanging()
    print("OK")
