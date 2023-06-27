from datetime import timedelta
from datetime import datetime
import logging
import lxml.html as lh
import re
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
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
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from .const import (
    DOMAIN,
    SENSOR_PLATFORM,
)

REQUIREMENTS = [ ]

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by nemzetiutdij.hu"
CONF_COUNTRY = 'country'
CONF_DELAY = 'delay'
CONF_PLATENUMBER = 'plateNumber'

DEFAULT_COUNTRY = 'H'
DEFAULT_DELAY = 0
DEFAULT_ICON = 'mdi:highway'
DEFAULT_NAME = 'EMatrica HU'

HTTP_TIMEOUT = 5 # secs
SCAN_INTERVAL = timedelta(hours=3)
URL = 'https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): cv.string,
    vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): cv.string,
    vol.Required(CONF_PLATENUMBER): cv.string,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    country = config.get(CONF_COUNTRY)
    delay = config.get(CONF_DELAY)
    platenumber = config.get(CONF_PLATENUMBER)

    async_add_devices(
        [EMatricaHUSensor(hass, country, platenumber, delay)],update_before_add=True)

class EMatricaHUSensor(Entity):

    def __init__(self, hass, country, platenumber, delay):
        """Initialize the sensor."""
        self._hass = hass
        self._country = country
        self._platenumber = platenumber
        self._name = platenumber.lower()
        self._state = None
        self._delay = int(re.findall('\d+',delay)[0])
        self._prevematrica = []
        self._ematrica = []
        self._icon = DEFAULT_ICON
        self._failure = False
        self._attr = {}

    @property
    def extra_state_attributes(self):

        if not self._failure:
            self._attr["nrOfStickers"] = len(self._ematrica)
            self._attr["stickers"] = self._ematrica
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

    async def async_update(self):
        earliest = 400
        _LOGGER.debug("Starting update on " + self._platenumber)
        self._prevematrica = self._ematrica
        self._ematrica = await self._hass.async_add_executor_job(self.async_get_ematrica)
        if len(self._ematrica) == 0:
            self._ematrica = self._prevematrica

        if len(self._ematrica) > 0:
            for item in self._ematrica:
                val = item.get('expiresIn')
                if int(val) < earliest:
                    earliest = int(val)

        _LOGGER.debug("Finishing update on " + self._platenumber)
        self._state = earliest
        return self._state

    def async_get_ematrica(self):
        json_data = {}
        mjson = []
        sp_elements = []
        lines = ""

        time.sleep(self._delay)
        _LOGGER.debug("Getting data on " + self._platenumber)

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
            driver.implicitly_wait(5)
        except WebDriverException:
            self._failure = True
            _LOGGER.debug("Could not connect to " + URL + " for sticker data on " + self._platenumber)

        if not self._failure:
            # cookie policy
            try:
                button1 = driver.find_element(By.CLASS_NAME, "orange--text")
                button1.click()
            except NoSuchElementException:
                _LOGGER.debug("Could not found cookie button... ignoring")

        if not self._failure:
            # countryCode
            try:
                cc = driver.find_element('id', 'VehicleNewForm--countryCode')
                driver.implicitly_wait(5)
                cc.send_keys(self._country)
                cc.send_keys(Keys.DOWN)
                cc.send_keys(Keys.ENTER)
            except NoSuchElementException:
                self._failure = True
                _LOGGER.debug("Could not found countryCode element for " + self._platenumber)
            else:
                _LOGGER.debug("countryCode set " + cc.get_attribute('value'))

        if not self._failure:
            # plateNumber
            try:
                pn = driver.find_element('id', 'VehicleNewForm--plateNumber')
                pn.send_keys(self._platenumber)
            except NoSuchElementException:
                self._failure = True
                _LOGGER.debug("Could not found plateNumber element for " + self._platenumber)
            else:
                _LOGGER.debug("plateNumber set " + pn.get_attribute('value'))

        if not self._failure:
            try:
                button = driver.find_element('id', "VehicleNewForm--saveButton")
                driver.implicitly_wait(5)
                ActionChains(driver).move_to_element(button).click(button).perform()

                time.sleep(5)

                lines = driver.page_source.replace("\r","").split('\n')
            except NoSuchElementException:
                self._failure = True
                _LOGGER.debug("Could not found submit button for " + self._platenumber)
            else:
                _LOGGER.debug("button pressed for " + self._platenumber)

        if not driver.service.process:
            _LOGGER.debug("webdriver quit unexpectedly")
        if driver.service.process:
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
