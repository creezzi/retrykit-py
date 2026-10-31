# retrykit

A retry decorator with exponential backoff, jitter and selectable exceptions.

## Usage

```python
from retrykit import retry

@retry(attempts=5, base_delay=0.2, exceptions=(ConnectionError,))
def fetch():
    ...
```

## Test

```bash
pip install pytest && pytest
```

## License

MIT
