
from flask_pluginengine import render_plugin_template
from wtforms.fields import StringField, URLField, BooleanField
from wtforms.validators import DataRequired, Optional

from indico.core.plugins import IndicoPlugin, url_for_plugin
from indico.modules.events.payment import (PaymentEventSettingsFormBase, PaymentPluginMixin,
                                           PaymentPluginSettingsFormBase)
from indico.util.string import remove_accents, str_to_ascii
from indico.web.forms.validators import UsedIf

from indico_payment_opencollective import _
from indico_payment_opencollective.blueprint import blueprint

OC_BASEURL = "https://opencollective.com"
OC_STAGING_BASEURL = "https://staging.opencollective.com"

class PluginSettingsForm(PaymentPluginSettingsFormBase):
    collective_slug = StringField('Slug for Collective on Open Collective')
    event_slug = StringField('Slug for and Event under the Collective on Open Collective')
    api_key = StringField('Open Collective API Key (Personal token)')
    use_staging = BooleanField('Use Staging server of Open Collective')

class EventSettingsForm(PaymentEventSettingsFormBase):
    collective_slug = StringField('Slug for Collective on Open Collective')
    event_slug = StringField('Slug for and Event under the Collective on Open Collective')
    api_key = StringField('Open Collective API Key (Personal token)')
    use_staging = BooleanField('Use Staging server of Open Collective')

class OpenCollectivePaymentPlugin(PaymentPluginMixin, IndicoPlugin):
    """OpenCollective

    Provides a payment method using the OpenCollective Post donation redirect API.
    """
    configurable = True
    settings_form = PluginSettingsForm
    event_settings_form = EventSettingsForm
    default_settings = {
        'method_name': 'OpenCollective',
        'collective_slug': '',
        'event_slug': '',
        'api_key':'',
        'use_staging': False
        }
    default_event_settings = {
        'enabled': False,
        'method_name': None,
        'collective_slug': '',
        'event_slug': '',
        'api_key':'',
        'use_staging': False
        }

    def init(self):
        super().init()

    @property
    def logo_url(self):
        return url_for_plugin(self.name + '.static', filename='images/logo.png')

    def get_blueprints(self):
        return blueprint

    def adjust_payment_form_data(self, data):
        url = "{{event_settings.collective_slug}}{% if event_slug %}/events/{{event_slug}}{% endif %}/donate?interval=oneTime&amount=10"
        
        event = data['event']
        registration = data['registration']
        event_settings = data['event_settings']
        plain_name = str_to_ascii(remove_accents(registration.full_name))
        plain_title = str_to_ascii(remove_accents(event.title))
        redirect_url = url_for_plugin('payment_opencollective.callback', registration.locator.uuid, _external=True)
        data['item_name'] = f'{plain_name}: registration for {plain_title}'

        if event_settings['use_staging']:
            url = f"{OC_STAGING_BASEURL}/{event_settings['collective_slug']}"
        else:
            url = f"{OC_BASEURL}/{event_settings['collective_slug']}"

        if event_settings['event_slug']:
            url += f"/events/{event_settings['event_slug']}"

        url += f"/donate?interval=oneTime&amount={data['amount']}&redirect={redirect_url}"
        
        data['payment_url'] = url
        
