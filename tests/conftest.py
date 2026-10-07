import pytest_asyncio

pytest_asyncio.plugin = True


@pytest_asyncio.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()