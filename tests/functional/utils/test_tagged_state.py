from dataclasses import dataclass

from _pytest.fixtures import fixture

from g3pt.utils.tagged_state import TaggedState


@dataclass
class TestTaggedState(TaggedState):
    a: int = 1
    b: int = 10

    def increment(self):
        self.a += 1
        self.b += 10


@fixture()
def tagged_state():
    return TestTaggedState()


def test_tagged_state_restores_to_tag(tagged_state):
    tagged_state.store_state('tag1')
    tagged_state.increment()
    tagged_state.restore_state('tag1')
    assert tagged_state.a == 1
    assert tagged_state.b == 10


def test_tagged_state_removes_tags_downstream_of_restored_tag(tagged_state):
    tagged_state.store_state('tag1')
    tagged_state.increment()
    tagged_state.store_state('tag2')
    tagged_state.increment()
    tagged_state.store_state('tag3')
    tagged_state.increment()
    tagged_state.restore_state('tag2')
    assert tagged_state.a == 2
    assert tagged_state.b == 20
    assert tagged_state.is_tag('tag1')
    assert tagged_state.is_tag('tag2')
    assert not tagged_state.is_tag('tag3')


def test_tagged_state_creates_tag_if_not_exist(tagged_state):
    tagged_state.create_or_reset_to_tag('tag1')
    tagged_state.increment()
    tagged_state.create_or_reset_to_tag('tag2')
    tagged_state.increment()
    tagged_state.create_or_reset_to_tag('tag1')
    assert tagged_state.a == 1
    assert tagged_state.b == 10
