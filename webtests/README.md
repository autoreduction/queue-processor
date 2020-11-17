#webtests

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
    │   └── help_page.py.py
    ├── screenshots
    │   └── .keep  
    ├── tests
    │   ├── base_tests.py
    │   ├── test_overiew_page.py
    │   ├── test_help_page.py
    │   └── test_instrument_summary_page.py
    ├── config.ini
    ├── configuration.py
    ├── driver.py    
    ├── runner.py
    └── README.md

```
## Running the Tests
From the repository root simply run
`python -m webtests.runner`

##Pages
The pages are built using the fluent page object model pattern. With common components being created
as mixins.