import pytest
import os

@pytest.fixture
def paths():
    base_dir = get_base_dir()
    return dict(
        base_dir=base_dir,
        data_dir=os.path.join(base_dir, "data"),
        mappings_dir=os.path.join(base_dir, "mappings"),
        references_dir=os.path.join(base_dir, "references"),
    )

def get_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path_parts = script_dir.split(os.sep)
    idx = path_parts.index("tests") + 1
    base_dir = os.path.join(os.sep, *path_parts[0:idx])
    return base_dir
