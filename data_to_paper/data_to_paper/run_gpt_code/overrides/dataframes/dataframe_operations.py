from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Iterable

from data_to_paper.utils.types import ListBasedSet


@dataclass(frozen=True)
class DataframeOperation:
    id: int


@dataclass(frozen=True)
class FileDataframeOperation(DataframeOperation):
    file_path: Optional[str]
    columns: Optional[Iterable]

    @property
    def filename(self):
        if self.file_path is None:
            return None
        return Path(self.file_path).name


@dataclass(frozen=True)
class CreationDataframeOperation(FileDataframeOperation):
    created_by: Optional[str]


@dataclass(frozen=True)
class SaveDataframeOperation(FileDataframeOperation):
    pass


@dataclass(frozen=True)
class SeriesDataframeOperation(DataframeOperation):
    series_name: str


@dataclass(frozen=True)
class AddSeriesDataframeOperation(SeriesDataframeOperation):
    pass


@dataclass(frozen=True)
class RemoveSeriesDataframeOperation(SeriesDataframeOperation):
    pass


@dataclass(frozen=True)
class ChangeSeriesDataframeOperation(SeriesDataframeOperation):
    pass


class DataframeOperations(List[DataframeOperation]):

    def get_read_ids(self) -> ListBasedSet[int]:
        return ListBasedSet(operation.id for operation in self
                            if isinstance(operation, CreationDataframeOperation) and operation.file_path is not None)

    def get_changed_ids(self) -> ListBasedSet[int]:
        return ListBasedSet(operation.id for operation in self if isinstance(operation, SeriesDataframeOperation))

    def get_saved_ids(self) -> ListBasedSet[int]:
        return ListBasedSet(operation.id for operation in self if isinstance(operation, SaveDataframeOperation))

    def get_saved_ids_filenames(self) -> ListBasedSet[Tuple[int, str]]:
        return ListBasedSet((operation.id, operation.filename) for operation in self
                            if isinstance(operation, SaveDataframeOperation))

    def get_read_filename(self, id_: int) -> Optional[str]:
        return next((operation.filename for operation in self
                     if isinstance(operation, CreationDataframeOperation) and operation.id == id_), None)

    def get_read_changed_but_unsaved_ids(self):
        return self.get_read_ids() & self.get_changed_ids() - self.get_saved_ids()

    def get_read_filenames_from_ids(self, ids: Iterable[int]) -> ListBasedSet[Optional[str]]:
        return ListBasedSet(operation.filename for operation in self
                            if operation.id in ids and isinstance(operation, CreationDataframeOperation))

    def get_creation_columns(self, id_: int) -> Optional[List[str]]:
        return next((operation.columns for operation in self
                     if isinstance(operation, CreationDataframeOperation) and operation.id == id_), None)

    def get_save_columns(self, id_: int) -> Optional[List[str]]:
        return next((operation.columns for operation in self
                     if isinstance(operation, SaveDataframeOperation) and operation.id == id_), None)

    def get_changed_columns(self, id_: int) -> List[str]:
        return [operation.series_name for operation in self
                if isinstance(operation, ChangeSeriesDataframeOperation) and operation.id == id_]
