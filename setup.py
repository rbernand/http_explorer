from setuptools import setup, find_packages


with open('requirements.txt') as requirements_file:
    requirements = requirements_file.readlines()


setup(
    name='http-explorer',
    version='0.0.1',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'http-explorer = http_explorer.main:main',
        ]
    },
)
