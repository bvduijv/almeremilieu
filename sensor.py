"""
Support for reading trash pickup data for Almere Milieu.

configuration.yaml

sensor:
  - platform: almeremilieu
    postcode: 
    huisnummer: 
    toevoeging: 
    resources:
      - GREENGREY
      - PACKAGES
      - PAPER
"""
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_RESOURCES, DEVICE_CLASS_TIMESTAMP)
from homeassistant.util import Throttle

import voluptuous as vol
from datetime import timedelta
from datetime import datetime

import requests
import json
import logging

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=12)

DEFAULT_NAME = 'Almere Milieu'
DEFAULT_COMPANY = '53d8db94-7945-42fd-9742-9bbc71dbe4c1'
DEFAULT_STARTDATE = datetime.today()
DEFUALT_ENDDATE = datetime.today() + timedelta(weeks=5)
CONST_POSTCODE = 'postcode'
CONST_HUISNUMMER = 'huisnummer'
CONST_TOEVOEGING = 'toevoeging'

# Predefined types and id's
TRASH_TYPES = {
    'GREENGREY': ['GFT', 'mdi:delete-empty'],
    'PACKAGES': ['Plastic en Verpakking', 'mdi:delete-empty'],
    'PAPER': ['Papier', 'mdi:delete-empty'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONST_POSTCODE): cv.string,
    vol.Optional(CONST_TOEVOEGING, default=''): cv.string,
    vol.Required(CONST_HUISNUMMER): cv.string,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(TRASH_TYPES)]),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Almere Milieu sensors."""
    postcode = config.get(CONST_POSTCODE)
    huisnummer = config.get(CONST_HUISNUMMER)
    toevoeging = config.get(CONST_TOEVOEGING)
    name = config.get(CONF_NAME)
    company = DEFAULT_COMPANY
    startdate = DEFAULT_STARTDATE
    enddate = DEFUALT_ENDDATE

    try:
        data = TrashData(postcode, huisnummer, toevoeging, company, startdate, enddate)
    except requests.exceptions.HTTPError as error:
        _LOGGER.error(error)
        return False

    entities = []
    for resource in config[CONF_RESOURCES]:
        trash_type = resource
        
        entities.append(TrashSensor(data, name, trash_type))
    add_entities(entities, True)

# pylint: disable=abstract-method
class TrashData(object):
    """Fetch data from 2go-mobile API."""

    def __init__(self, postcode, huisnummer, toevoeging, company, startdate, enddate):
        """Initialize."""
        self._postcode = postcode
        self._huisnummer = huisnummer
        self._toevoeging = toevoeging
        self._company = company
        self._enddate = enddate
        self._startdate = startdate
        self._addressid = None
        self.data = None

        """Get the adressID using the postcode, huisnummer, toevoeging and company."""
        try:
            json_data = requests.post("https://wasteapi.2go-mobile.com/api/FetchAdress", data = {
              "companyCode": self._company,
              "postCode": self._postcode,
              "houseNumber": self._huisnummer,
              "houseLetter": self._toevoeging
            }).json()
            _LOGGER.debug("Get Unique Adress ID = %s", json_data)
            self._addressid = json_data['dataList'][0]['UniqueId']
            _LOGGER.debug("Parsed addressid = %s", self._addressid)
        except requests.exceptions.RequestException:
            _LOGGER.error("Cannot fetch the addressid %s.", err.args)
            self.data = None
            return False

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the almeremilieu calendar data."""
        trashschedule = []
        try:
            json_data = requests.post("https://wasteapi.2go-mobile.com/api/GetCalendar", data = {
              "companyCode": self._company,
              "uniqueAddressID": self._addressid,
              "startDate": self._startdate,
              "endDate": self._enddate
            }).json()
            _LOGGER.debug("Get almeremilieu calendar data = %s", json_data)
        except requests.exceptions.RequestException:
            _LOGGER.error("Cannot fetch calendar data %s.", err.args)
            self.data = None
            return False

        """Parse the almeremilieu data."""
        try:
            for afval in json_data['dataList']:
               if len(afval['pickupDates']) != 0:
                  _LOGGER.debug(" Afval Type: %s Datum: %s", afval['_pickupTypeText'], afval['pickupDates'])
                  trash = {}
                  trash['title'] = afval['_pickupTypeText']
                  trash['date'] = min(afval['pickupDates'])
                  _LOGGER.debug(min(afval['pickupDates']))
                  trashschedule.append(trash)
            self.data = trashschedule
        except ValueError as err:
            _LOGGER.error("Cannot parse the data %s", err.args)
            self.data = None
            return False

class TrashSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, data, name, trash_type):
        """Initialize the sensor."""
        self.data = data
        self._trash_type = trash_type
        self._name = name + ' ' + TRASH_TYPES[self._trash_type][0]
        self._icon = TRASH_TYPES[self._trash_type][1]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon
    
    @property
    def device_class(self):
        """Return the class of this sensor."""
        return DEVICE_CLASS_TIMESTAMP

    def update(self):
        """Fetch new state data for the sensor."""
        self.data.update()
        _LOGGER.debug("Update = %s", self.data.data)

        for d in self.data.data:
           pickupdate = datetime.strptime(d['date'], '%Y-%m-%dT%H:%M:%S')
           if d['title'] == self._trash_type:
              self._state = pickupdate
