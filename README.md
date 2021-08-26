[![Build Status](https://github.com/ISISScientificComputing/autoreduce/workflows/Tests/badge.svg?branch=master)](https://github.com/ISISScientificComputing/autoreduce/actions?query=workflow%3ATests+branch%3Amaster)
[![codecov](https://codecov.io/gh/ISISScientificComputing/autoreduce/branch/master/graph/badge.svg?token=ZJ1C5VE5WN)](https://codecov.io/gh/ISISScientificComputing/autoreduce)


# Autoreduction service description
A service for automated batch processing of jobs specifically design for use at [ISIS Neutron and Muon Facility](https://www.isis.stfc.ac.uk). For further documentation see also [Wiki](https://github.com/ISISScientificComputing/autoreduce/wiki). 

In one (not complete) picture the Autoreduction service is:

![Example Table](documentation/assets/main_components/Autoreduction_main_components.png)

This repository contains only the backend service code, also named the `queue processor` service. Repositories for the rest of the microservices can be found in the [GitHub organisation page](https://github.com/ISISScientificComputing)
