from dataclasses import dataclass


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: str  # a user provided description of the file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file.
        """
        with open(self.file_path) as f:
            head = [next(f) for _ in range(num_lines)]
            return ''.join(head)

    def pretty_repr(self):
        return f'{self.file_path}\n{self.description}\n' \
               f'Here are the first few lines of the file:\n' \
               f'{self.get_file_header()}'
