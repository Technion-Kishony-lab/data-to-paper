from _pytest.fixtures import fixture

from scientistgpt.base_products import DataFileDescription, DataFileDescriptions


class TestDataFileDescription(DataFileDescription):
    def get_file_header(self, num_lines: int = 4):
        return f"Header of {self.file_path}, {num_lines} lines\n"


@fixture()
def data_file_descriptions():
    return DataFileDescriptions(
        [
            TestDataFileDescription(
                file_path="fileA.txt",
                description="Description of fileA.txt",
                originated_from=None,
            ),
            TestDataFileDescription(
                file_path="fileB.txt",
                description="Description of fileB.txt",
                originated_from=None,
            ),
            TestDataFileDescription(
                file_path="fileC.txt",
                description="Description of fileC.txt",
                originated_from=None,
            ),
            TestDataFileDescription(
                file_path="fileA_modified.txt",
                description="Description of fileA_modified.txt",
                originated_from="fileA.txt",
            ),
            TestDataFileDescription(
                file_path="fileB_modified.txt",
                description="Description of fileB_modified.txt",
                originated_from="fileB.txt",
            ),
            TestDataFileDescription(
                file_path="fileA_modified_modified.txt",
                description="Description of fileA_modified_modified.txt",
                originated_from="fileA_modified.txt",
            ),
        ]
    )


def test_data_file_descriptions_repr(data_file_descriptions):
    description = str(data_file_descriptions)
    correct_order = ['fileA.txt', 'fileA_modified.txt', 'fileA_modified_modified.txt', 'fileB.txt',
                     'fileB_modified.txt', 'fileC.txt']
    previous_index = -1
    for should_be in correct_order:
        assert should_be in description
        index = description.find(should_be)
        assert index > previous_index
        previous_index = index

    print(description)

    should_have_header = ['fileA_modified_modified.txt', 'fileB_modified.txt', 'fileC.txt']
    for should_be in should_have_header:
        assert data_file_descriptions.get_file_description(should_be).get_file_header() in description

    should_not_have_header = ['fileA.txt', 'fileA_modified.txt', 'fileB.txt']
    for should_be in should_not_have_header:
        assert data_file_descriptions.get_file_description(should_be).get_file_header() not in description
