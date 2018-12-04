## settings

The client settings class holds credentials used to access a service. The following are required by the `__init__`:
* `username`
* `password`
* `host`
* `port`

`ClientSettings` is a generic class and most services require additional information. The `ClientSettingsFactory`
provides a way to create bespoke `ClientSettings` for different services. These will have additional variables such
as (in the example of `ICATClient`) the authentication type must also be stored.

Currently the supported `settings_type` are `database`,`icat` and `queue`.

To create a `ClientSettings` class using the factory:
```
from utils.clients.settings.client_settings_factory import ClientSettingsFactory

ICAT_SETTINGS = SETTINGS_FACTORY.create(settings_type='icat',
                                        username='USERNAME',
                                        password='PASSWORD',
                                        host='HOST',
                                        port='PORT',
                                        authentication_type='Simple')
```

*`utils.test_settings` has examples of this.*
