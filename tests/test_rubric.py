from kriyon_bd.scoring.rubric import AXIS_NAMES, Rubric


def test_rubric_loads_from_config():
    rubric = Rubric.load()

    assert rubric.version
    assert isinstance(rubric.threshold, int)
    assert 0 <= rubric.threshold <= 20
    assert set(rubric.axis_descriptions) == set(AXIS_NAMES)
    for description in rubric.axis_descriptions.values():
        assert description
