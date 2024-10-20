
from indico.core.plugins import IndicoPlugin, url_for_plugin
from indico.modules.events.payment import (PaymentEventSettingsFormBase,
                                           PaymentPluginMixin,
                                           PaymentPluginSettingsFormBase)
from indico.util.string import remove_accents, str_to_ascii
from wtforms.fields import BooleanField, StringField
from wtforms.validators import DataRequired, Optional

from indico_payment_opencollective import _
from indico_payment_opencollective.blueprint import blueprint
from indico_payment_opencollective.constants import (OC_BASEURL,
                                                     OC_STAGING_BASEURL)


class PluginSettingsForm(PaymentPluginSettingsFormBase):
    collective_slug = StringField(_('Collective Slug'), [Optional()], description=_('Slug for Collective on Open Collective'))
    event_slug = StringField(_('Event Slug'), [Optional()], description=_('Slug for and Event under the Collective on Open Collective'))
    token = StringField(_('Token'), [Optional()], description=_('Open Collective Token (Personal token - To create one, go to your personal settings on Open Collective and navigate to the For developers section.)'))
    use_staging = BooleanField(_('Use Staging'), [Optional()], description=_('Use Staging server of Open Collective. Plugin might not fully functional with staging server'))

class EventSettingsForm(PaymentEventSettingsFormBase):
    collective_slug = StringField(_('Collective Slug'), [DataRequired()], description=_('Slug for Collective on Open Collective'))
    event_slug = StringField(_('Event Slug'), [Optional()], description=_('Slug for and Event under the Collective on Open Collective'))
    token = StringField(_('Token'), [DataRequired()], description=_('Open Collective Token (Personal token - To create one, go to your personal settings on Open Collective and navigate to the For developers section.)'))
    use_staging = BooleanField(_('Use Staging'), [Optional()], description=_('Use Staging server of Open Collective. Plugin might not fully functional with staging server'))

class OpenCollectivePaymentPlugin(PaymentPluginMixin, IndicoPlugin):
    """Open Collective

    Provides a payment method using the OpenCollective Post donation redirect API.
    """
    configurable = True
    settings_form = PluginSettingsForm
    event_settings_form = EventSettingsForm
    default_settings = {
        'method_name': 'Open Collective',
        'collective_slug': '',
        'event_slug': '',
        'token':'',
        'use_staging': False
        }
    default_event_settings = {
        'enabled': False,
        'method_name': None,
        'collective_slug': '',
        'event_slug': '',
        'token':'',
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
        event = data['event']
        registration = data['registration']
        event_settings = data['event_settings']
        plain_name = str_to_ascii(remove_accents(registration.full_name))
        plain_title = str_to_ascii(remove_accents(event.title))
        redirect_url = url_for_plugin('payment_opencollective.callback', registration.locator.uuid, _external=True)
        data['item_name'] = f'{plain_name}: registration for {plain_title}'

        if event_settings['use_staging']:
            url = f"{OC_STAGING_BASEURL}"
        else:
            url = f"{OC_BASEURL}"

        if event_settings['event_slug']:
            url += f"/{event_settings['event_slug']}"
        else:
            url += f"/{event_settings['collective_slug']}"

        url += f"/donate/{int(data['amount'])}/indico_registration_fee_payment?redirect={redirect_url}"
        
        data['payment_url'] = url
        
