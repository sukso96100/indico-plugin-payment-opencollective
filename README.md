# indico-plugin-payment-opencollective

This plugin allows Open Collective to be used as payment method for paying registration fee on Indico. [Uses Open Collective's Post-Donation Redirect feature](https://docs.opencollective.com/help/contributing/development/post-donation-redirect) to handle payment. With this plugin, Usrs are redirected to specific event on collective on Open Collective then redirected back to Indico with transaction information from Open Collective.

## Installing

### For testing inside Indico development environment
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

### For production
TBD

