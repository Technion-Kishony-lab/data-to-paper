import os
from dataclasses import dataclass
from pathlib import Path

from data_to_paper.run_gpt_code.cache_runs import CacheRunToFile


@dataclass
class TestCacheRunToFile(CacheRunToFile):
    cache_filepath: Path = 'cache.pkl'
    run_directory: Path = None
    called_count: int = 0
    result: str = None
    write_files: bool = False

    def _get_instance_key(self) -> tuple:
        return (self.result, )

    def _get_run_directory(self):
        return self.run_directory

    def _run(self):
        self.called_count += 1
        if self.write_files:
            with open('result.txt', 'w') as f:
                f.write(self.result)
        return self.result


def get_runner(result, write_files=False):
    return TestCacheRunToFile(result=result,
                              write_files=write_files,
                              cache_filepath=Path('cache').joinpath('cache.pkl').absolute(),
                              run_directory=Path('output').absolute()
                              )


def test_cache_method_output_to_file(tmpdir):
    os.chdir(tmpdir)
    os.mkdir('cache')
    os.mkdir('output')
    runner = get_runner('hello')
    assert runner.run() == 'hello'
    assert runner.called_count == 1
    assert runner.run() == 'hello'
    assert runner.called_count == 1

    # check the cache file was loaded
    runner.result = 'world'
    assert runner.run() == 'world'
    assert runner.called_count == 2

    # check with new instance
    runner = get_runner('hello')
    assert runner.run() == 'hello'
    assert runner.called_count == 0
    runner.result = 'world'
    assert runner.run() == 'world'
    assert runner.called_count == 0


def test_cache_method_output_to_file_with_created_files(tmpdir):
    os.chdir(tmpdir)
    os.mkdir('cache')
    os.mkdir('output')
    instance = get_runner('hello', write_files=True)
    assert instance.run() == 'hello'
    assert instance.called_count == 1
    # check that the file was written:
    with open('output/result.txt') as f:
        assert f.read() == 'hello'
    # delete the file and check that it is read from the cache
    os.remove('output/result.txt')
    assert instance.run() == 'hello'
    assert instance.called_count == 1
    # check that the file was written:
    with open('output/result.txt') as f:
        assert f.read() == 'hello'
