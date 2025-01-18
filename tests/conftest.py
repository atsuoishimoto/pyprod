import pytest

import pyprod
from pyprod import main

pyprod.verbose = 2


@pytest.fixture(autouse=True)
def init_args():
    main.init_args([])
