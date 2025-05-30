def pytest_addoption(parser):
    parser.addoption("--include-ai", action="store_true", help="run OpenAI tests")