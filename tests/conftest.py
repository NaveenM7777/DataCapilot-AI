import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# The agents use relative paths such as "database/chinook.db",
# so make sure tests always run from the project root.
os.chdir(Path(__file__).resolve().parent.parent)

from api.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)