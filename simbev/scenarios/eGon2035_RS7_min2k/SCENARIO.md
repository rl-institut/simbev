# Scenario: eGon2035

This is a sample scenario for Germany using the RegioStaR7 regions with the following parameters:

- Total number of EV: 140k (1% of the EVs as given in the C2035 scenario of the
  [NEP](https://www.netzentwicklungsplan.de/sites/default/files/paragraphs-files/NEP_2035_V2021_2_Entwurf_Teil1.pdf))
- The total numbers of EVs per RS7 region as well as the EV types distribution is derived from the municipalities' RS7
  type combined with data (01/2020) from
  [KBA](https://www.kba.de/DE/Statistik/Produktkatalog/produkte/Fahrzeuge/fz10/fz10_gentab.html)

Start the simulation using

    python main_simbev.py default_RS7

**Warning:** the simulation may take a while, depending on your machine's configuration consider to increase the number
of threads (max: 7).
