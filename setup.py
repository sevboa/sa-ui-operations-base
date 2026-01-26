from setuptools import setup, find_packages
from pathlib import Path

# Читаем README для длинного описания
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="sa-ui-operations-base",
    version="1.2.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="Универсальная библиотека для создания GUI приложений на PySide6 с системой плагинов",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sevboa/sa-ui-operations-base",
    packages=find_packages(exclude=["examples", "tests", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sa-ui-operations=sa_ui_operations.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

