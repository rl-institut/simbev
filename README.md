# Download and run SimBEV

## Download/install

- clone repository to your local machine
- install requirements found in requirements.txt (virtualenv recommended)

## Run SimBEV

- you can use a default scenario or define a custom one in the directory `scenarios`, see
  [scenario readme](./simbev/scenarios/README.md) for further instructions
- run main_simbev.py with the desired scenario: `python main_simbev.py <SCENARIO_NAME>`
  (defaults to `python main_simbev.py default_single`)
- results are created in directory `res`

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

