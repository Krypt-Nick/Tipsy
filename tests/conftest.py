def pytest_addoption(parser):
    parser.addoption("--include-ai", action="store_true", help="run OpenAI tests")

import os
import pytest

@pytest.fixture(autouse=True)
def clear_openai_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)