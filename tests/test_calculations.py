import pytest
from calculations import add


@pytest.mark.parametrize("n1, n2, expected", [
    (3, 2, 5),
    (7, 1, 8)
])
def test_add(n1, n2, expected):
    print("Testing add function")
    assert add(n1,n2) == expected

