import os
import setuptools


def _read_reqs(relpath):
    fullpath = os.path.join(os.path.dirname(__file__), relpath)
    with open(fullpath) as f:
        return [s.strip() for s in f.readlines() if (s.strip() and not s.startswith("#"))]


setup_common_args = {
    "include_package_data": True,
    "packages": setuptools.find_packages(where=".", include=["app"]).append("html_encoder"),
}
setuptools.setup(
    name="html_encoder",
    author="Dan Kelman",
    author_email="danjkelman@gmail.com",
    version="1.0.0",
    install_requires=_read_reqs("requirements.txt"),
    **setup_common_args,
)
