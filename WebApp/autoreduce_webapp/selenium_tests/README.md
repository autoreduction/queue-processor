# webtests

This package holds the selenium tests for the autoreduction webapp. It has the following structure:

```
─── webtests
    ├── pages
    │   ├── component_mixins
    │   │   ├── footer.py
    │   │   ├── navbar.py
    │   │   └── tour.py
    │   ├── page.py
    │   ├── overview_page.py
    │   ├── instrument_summary_page.py
    │   └── help_page.py
    ├── screenshots
    │   └── .keep  
    ├── tests
    │   ├── base_tests.py
    │   ├── test_overiew_page.py
    │   ├── test_help_page.py
    │   └── test_instrument_summary_page.py
    ├── config.json
    ├── configuration.py
    ├── driver.py    
    └── README.md

```
## Running the Tests
From `WebApp/autoreduce_webapp` run `python manage.py test selenium_tests`


## Pages
The pages are built using the fluent page object model pattern. With common components being created
as mixins.

### Login Workaround
Due to there being no real login mechanism being enabled for local deployments (Such as
within the selenium test action) There is currently a workaround on each launch method.
This is the reason why the base url is navigated to first, to simulate logging in as 
seen below:  
```python
self.driver.get(configuration.get_url())
self.driver.get(OverviewPage.url())
```

## Screenshots
If a test produces an error or fails, the webdriver will attempt to save a screenshot to the 
screenshot directory. If the tests are running within a github action workflow and an error or 
failure is produced, a ZIP of the screenshot folder for that run is downloadable as an artifact for
that run.

## Configuration
**Note:** Until these tests can be run with pytest-django. Parallel execution is not avaible.    
A configuration file has to be used to allow test settings to be shared across threads. An example 
configuration file is provided and can be copied from `config.json.example` to `config.json`.

## Database Injection
To inject data for tests a fixture file must be created within `WebApp/autoreduce_webapp/autoreduce_webapp/fixtures`.
Fixture files contain models as json and are automatically added to a test database at test time.  
To add a fixture to a test:  
```python
class TestMyPage(BaseTestCase):
    fixtures = BaseTestCase.fixtures + ['my_fixture']
```
For more info on fixtures see the relevant [django documentation](https://docs.djangoproject.com/en/3.1/howto/initial-data/).