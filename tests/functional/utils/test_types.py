import unittest
from data_to_paper.utils.types import ListBasedSet, MemoryDict


def test_list_based_set():
    s = ListBasedSet([1, 2, 3, 4])
    assert 1 in s
    assert 5 not in s
    assert len(s) == 4
    s.add(5)
    assert 5 in s
    assert len(s) == 5
    s.add(5)
    assert len(s) == 5
    assert str(s) == '{1, 2, 3, 4, 5}'
    assert list(s) == [1, 2, 3, 4, 5]


def test_list_based_set_operations():
    s1 = ListBasedSet([1, 2, 3, 4])
    s2 = ListBasedSet([3, 4, 5, 6])
    assert s1 | s2 == ListBasedSet([1, 2, 3, 4, 5, 6])
    assert s1 & s2 == ListBasedSet([3, 4])
    assert s1 - s2 == ListBasedSet([1, 2])
    assert s2 - s1 == ListBasedSet([5, 6])
    assert s1 ^ s2 == ListBasedSet([1, 2, 5, 6])


def test_list_based_set_comparisons():
    s1 = ListBasedSet([1, 2, 3, 4])
    s2 = ListBasedSet([3, 4, 5, 6])
    s3 = ListBasedSet([4, 3, 2, 1])
    assert s1 == s3
    assert s1 != s2


def test_list_based_set_operations_with_other_types():
    s = ListBasedSet([1, 2, 3, 4])
    assert s | {3, 4, 5, 6} == ListBasedSet([1, 2, 3, 4, 5, 6])
    assert s & {3, 4, 5, 6} == ListBasedSet([3, 4])
    assert s - {3, 4, 5, 6} == ListBasedSet([1, 2])
    assert s ^ {3, 4, 5, 6} == ListBasedSet([1, 2, 5, 6])
    assert {3, 4, 5, 6} - s == ListBasedSet([5, 6])


def test_list_based_set_comparisons_with_other_types():
    s = ListBasedSet([1, 2, 3, 4])
    assert s == {4, 3, 2, 1}
    assert s != {3, 4, 5, 6}


class MemoryDictTests(unittest.TestCase):
    def test_getitem(self):
        my_dict = MemoryDict()
        my_dict['key'] = 'value1'
        my_dict['key'] = 'value2'
        self.assertEqual(my_dict['key'], 'value2')

    def test_add_named_value(self):
        my_dict = MemoryDict()
        my_dict.add_named_value('key', 'name1', 'value1')
        my_dict.add_named_value('key', 'name2', 'value2')
        self.assertEqual(my_dict.get_named_value('key', 'name1'), 'value1')
        self.assertEqual(my_dict.get_named_value('key', 'name2'), 'value2')

    def test_delitem(self):
        my_dict = MemoryDict()
        my_dict['key'] = 'value1'
        del my_dict['key']
        self.assertNotIn('key', my_dict)

    def test_contains(self):
        my_dict = MemoryDict()
        my_dict['key'] = 'value1'
        self.assertIn('key', my_dict)
        self.assertNotIn('nonexistent_key', my_dict)

    def test_len(self):
        my_dict = MemoryDict()
        my_dict['key1'] = 'value1'
        my_dict['key2'] = 'value2'
        self.assertEqual(len(my_dict), 2)
