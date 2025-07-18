from setuptools import setup, find_packages

setup(
    name="whatsapp-flow-tester",
    version="1.0.0",
    description="Dynamic WhatsApp flow testing framework",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai>=1.0.0",
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "openpyxl>=3.1.0",
        "pytz>=2023.3",
        "rich>=13.0.0",
        "asyncio-throttle>=1.0.0",
        "colorama>=0.4.6",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "whatsapp-flow-tester=flow_tester.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
