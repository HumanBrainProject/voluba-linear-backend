Deploying to production
=======================

As an example, these are the instructions for restoring the production deployment on https://okd.hbp.eu/.

#. You can use the deployment configuration saved in `<openshift-prod-export.yaml>`_ provided in the repository as a starting point. Edit the route contained in this file to use the correct URL.
#. Create the project named `voluba-linear-backend` on https://okd.hbp.eu/
#. Log in using the command-line ``oc`` tool (https://okd.hbp.eu/console/command-line), switch to the `voluba-linear-backend` project with ``oc project voluba-linear-backend``
#. Import the objects from your edited YAML file using ``oc create -f openshift-prod-export.yaml``
#. Re-create the Persistent Volume Claims and upload the data (none for this project).
#. Edit the Config Maps if needed, re-create the needed Secrets (none for this project).
#. Start the build. The deployment should follow automatically.
#. For production, increase the number of replicas in order to be more resilient to node failures: go to `Applications` -> `Deployments` -> `flask` -> `Configuration` and change the number of `Replicas` to 3.
#. Go to `Builds` -> `Builds` -> `flask` -> `Configuration`, copy the GitHub Webhook URL and configure it into the GitHub repository (https://github.com/HumanBrainProject/voluba-linear-backend/settings/hooks). Make sure to set the Content Type to ``application/json``.

The deployment configuration is saved to `<openshift-prod-export.yaml>`_ by running ``oc get -o yaml --export is,bc,dc,svc,route,pvc,cm,horizontalpodautoscaler > openshift-prod-export.yaml`` (`status` information is stripped manually, see https://collab.humanbrainproject.eu/#/collab/38996/nav/270508 for other edits that may be necessary).
