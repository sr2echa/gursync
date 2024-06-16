from setuptools import setup, find_packages

with open("README.md", "r") as f:
    discription = f.read()

setup(
    name='gursync',
    version='0.1.1',
    author='Sreecharan S.',
    description='a tool that allows users to sync a windows folder with an imgur album, ensuring that both have the same images at all times.',
    url='https://github.com/sr2echa/gursync', 
    packages=find_packages(),
    install_requires=[
        'watchdog',
        'requests',
        'typer',
        'questionary',
    ],
    entry_points={
        'console_scripts': [
            'gursync = gursync.__main__:app',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    long_description=discription,
    long_description_content_type="text/markdown",
)