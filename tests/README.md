# Test Suite

Run unit tests:
```bash
pytest tests/unit -v
```

Run integration tests:
```bash
pytest tests/integration -v
```

Run all tests with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```
