from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent
long_description = (setup_directory / "README.md").read_text(encoding="utf-8")

setup(
    description='A chatgpt based scientist allowing automatic analysis and paper writing',
    author="Kishony lab, Technion Israel Institute of Technology",
    author_email="rkishony@technion.ac.il",
    url="https://github.com/Technion-Kishony-lab/data2paper",
    classifiers=[
        'Framework :: Jupyter',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Information Technology',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
    name="data2paper",
    version='0.0.1',
    python_requires='>=3.8',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "openai",
        "numpy",
        "pandas",
        "colorama",
        "unidecode"
        "pygments",
        "regex",
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov',
            'pytest-benchmark',
            'pytest-benchmark',
        ],
    }
)
