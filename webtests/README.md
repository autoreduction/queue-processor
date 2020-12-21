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
    ├── runner.py
    └── README.md

```
## Running the Tests
From the repository root simply run
`python -m webtests.runner`

To run against different deployments a url can be provided for example:  
` python -m webtests.runner --url https://example.com`

The tests may also be run with a headless browser by providing the headless flag `--headless`

An environment property may also be set with `-e <remote/local>` `--environment <local/remote>`. 
If this property is set to local tests decorated with `@local_only` will also be run. Theses tests
rely on inspecting settings that the WebApp is currently using e.g. `VALID_INSTRUMENTS` 


## Pages
The pages are built using the fluent page object model pattern. With common components being created
as mixins.

## Screenshots
If a test produces an error or fails, the webdriver will attempt to save a screenshot to the 
screenshot directory. If the tests are running within a github action worflow and an error or 
failure is produced, a ZIP of the screenshot folder for that run is downloadable as an artifact for
that run.

## Configuration
A configuration file has to be used to allow test settings to be shared across threads. An example 
configuration file is provided and can be copied from `config.json.example` to `config.json`.