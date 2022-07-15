from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="simbev",
    version="1.0.0",
    description="Simulation of electric vehicle charging demand",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/rl-institut/simbev",  # Optional
    author="Reiner Lemoine Institut gGmbH",  # Optional
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    # # This field adds keywords for your project which will appear on the
    # # project page. What does your project relate to?
    # #
    # # Note that this is a string of words separated by whitespace, not a list.
    # keywords="",  # Optional
    # When your source code is in a subdirectory under the project root, e.g.
    # `src/`, it is necessary to specify the `package_dir` argument.
    package_dir={"simbev": "./simbev"},  # Optional
    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(),  # Required
    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires=">=3.8",
    # # This field lists other packages that your project depends on to run.
    # # Any package you put here will be installed by pip when your project is
    # # installed, so they must be valid existing projects.
    # #
    # # For an analysis of "install_requires" vs pip's requirements files see:
    # # https://packaging.python.org/en/latest/requirements.html
    install_requires=requirements,
    # # List additional groups of dependencies here (e.g. development
    # # dependencies). Users will be able to install these using the "extras"
    # # syntax, for example:
    # #
    # #   $ pip install sampleproject[dev]
    # #
    # # Similar to `install_requires` above, these must be valid existing
    # # projects.
    # extras_require={"dev": [], "test": []},  # Optional
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    # package_data={  # Optional
    #     'sample': ['package_data.dat'],
    # },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],  # Optional
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    # entry_points={  # Optional
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        "Bug Reports": "https://github.com/rl-institut/simbev/issues",
        "Source": "https://github.com/rl-institut/simbev",
    }
)
