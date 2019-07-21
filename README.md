# almeremilieu
Almere Afvalkalender (garbage collection) sensor for Home Assistant

Results are retrieved from: https://www.almere.nl/wonen/afval/almere-afval-app-en-afvalkalender/

Add full directory (including 'almeremilieu') to your config/custom_components folder and add

sensor:
  - platform: almeremilieu
    postcode: 
    huisnummer: 
    toevoeging: 
    resources:
      - GREENGREY
      - PACKAGES
      - PAPER

to your configuration.yaml
