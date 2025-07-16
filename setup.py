from setuptools import setup, find_packages
import os

# Get version from environment or default
version = os.environ.get('PACKAGE_VERSION', '3.0.0')

# Read requirements with fallback
requirements = []
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    # Fallback requirements if file not found
    requirements = [
        "requests>=2.25.0",
        "openai>=1.0.0",
    ]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="retrochat-cli",
    version=version,
    author="DefamationStation",
    author_email="your-email@example.com",
    description="Multi-Provider AI Chat Application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DefamationStation/retrochat-v3",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rchat=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "LICENSE"],
    },
)
