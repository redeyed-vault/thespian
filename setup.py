from setuptools import find_packages, setup

from yari.version import __version__


setup(
    name="Yari",
    version=__version__,
    packages=find_packages(),
    package_data={"yari": ["sources/*.yml"]},
    url="https://taylormarcus.github.io/Yari/",
    license="MIT",
    author="Marcus T Taylor",
    description="Generate 5th edition Dungeons & Dragons characters.",
    long_description=open("README.md", "r", encoding="utf8", errors="ignore").read(),
    long_description_content_type="text/markdown",
    install_requires=["beautifulsoup4", "click", "lxml", "maya", "PyYAML", ],
    python_requires=">=3.0",
    entry_points={"console_scripts": ["yari=yari.shell:main"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
)
