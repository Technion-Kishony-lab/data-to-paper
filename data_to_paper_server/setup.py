from setuptools import setup, find_packages

setup(
    description='A chatgpt based scientist allowing automatic analysis and paper writing',
    author="Kishony lab, Technion Israel Institute of Technology",
    author_email="rkishony@technion.ac.il",
    url="https://github.com/Technion-Kishony-lab/data_to_paper",
    name="data_to_paper_server",
    version='0.0.1',
    python_requires='>=3.8',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-socketio",
        "gipc",
        "gevent",
    ]
)
