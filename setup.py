import os
from setuptools import setup, find_packages


setup(
    name="lifelogger",
    version="0.0.1",
    packages=find_packages(where=['lifelogger']),
    author="Ilya Telvanni",
    author_email="ilya_telvanni@yandex.ru",
    license="proprietary",
    python_requires='>=3.10.2',
    install_requires=[
        'aiohttp==3.8.3',
        'aiosqlite==0.18.0',
        'greenlet==2.0.1',
        'SQLAlchemy==1.4.46'
    ],
    extras_require={
        'testing': [
            "pytest",
            "pytest-asyncio"
        ],
        'mypy': ['mypy']
    },
    description="",
    url="https://github.com/ilyatelvanni-work/lifelogger"
)
