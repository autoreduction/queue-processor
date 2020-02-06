---
name: Release issue template
about: Final checklist before a release
title: 'Release xx.x checklist'
labels: ''
assignees: ''

---

Before the next version of autoreduction can be released, the following must be checked:

#### Internals
* [ ] Release notes complete and checked
* [ ] Update version number


#### Smoke testing
* [ ] Ingestion code
* [ ] Queue Processor
* [ ] Autoreduction Processor
* [ ] Web application

#### Externals
* [ ] Wipe database

Once everything is complete, the release will be ready to deploy.
