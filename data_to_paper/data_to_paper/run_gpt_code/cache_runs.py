import pickle
import os
import hashlib
import time
import traceback

from traceback import FrameSummary

from contextlib import contextmanager
from dataclasses import asdict, dataclass

from pathlib import Path
from typing import Union

from data_to_paper.env import DELAY_CODE_RUN_CACHE_RETRIEVAL
from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.print_to_file import print_and_log


def old_directory_hash(directory):
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


def directory_hash(directory):
    """
    Create a hash based on all files in the directory, hashing only the relative path of each file
    from the specified directory.
    """
    hasher = hashlib.sha256()
    root_dir = os.path.abspath(directory)
    all_files = []

    # Walk the directory tree and capture all file paths
    for path, dirs, files in os.walk(root_dir):
        for file in files:
            full_path = os.path.join(path, file)
            relative_path = os.path.relpath(full_path, start=directory)  # Compute the relative path
            all_files.append((relative_path, full_path))  # Store both relative and full path

    # Sort all file paths by relative path
    all_files.sort(key=lambda x: x[0])

    # Hash each file's relative path and contents
    for relative_path, full_path in all_files:
        hasher.update(relative_path.encode('utf-8'))
        with open(full_path, 'rb') as file:
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


# TODO: hack for python version compatibility. Remove when possible.
class CustomFrameSummary(FrameSummary):
    @property
    def end_lineno(self):
        # Return a default value or None if 'end_lineno' is not available
        return getattr(self, '_end_lineno', None)

    @end_lineno.setter
    def end_lineno(self, value):
        self._end_lineno = value


traceback.FrameSummary = CustomFrameSummary


@dataclass
class CacheRunToFile:
    """
    A class that caches the results of a 'run' method to a file.
    Also caches the files created during the run.
    Files pre-existing in the run directory are considered part of the run input.
    """
    cache_filepath: Union[str, Path] = None  # Path to the cache file, or None to disable caching

    def _get_instance_key(self) -> tuple:
        return tuple(asdict(self).values())

    def _get_run_directory_key(self) -> tuple:
        return (directory_hash(self._get_run_directory()), )

    def _get_run_directory_old_key(self) -> tuple:
        return (old_directory_hash(self._get_run_directory()), )

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
        if self.cache_filepath is None:
            return self._run(*args, **kwargs)

        cache = self._load_cache()
        key = self._get_instance_key() + self._get_run_directory_key() \
            + tuple(args) + tuple(kwargs.items())

        old_key = self._get_instance_key() + self._get_run_directory_old_key() \
            + tuple(args) + tuple(kwargs.items())

        if old_key in cache:
            # replace old key with new key
            print(f"{self.__class__.__name__}: Replacing old key with new key.")
            cache[key] = cache.pop(old_key)
            self._dump_cache(cache)

        if key in cache:
            print_and_log(f"{self.__class__.__name__}: Using cached output.")
            time.sleep(DELAY_CODE_RUN_CACHE_RETRIEVAL.val)
            results, filenames = cache[key]
            with run_in_directory(self._get_run_directory()):
                _write_files(filenames)
            return results

        print_and_log(f"{self.__class__.__name__}: Running and caching output.")
        # Call the function and cache the result along with any created files
        with run_in_directory(self._get_run_directory()):
            with get_created_files() as created_files:
                results = self._run(*args, **kwargs)
            file_contents = _read_files(created_files)

        # Update cache
        cache[key] = (results, file_contents)
        self._dump_cache(cache)

        return results


@contextmanager
def get_created_files():
    """
    Context manager for returning all new files created in the current directory.
    Files are returned as a sorted list of filenames.
    Note: The files are not deleted after the context manager exits.
    """
    # we need to preserve the filenames and metadata of the files
    preexisting_files_and_metadata = set()
    for filename in os.listdir():
        preexisting_files_and_metadata.update(_get_filename_and_metadata(filename))

    created_files = []
    try:
        yield created_files
    finally:
        for filename in sorted(os.listdir()):
            if _get_filename_and_metadata(filename) not in preexisting_files_and_metadata:
                created_files.append(filename)


def _get_filename_and_metadata(filename):
    return filename, os.stat(filename).st_mtime
