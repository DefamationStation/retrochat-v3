#!/usr/bin/env python3
"""
Setup script for RetroChat CLI
"""
from setuptools import setup, find_packages

setup(
    name="retrochat",
    version="1.0.0",
    description="A minimalistic CLI chat application with modular architecture for LM Studio",
    author="RetroChat Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "lmstudio>=0.2.31",
        "colorama>=0.4.6",
        "typing-extensions>=4.8.0",
    ],
    entry_points={
        "console_scripts": [
            "retrochat=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
