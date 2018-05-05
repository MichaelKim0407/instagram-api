import os

from setuptools import setup, find_packages

root_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root_dir, "VERSION")) as f:
    VERSION = f.read().rstrip()

setup(
    name="mk-instagram-api",

    version=VERSION,

    packages=find_packages(),

    url="https://github.com/MichaelKim0407/instagram-api",

    license="MIT",

    author="Michael Kim",

    author_email="mkim0407@gmail.com",

    description="Object-Oriented Instagram Private API",

    classifiers=[
        "Development Status :: 1 - Planning",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python :: 3.6",

        "Topic :: Software Development :: Libraries",
    ]
)
