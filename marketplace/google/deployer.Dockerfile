FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild:latest

# Google Cloud Marketplace requires the deployer image to include schema.yaml
# at /data/schema.yaml. The onbuild base image copies package files into /data.
COPY schema.yaml /data/schema.yaml
COPY deploy.sh /data/deploy.sh
COPY templates /data/templates
