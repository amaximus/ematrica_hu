import asyncio

from datetime import timedelta
from datetime import datetime
#import json
import logging
import lxml.html as lh
#import re
import voluptuous as vol
#import aiohttp

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
#from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform

import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

from .const import (
    DOMAIN,
    SENSOR_PLATFORM,
)

REQUIREMENTS = [ ]

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by nemzetiutdij.hu"
CONF_COUNTRY = 'country'
CONF_PLATENR = 'platenr'

DEFAULT_NAME = 'EMatrica HU'
DEFAULT_ICON = 'mdi:highway'

HTTP_TIMEOUT = 5 # secs
SCAN_INTERVAL = timedelta(hours=12)
URL = 'https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_COUNTRY): cv.string,
    vol.Required(CONF_PLATENR): cv.string,
})

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    country = config.get(CONF_COUNTRY)
    platenr = config.get(CONF_PLATENR)

    async_add_devices(
        [EMatricaHUSensor(hass, country, platenr)],update_before_add=True)

class EMatricaHUSensor(Entity):

    def __init__(self, hass, country, platenr):
        """Initialize the sensor."""
        self._hass = hass
        self._country = country
        self._platenr = platenr
        self._name = platenr.lower()
        self._state = None
        self._ematrica = []
        self._icon = DEFAULT_ICON
        #self._session = async_get_clientsession(self._hass)
        self._attr = {}

    @property
    def extra_state_attributes(self):

        self._attr["ematrica"] = self._ematrica
        self._attr["nrOfStickers"] = len(self._ematrica)
        self._attr["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        self._attr["provider"] = CONF_ATTRIBUTION
        return self._attr

    def __repr__(self):
        """Return main sensor parameters."""
        return (
            f"EMatricaHU[ name: {self._name}, "
            f"entity_id: {self.entity_id}, "
            f"state: {self.state}\n"
            f"config: {self.config}]"
        )

    @asyncio.coroutine
    async def async_update(self):
        earliest = 400
        self._ematrica = await self._hass.async_add_executor_job(self.async_get_ematrica)

        if len(self._ematrica) > 0:
            for item in self._ematrica:
                val = item.get('expiresIn')
                if int(val) < earliest:
                    earliest = int(val)

        self._state = earliest
        return self._state

    def async_get_ematrica(self):
        json_data = {}
        mjson = []
        sp_elements = []
        lines = ""

        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--single-process')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        options.add_argument('--log-level=2')
        try:
            driver = webdriver.Chrome(desired_capabilities=capa,options=options)
            driver.get(URL);
            time.sleep(5)
        except WebDriverException:
            _LOGGER.debug("Could not connect to " + URL)

        # cookie policy
        try:
            button1 = driver.find_element(By.CLASS_NAME, "orange--text")
            button1.click()
        except NoSuchElementException:
            _LOGGER.debug("Could not found cookie button")

        # countryCode
        try:
            cc = driver.find_element('id', 'VehicleNewForm--countryCode')
            cc.send_keys(self._country)
            cc.send_keys(Keys.DOWN)
            cc.send_keys(Keys.ENTER)
        except NoSuchElementException:
            _LOGGER.debug("Could not found countryCode element")

        # plateNumber
        try:
            pn = driver.find_element('id', 'VehicleNewForm--plateNumber')
            pn.send_keys(self._platenr)
        except NoSuchElementException:
            _LOGGER.debug("Could not found plateNumber element")

        try:
            button = driver.find_element('id', "VehicleNewForm--saveButton")
            driver.implicitly_wait(10)
            ActionChains(driver).move_to_element(button).click(button).perform()

            time.sleep(5)

            lines = driver.page_source.replace("\r","").split('\n')
        except NoSuchElementException:
            _LOGGER.debug("Could not found submit button")

        driver.quit()

        matched_lines = [line for line in lines if '<span data-v-83d5f0d4="">' in line]
        if len(matched_lines) > 0:
            doc = lh.fromstring(matched_lines[0])
            sp_elements = doc.xpath('//span/text()')
            _LOGGER.debug("nr of stickers: " + str(int(len(sp_elements)/6)))

            dt = datetime.today()

            for i in range(0, int(len(sp_elements)/6)):
                ds = datetime.strptime(sp_elements[i*6 + 5].split(',')[0],"%Y. %m. %d.")
                _LOGGER.debug(str(sp_elements[i*6 + 0]) + ": " + str(sp_elements[i*6 + 5]))
                days = (ds - dt).days + 1
                json_data={ "sticker": sp_elements[i*6], \
                            "expiresAt": sp_elements[i*6 + 5], \
                            "expiresIn": days }
                mjson.append(json_data)

        return mjson

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return DEFAULT_ICON
