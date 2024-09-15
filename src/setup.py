from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent

setup(
    description='data-to-paper',
    author="Kishony lab, Technion Israel Institute of Technology",
    author_email="rkishony@technion.ac.il",
    url="https://github.com/Technion-Kishony-lab/data_to_paper",
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
    scripts=[
        'data_to_paper/scripts/run.py',
    ],
    name="data_to_paper",
    version='0.1.0',
    python_requires='>=3.9',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        '': ['*.tex']
    },
    install_requires=[
        "colorama",
        "openai",
        "regex",
        "tiktoken",
        "pygments",
        "requests",
        "unidecode",
        "PyMuPDF",
        "py-spy",
        "ansi2html",
        "PySide6",

        # packages for the LLM code:
        "numpy",
        "pandas",
        "statsmodels",
        "scipy",
        "scikit-learn",  # sklearn
        "networkx",
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
