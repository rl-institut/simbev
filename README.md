# Download and run SimBEV

## Download/install

- clone repository to your local machine
- install requirements found in requirements.txt

## Run SimBEV

- change config-file to the setting for your scenario
- run main_simbev.py
- results are found in 'res'-folder

## Set paramters for your scenario

Select regio-type for the mobility characteristics:
- regiotypes:
# Ländliche Regionen
# LR_Klein - Kleinstädtischer, dörflicher Raum
# LR_Mitte - Mittelstädte, städtischer Raum
# LR_Zentr - Zentrale Stadt
# Stadtregionen
# SR_Klein - Kleinstädtischer, dörflicher Raum
# SR_Mitte - Mittelstädte, städtischer Raum
# SR_Gross - Regiopolen, Großstädte
# SR_Metro - Metropole

Change vehicle configuration
- battery capacity
- charging power (slow and fast)
- consumption

Decide how many vehicles should be simulated
- note: more than 5000 vehicles of one type in one region is not necessary, if you want to analyze more, scale it accordingly

