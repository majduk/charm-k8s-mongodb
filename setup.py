import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="charm-k8s-mongodb",
    version="0.1.0",
    author="Michal Ajduk",
    author_email="michal.ajduk@canonical.com",
    description="Kubernetes Charm for MongoDb",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/majduk/charm-k8s-mongodb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
