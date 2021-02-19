# webtests

This package holds the selenium tests for the autoreduction webapp.
## Running the Tests
From `WebApp/autoreduce_webapp` run `pytest WebApp/autoreduce_webapp/selenium_tests`

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
**Note:** Until these tests can be run with pytest-django and their open issue for xdist compatibility is fixed,
parallel execution is not avaible.
A configuration file has to be used to allow test settings to be shared across threads.

## Database Injection
To inject data for tests a fixture file must be created within `WebApp/autoreduce_webapp/autoreduce_webapp/fixtures`.
Fixture files contain models as json and are automatically added to a test database at test time.
To add a fixture to a test:
```python
class TestMyPage(BaseTestCase):
    fixtures = BaseTestCase.fixtures + ['my_fixture']
```
For more info on fixtures see the relevant [django documentation](https://docs.djangoproject.com/en/3.1/howto/initial-data/).