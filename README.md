# almeremilieu
Almere Afvalkalender (garbage collection) sensor for Home Assistant

Results are retrieved from: https://www.almere.nl/wonen/afval/almere-afval-app-en-afvalkalender/

Add full directory (including 'almeremilieu') to your config/custom_components folder and add

```
sensor:
  - platform: almeremilieu
    postcode: 
    huisnummer: 
    toevoeging: 
    resources:
      - GREENGREY
      - PACKAGES
      - PAPER
```

to your configuration.yaml

Add the followin to your lovelace configuration:

```
  - type: entities
    title: Almere Afvalkalender
    entities:
      - sensor.almere_milieu_gft
      - sensor.almere_milieu_papier
      - sensor.almere_milieu_plastic_en_verpakking
    show_header_toggle: false
```

Screenshot

![alt text](https://raw.githubusercontent.com/bvduijv/almeremilieu/master/almeremilieu-lovelace%20screenshot.png)
