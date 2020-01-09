An HTTP backend for estimating linear spatial transformations from a list of point landmarks.

.. image:: https://img.shields.io/swagger/valid/3.0?label=OpenAPI&specUrl=https%3A%2F%2Fvoluba-linear-backend.apps.hbp.eu%2Fopenapi.json
   :alt: Swagger Validator

This backend is used by `Voluba <https://voluba.apps.hbp.eu/>`_, a web-based tool for interactive registration of 3-dimensional images, dedicated to the alignment of sub-volumes into brain templates.


Public deployments
==================

A production deployment (following the ``master`` branch) is deployed on https://voluba-linear-backend.apps.hbp.eu. |uptime-prod|

The ``dev`` branch is deployed on https://voluba-linear-backend.apps-dev.hbp.eu. |uptime-dev|

The public deployments are managed by OpenShift clusters, the relevant configuration is described in `<openshift-deployment/>`_.


Documentation
=============

The API is documented using the OpenAPI standard (a.k.a. Swagger): see `the ReDoc-generated documentation <https://voluba-linear-backend.apps.hbp.eu/redoc>`_. `A Swagger UI page <https://voluba-linear-backend.apps.hbp.eu/swagger-ui>`_ is also available for trying out the API.


Development
===========

Useful commands for development:

.. code-block:: shell

  git clone https://github.com/HumanBrainProject/voluba-linear-backend.git

  # Install in a virtual environment
  cd voluba-linear-backend
  python3 -m venv venv/
  . venv/bin/activate
  pip install -e .[dev]

  export FLASK_APP=linear_voluba
  flask run  # run a local development server

  # Tests
  pytest  # run tests
  pytest --cov=linear_voluba --cov-report=html  # detailed test coverage report
  tox  # run tests under all supported Python versions

  # Please install pre-commit if you intend to contribute
  pip install pre-commit
  pre-commit install  # install the pre-commit hook


Contributing
============

This repository uses `pre-commit`_ to ensure that all committed code follows minimal quality standards. Please install it and configure it to run as a pre-commit hook in your local repository (see above).


.. |uptime-prod| image:: https://img.shields.io/uptimerobot/ratio/7/m783970711-bbe034c363d690e3163c1b6c
   :alt: Weekly uptime ratio of the production instance
.. |uptime-dev| image:: https://img.shields.io/uptimerobot/ratio/7/m783970712-d728e3948939d25be7ccaa9a
   :alt: Weekly uptime ratio of the development instance
.. _pre-commit: https://pre-commit.com/
