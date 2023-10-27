~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Installing SimBEV
=================

Install using pip
-----------------

First, clone via SSH:

.. code:: bash

    git clone git@github.com:rl-institut/simbev.git /local/path/to/simbev/

or via HTTPS:

.. code:: bash

    git clone https://github.com/rl-institut/simbev.git

Make sure you have Python >= 3.8 installed, let's create a virtual env:

.. code:: bash

    python3 -m venv venv
    source venv/bin/activate

Install package with

.. code:: bash

    pip install -e /local/path/to/simbev/

Install using conda
-------------------

Make sure you have conda installed, e.g. miniconda. Then create the env:

.. code:: bash

    conda create -n simbev /local/path/to/simbev/environment.yml
    conda activate simbev


Start Simulating
================

The following code already simulates the default scenario in the folder scenarios/default/.

.. code:: bash

    python -m simbev

More about simulating: :doc:`usage_details`
