FROM quay.io/operator-framework/opm:latest

COPY catalog/index.yaml /configs/index.yaml

ENTRYPOINT ["/bin/opm"]
CMD ["serve", "/configs"]
