FROM circleci/python:3.6

USER root

ENV KIND_VERSION="v0.7.0"
ENV KUBECTL_VERSION="v1.15.0"
ENV HELM_VERSION="v3.1.1"

RUN set -ex; \
    groupadd docker; \
    usermod -aG docker circleci; \
    mkdir -p /anchore-ci/lib; \
    sudo apt-get update && sudo apt-get upgrade; \
    sudo pip install --upgrade pip; \
    sudo pip install --upgrade tox; \
    sudo pip install --upgrade awscli; \
    sudo pip install --upgrade anchorecli

RUN set -ex; \
    arch=$(uname | tr A-Z a-z); \
    echo "Installing KIND"; \
    curl -qsSLo "/usr/local/bin/kind" "https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VERSION}/kind-${arch}-amd64"; \
    chmod +x "/usr/local/bin/kind"; \
    echo "Installing Helm..."; \
    curl -sSL "https://get.helm.sh/helm-${HELM_VERSION}-${arch}-amd64.tar.gz" | tar xzf - -C /usr/local/bin --strip-components=1 "${arch}-amd64/helm"; \
    chmod +x "/usr/local/bin/helm"; \
    echo "Installing kubectl"; \
    curl -sSLo "/usr/local/bin/kubectl" "https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/${arch}/amd64/kubectl"; \
    chmod +x "/usr/local/bin/kubectl"

COPY scripts/run_make_command.sh /anchore-ci/run_make_command.sh
COPY scripts/lib/* /anchore-ci/lib/

USER circleci

WORKDIR /home/circleci