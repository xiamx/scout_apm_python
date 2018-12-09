import os

import pytest

from scout_apm.core.config import SCOUT_PYTHON_VALUES

# Env variables have precedence over Python configs in ScoutConfig.
# Unset all Scout env variables to prevent interference with tests.

for key in os.environ.keys():
    if key.startswith("SCOUT_"):
        del os.environ[key]


class GlobalStateLeak(Exception):
    """Exception raised when a test leaks global state."""


class ConfigLeak(GlobalStateLeak):
    """Exception raised when a test leaks changes in ScoutConfig."""


@pytest.fixture(autouse=True)
def isolate_global_state():
    """
    Isolate global state in ScoutConfig.

    Since scout_apm relies heavily on global variables, it's unfortunately
    easy to leak state changes after a test, which can affect later tests.
    This fixture acts as a safety net. It checks after each test if global
    state was properly reset. If not, it fails the test.

    (An alternative would be to clean up here rather than in each test. The
    original author of this fixture is uncomfortable with such an implicit
    behavior. He prefers enforcing an explicit clean up in tests, requiring
    developers to understand how their test affects global state.)

    RequestManager and RequestBuffer aren't convered because the current
    implementation doesn't buffer anything.

    """
    try:
        yield
    finally:
        SCOUT_ENV_VARS = {
            key: value for key, value in os.environ.items() if key.startswith("SCOUT_")
        }
        if SCOUT_ENV_VARS:
            raise ConfigLeak("Env config changes: %r" % SCOUT_ENV_VARS)
        if SCOUT_PYTHON_VALUES:
            raise ConfigLeak("Python config changes: %r" % SCOUT_PYTHON_VALUES)


try:
    from tempfile import TemporaryDirectory
except ImportError:  # Python < 3.2
    from contextlib import contextmanager
    from tempfile import mkdtemp
    from shutil import rmtree

    @contextmanager
    def TemporaryDirectory():
        tempdir = mkdtemp()
        try:
            yield tempdir
        finally:
            rmtree(tempdir)


# Create a temporary directory for the duration of the test session to ensure
# isolation and to avoid downloading the core agent in each test.
@pytest.fixture(scope="session")
def core_agent_dir():
    with TemporaryDirectory() as temp_dir:
        yield temp_dir
