
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
from indico_payment_opencollective.util import validate_business

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

class PaypalPaymentPlugin(PaymentPluginMixin, IndicoPlugin):
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
        self.template_hook('event-manage-payment-plugin-before-form', self._get_encoding_warning)

    @property
    def logo_url(self):
        return url_for_plugin(self.name + '.static', filename='images/logo.png')

    def get_blueprints(self):
        return blueprint

    def adjust_payment_form_data(self, data):
        event = data['event']
        registration = data['registration']
        plain_name = str_to_ascii(remove_accents(registration.full_name))
        plain_title = str_to_ascii(remove_accents(event.title))
        data['item_name'] = f'{plain_name}: registration for {plain_title}'
        data['redirect_url'] = url_for_plugin('payment_opencollective.success', registration.locator.uuid, _external=True)
        data['cancel_url'] = url_for_plugin('payment_opencollective.cancel', registration.locator.uuid, _external=True)

    def _get_encoding_warning(self, plugin=None, event=None):
        if plugin == self:
            return render_plugin_template('event_settings_encoding_warning.html')