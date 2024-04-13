import pickle
import os
import hashlib
from dataclasses import asdict, dataclass

from pathlib import Path
from typing import Union

from data_to_paper.run_gpt_code.run_contexts import TrackCreatedFiles
from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.print_to_file import print_and_log


def directory_hash(directory):
    """Create a hash based on all files in the directory."""
    hasher = hashlib.sha256()
    for path, dirs, filenames in os.walk(directory):
        for filename in sorted(filenames):
            file_path = os.path.join(path, filename)
            # Consider the file path and the file contents
            hasher.update(file_path.encode('utf-8'))
            with open(file_path, 'rb') as file:
                while chunk := file.read(8192):
                    hasher.update(chunk)
    return hasher.hexdigest()


def _read_file(filename):
    with open(filename, 'rb') as f:
        return f.read()


def _write_file(filename, content):
    with open(filename, 'wb') as f:
        f.write(content)


def _read_files(filenames):
    file_contents = {}
    for fname in filenames:
        file_contents[fname] = _read_file(fname)
    return file_contents


def _write_files(filenames):
    for fname, content in filenames.items():
        _write_file(fname, content)


@dataclass
class CacheRunToFile:
    """
    A class that caches the results of a 'run' method to a file.
    Also caches the files created during the run.
    Files pre-existing in the run directory are considered part of the run input.
    """
    cache_filepath: Union[str, Path] = None

    def _get_instance_key(self) -> tuple:
        return tuple(asdict(self).values())

    def _get_run_directory_key(self) -> tuple:
        return (directory_hash(self._get_run_directory()), )

    def _get_run_directory(self):
        raise NotImplementedError

    def _run(self, *args, **kwargs):
        raise NotImplementedError

    def _load_cache(self, filename=None):
        filename = filename or self.cache_filepath
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                return pickle.load(f)
        return {}

    def _dump_cache(self, cache, filename=None):
        filename = filename or self.cache_filepath
        with open(filename, 'wb') as f:
            pickle.dump(cache, f)

    def run(self, *args, **kwargs):
        """
        Cache the results of a call to _run().
        """
        cache = self._load_cache()
        key = self._get_instance_key() + self._get_run_directory_key() \
            + tuple(args) + tuple(kwargs.items())

        if key in cache:
            print_and_log(f"{self.__class__.__name__}: Using cached output.")
            results, filenames = cache[key]
            with run_in_directory(self._get_run_directory()):
                _write_files(filenames)
            return results

        print_and_log(f"{self.__class__.__name__}: Running and caching output.")
        # Call the function and cache the result along with any created files
        with run_in_directory(self._get_run_directory()):
            with TrackCreatedFiles() as track_created_files:
                results = self._run(*args, **kwargs)
            file_contents = _read_files(track_created_files.created_files)

        # Update cache
        cache[key] = (results, file_contents)
        self._dump_cache(cache)

        return results
