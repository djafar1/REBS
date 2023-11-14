import runpy
from os.path import dirname, join
from pathlib import Path
from setuptools import setup, find_packages


# Import only the metadata of the pm4py to use in the setup. We cannot import it directly because
# then we need to import packages that are about to be installed by the setup itself.
meta_path = Path(__file__).parent.absolute() / "pm4py" / "meta.py"
meta = runpy.run_path(str(meta_path))


def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


setup(
    name='pm4pyDCR',
    version='1.0',
    description="This is extension to the open source library pm4py, this extension provide a basis functionality to perform process mining techniques, currently supported technique are process discovery using the DisCoveR miner, and conformance checking using alignments and rule based approaches",
    long_description=read_file('README.md'),
    author='Jonas Kjeldsen, Simon Hermansen and Ragnar Jónsson',
    author_email=['jonas.lykke.kjeldsen@gmail.com, simonhermansen5dk@gmail.com, ragnarlaki@gmail.com'],
    include_package_data=True,
    packages=[x for x in find_packages() if x.startswith("pm4py")],
    license='GPL 3.0',
    install_requires=read_file("requirements.txt").split("\n"),
    project_urls='https://github.com/paul-cvp/pm4py-dcr/tree/develop'
)
