# indico-plugin-payment-opencollective

[![PyPI - Version](https://img.shields.io/pypi/v/indico-plugin-payment-opencollective)](https://pypi.org/project/indico-plugin-payment-opencollective/) [![CI](https://github.com/sukso96100/indico-plugin-payment-opencollective/actions/workflows/ci.yml/badge.svg)](https://github.com/sukso96100/indico-plugin-payment-opencollective/actions/workflows/ci.yml) [![CD](https://github.com/sukso96100/indico-plugin-payment-opencollective/actions/workflows/cd.yml/badge.svg)](https://github.com/sukso96100/indico-plugin-payment-opencollective/actions/workflows/cd.yml)


This plugin allows Open Collective to be used as payment method for paying registration fee on Indico. [Uses Open Collective's Post-Donation Redirect feature](https://docs.opencollective.com/help/contributing/development/post-donation-redirect) to handle payment. With this plugin, Usrs are redirected to specific event on collective on Open Collective then redirected back to Indico with transaction information from Open Collective.

[**See how it works with short demo video**](https://youtu.be/FnMXnVP1xwA)

## Installation

Install the plugin [package](https://pypi.org/project/indico-plugin-payment-opencollective/) from PyPI
```bash
pip install indico-plugin-payment-opencollective
```

Open `indico.conf` of your indico installation then add `payment_opencollective` on `PLUGIN`.
```python
PLUGINS = { ... , 'payment_opencollective'}
```

## Install for development for contributing to this plugin

Clone this repository on `~/dev/indico/plugins`
```bash
git clone https://github.com/ubucon-asia/indico-plugin-payment-opencollective.git
```

With python virtual environment of Indico development installation enabled, enter the cloned directory then run following command to install the plugin.
```bash
pip install -e .
```

Open `indico.conf` which should be located in `~/dev/indico/src/indico` then add `payment_opencollective` on `PLUGIN`.
```python
PLUGINS = { ... , 'payment_opencollective'}
```

You can now test you modification on your development indico environment.

## Configuration
On your Indico event item admin page, Go to `Features` then enable `Payment` feature.

Once done, Go to `Payments` then under `Payment methods` section, Click `Open Collective` and enable. Enter and save configurations. 
Once you also configured pricing for each registration form, then you're ready to accept payments with Open Collective.

- Collective Slug: Slug of your collective on Open Collective. (e.g. If it's `https://opencollective.com/ubucon-asia` then enter `ubucon-asia`)
- Event Slug: If you have created event under your collective, enter slug of the event on Open Collective. (e.g. If it's `https://opencollective.com/ubucon-asia/events/ubucon-asia-2024-d62e355c` then enter `ubucon-asia-2024-d62e355c`)
- Token: Used for querying order data from Open Collective. Go to your personal settings on Open Collective and navigate to the `For developers` section to craete yours

Pricing of each registration can be configured on `General settings` of each regiatraion settings. Make sure to match currency of registration form with the collective integrated so that people won't get confused on checkout.  
