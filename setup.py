from setuptools import find_packages, setup

from yari.version import __version__


with open("README.md", "r", encoding="utf8") as description:
    readme = description.read()

setup(
    name="Yari",
    version=__version__,
    packages=find_packages(),
    package_data={"yari": ["sources/*.yml"]},
    url="https://taylormarcus.github.io/Yari/",
    license="MIT",
    author="Marcus T Taylor",
    description="Generate 5th edition Dungeons & Dragons characters.",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=[
        "aiohttp~=3.6.2",
        "beautifulsoup4~=4.9.1",
        "click~=7.1.2",
        "lxml~=4.5.2",
        "PyYAML~=5.3.1",
    ],
    python_requires=">=3.0",
    entry_points={"console_scripts": ["yari=yari:main"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Topic :: Games/Entertainment :: Role-Playing",
    ],
)
