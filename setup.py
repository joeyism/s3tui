from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="s3tui",
    version="0.1.0",
    author="joeyism",
    author_email="joeyism101@example.com",
    description="Terminal User Interface for AWS S3 with ranger-style navigation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joeyism/s3tui",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "boto3>=1.28.0",
        "textual>=0.47.0",
    ],
    entry_points={
        "console_scripts": [
            "s3tui=s3tui.__main__:main",
        ],
    },
)
