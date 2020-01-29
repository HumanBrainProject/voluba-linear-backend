The production configuration has been exported to `openshift-prod-export.yaml` using ``oc get -o yaml --export is,bc,dc,svc,route,pvc,cm`` (`status` information was manually stripped).

Deploying on an OpenShift cluster
=================================

#. Create the project named `voluba-linear-backend` on https://okd.hbp.eu/
#. Log in to https://okd.hbp.eu/ using the command-line ``oc`` tool, switch to the `voluba-linear-backend` project with ``oc project voluba-linear-backend``
#. Import the objects from your edited YAML file using ``oc create -f openshift-prod-export.yaml``
#. Re-create the Persistent Volume Claims (none for this project).
#. Create the needed Config Maps and Secrets (none for this project).
#. Start the build. The deployment should follow automatically.
#. Go to `Builds` -> `Builds` -> `voluba-linear-backend` -> `Configuration`, copy the GitHub Webhook URL and configure it into the GitHub repository (https://github.com/HumanBrainProject/voluba-linear-backend/settings/hooks). Make sure to set the Content Type to ``application/json``.
