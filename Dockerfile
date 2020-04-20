FROM golang:1.12 as compiler
RUN set -ex; \
    go get -u github.com/golang/dep/cmd/dep; \
    mkdir -p /go/src/github.com/anchore/test-infra

WORKDIR /go/src/github.com/anchore/test-infra

COPY src/ ./src
COPY Gopkg.lock .
COPY Gopkg.toml .

RUN set -ex; \
    dep ensure; \
    cd src/test/anchore-engine; \
    GOOS=linux GOARCH=amd64 go test -c .

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
    sudo curl -o /usr/local/bin/aws-iam-authenticator https://amazon-eks.s3-us-west-2.amazonaws.com/1.12.7/2019-03-27/bin/linux/amd64/aws-iam-authenticator; \
    sudo chmod +x /usr/local/bin/aws-iam-authenticator

# RUN set -ex; \
#     curl https://raw.githubusercontent.com/helm/helm/master/scripts/get | bash; \
#     sudo apt-get update && sudo apt-get install -y apt-transport-https; \
#     curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - ;\
#     echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list; \
#     sudo apt-get update; \
#     sudo apt-get install -y kubectl

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

COPY --from=compiler /go/src/github.com/anchore/test-infra/src/test/anchore-engine/anchore-engine.test /usr/local/bin/anchore-engine.test
COPY scripts/ci_utils.sh /usr/local/bin/ci_utils.sh

COPY scripts/run_make_command.sh /anchore-ci/run_make_command.sh
COPY scripts/lib/* /anchore-ci/lib/

USER circleci

WORKDIR /home/circleci