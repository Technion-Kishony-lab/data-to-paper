from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent

setup(
    description='Goal-Guided GPT',
    author="Kishony lab, Technion Israel Institute of Technology",
    author_email="rkishony@technion.ac.il",
    url="https://github.com/Technion-Kishony-lab/g3pt",
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
    name="scientistgpt",
    version='0.0.1',
    python_requires='>=3.8',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "openai",
        "numpy",
        "pandas",
        "colorama",
        "unidecode",
        "pygments",
        "regex",
        "scipy",
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
