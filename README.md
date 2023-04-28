[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

<p><a href="https://www.buymeacoffee.com/6rF5cQl" rel="nofollow" target="_blank"><img src="https://camo.githubusercontent.com/c070316e7fb193354999ef4c93df4bd8e21522fa/68747470733a2f2f696d672e736869656c64732e696f2f7374617469632f76312e7376673f6c6162656c3d4275792532306d6525323061253230636f66666565266d6573736167653d25463025394625413525413826636f6c6f723d626c61636b266c6f676f3d6275792532306d6525323061253230636f66666565266c6f676f436f6c6f723d7768697465266c6162656c436f6c6f723d366634653337" alt="Buy me a coffee" data-canonical-src="https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&amp;message=%F0%9F%A5%A8&amp;color=black&amp;logo=buy%20me%20a%20coffee&amp;logoColor=white&amp;labelColor=b0c4de" style="max-width:100%;"></a></p>

# Hungarian highway sticker information for Home Assistant

This custom component gets Hungarian highway sticker information for your car from
[https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes](https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes)

#### Prerequisites

This has been developed for Raspbian/Debian OS, however if the needed OS packages are available for your
OS, most probably it will work on that OS as well.

OS packages needed for this component to work are `chromium-browser` and `chromium-chromedriver`.

Python module `selenium` is also required. It is specified as requirement in the manifest file,
but if it doesn't get installed automatically, install it manually.

#### Installation

The easiest way to install it is through [HACS (Home Assistant Community Store)](https://github.com/hacs/integration),
search for <i>Highway Sticker Information Hungary</i> in the Integrations.<br />

#### General

The entity created will be named based on the specified plate number e.g. `sensor.abc123` (see example configuration below)

The state of the sensor will be the number of days till the first highway sticker expires.

The sensor will also report in attributes all your valid highway stickers:

![State and attributes for a sensor](https://raw.githubusercontent.com/amaximus/ematrica_hu/main/ematrica1.png)

#### Configuration:
Define sensor with the following configuration parameters:<br />

---
| Name | Optional | `Default` | Version | Description |
| :---- | :---- | :------- | :----------- | :-----------|
| country | **N** | `` | 0.0.1 | name of the sensor |
| platenr | **N** | `` | 0.0.1 | plate number |
---

Country code and plate number should be in format accepted by
[https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes](https://nemzetiutdij.hu/hu/e-matrica/matrica-lekerdezes), namely:
* country code in fact accepts a pattern for which the top selection should be made
* platenumber is usually in form of capital letters and numbers without spaces, dashes, etc.

#### Example
```
platform: ematrica_hu
country: 'H'
platenr: 'ABC123'
```

## Thanks

Thanks to all the people who have contributed!

[![contributors](https://contributors-img.web.app/image?repo=amaximus/ematrica_hu)](https://github.com/amaximus/ematrica_hu/graphs/contributors)
