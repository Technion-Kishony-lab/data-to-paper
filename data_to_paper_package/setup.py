from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent

setup(
    description='Data to Paper',
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
    name="data_to_paper",
    version='0.1.0',
    python_requires='>=3.8',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        'data_to_paper': [
            'data_to_paper/projects/scientific_research/templates/*',
        ],
        '': ['*.tex']
    },
    install_requires=[
        "requests",
        "openai",
        "numpy",
        "pandas",
        "scikit-learn",
        "statsmodels",
        "xgboost",
        "colorama",
        "unidecode",
        "pygments",
        "regex",
        "scipy",
        "imblearn",
        "tiktoken",
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
