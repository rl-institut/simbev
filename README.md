<img align="right" width="150" src="https://github.com/rl-institut/simbev/blob/master/docs/img/rli_logo.png">

# SimBEV

Simulation of electric vehicle charging demand.

## Documentation

The full documentation can be found [here](https://simbev.readthedocs.io/en/latest/)

## Installation

### Install using pip

First, clone via SSH using

    git clone git@github.com:rl-institut/simbev.git /local/path/to/simbev/

Make sure you have Python >= 3.8 installed, let's create a virtual env:

    virtualenv --python=python3.8 simbev
    source simbev/bin/activate

Install package with

    pip install -e /local/path/to/simbev/

### Install using conda

Make sure you have conda installed, e.g. miniconda. Then create the env:
    
    conda env create -n simbev -f /local/path/to/simbev/environment.yml
    conda activate simbev

## Run simBEV

### Get the data
If you want to run SimBEV in the mode using probabilities, a data set is available [here](https://zenodo.org/record/7609683)

### Create a scenario
- You can use a default scenario or define a custom one in the directory `scenarios`
- Run simbev with the desired scenario: `python -m simbev path/to/config`
  (defaults to `python -m simbev scenarios/default/configs/default.cfg`)
- Results are created in the subdirectory `results` in the scenario directory

### Set parameters for your scenario

Select regio-type for the mobility characteristics:
- regiotypes:
Ländliche Regionen
LR_Klein - Kleinstädtischer, dörflicher Raum
LR_Mitte - Mittelstädte, städtischer Raum
LR_Zentr - Zentrale Stadt
Stadtregionen
SR_Klein - Kleinstädtischer, dörflicher Raum
SR_Mitte - Mittelstädte, städtischer Raum
SR_Gross - Regiopolen, Großstädte
SR_Metro - Metropole

Change vehicle configuration
- battery capacity
- charging power (slow and fast)
- consumption

Decide how many vehicles should be simulated
- note: more than 5000 vehicles of one type in one region is not necessary, if you want to analyze more, scale it accordingly

## License

see [LICENSE](LICENSE)
