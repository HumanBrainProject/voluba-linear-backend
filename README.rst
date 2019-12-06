An HTTP backend for estimating linear spatial transformations from a list of point landmarks.


Public deployments
==================

Coming soon

..
   A production deployment (following the ``master`` branch) is deployed on https://voluba-linear-backend.apps.hbp.eu. |uptime-prod|

   The ``dev`` branch is deployed on https://voluba-linear-backend.apps-dev.hbp.eu. |uptime-dev|

   The public deployments are managed by OpenShift clusters, the relevant configuration is described in `<openshift-deployment/>`_.


Documentation
=============

Coming soon


Development
===========

Useful commands for development:

.. code-block:: shell

  git clone https://github.com/FZJ-INM1-BDA/voluba-linear-backend.git

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


.. |uptime-prod| image:: https://img.shields.io/uptimerobot/ratio/7/FIXME
   :alt: Weekly uptime ratio of the production instance
.. |uptime-dev| image:: https://img.shields.io/uptimerobot/ratio/7/FIXME
   :alt: Weekly uptime ratio of the development instance
.. _pre-commit: https://pre-commit.com/
