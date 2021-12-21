# simBEV

Simulation of electric vehicle charging demand.

## Download/install

### Install using pip

First, clone via SSH using

    git clone git@github.com:rl-institut/simbev.git /local/path/to/simbev/

Make sure you have Python >= 3.9 installed, let's create a virtual env:

    virtualenv --python=python3.8 simbev
    source simbev/bin/activate

Install package with

    pip install -e /local/path/to/simbev/

### Install using conda

Make sure you have conda installed, e.g. miniconda. Then create the env:
    
    conda create -n simbev /local/path/to/simbev/environment.yml
    conda activate simbev

## Run SimBEV

- You can use a default scenario or define a custom one in the directory `scenarios`, see
  [scenario readme](./simbev/scenarios/README.md) for further instructions
- Run main_simbev.py with the desired scenario: `python main_simbev.py <SCENARIO_NAME>`
  (defaults to `python main_simbev.py default_single`)
- Results are created in directory `res`

## Set parameters for your scenario

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
