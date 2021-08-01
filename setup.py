from setuptools import setup, find_packages

with open('requirements.txt') as file:
    required = file.read().splitlines()

setup(
        name="spatial_interpolation",
        version="0.1",
        install_requires=required,
        packages=find_packages(),
        description="Spatial interpolation for IoT datasets.",
        author="Harvey Bates"
        )
