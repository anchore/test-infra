# Create kubernetes testing cluster on AWS

Functional testing is performed on an EKS cluster running on the Anchore-Testing AWS account.

The following software must be installed on your system.
* awscli
* eksctl
* helm
* kubectl

Setup awscli profiles for accessing the Anchore-Testing AWS account using role-switching.

### Create & setup cluster for testing

1. Create the EKS cluster
    ```bash
    eksctl create cluster -f cluster.yaml --profile testing`
    ```

2. Connect to cluster using kubectl
    ```bash
    aws eks --region us-west-2 update-kubeconfig --name anchore-ci --profile testing`
    ```

3. Install tiller to cluster
    ```bash
    helm init

    kubectl create serviceaccount --namespace kube-system tiller

    kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller

    kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'

    helm init --service-account tiller --upgrade
    ```

4. Copy demo enterprise license & readonly dockerhub account creds to cluster.
    ```bash
    kubectl create secret generic anchore-enterprise-license --from-file=license.yaml=license.yaml -n default

    kubectl create secret docker-registry anchore-enterprise-pullcreds --docker-server=docker.io --docker-username=anchoreci --docker-password=xxxxxxxxxxxxxxx --docker-email=anchoreci@anchore.com -n default
    ```

5. Add pullcreds to default service account.
    ```bash
    k patch serviceaccount default -p '{"imagePullSecrets":[{"name": "anchore-enterprise-pullcreds"}]}' --type=merge
    ```

6. Create EKS cluster autoscaler. Replace `<EKS_CLUSTER_AUTOSCALING_GROUP_NAME>` in cluster-autoscaler.yml with the name of the eks node autoscaling group created by eksctl. Then apply config to the cluster.
    ```bash
    CLUSTER_NAME=$(aws autoscaling describe-auto-scaling-groups --query "AutoScalingGroups[? Tags[? (Key=='alpha.eksctl.io/cluster-name') && Value=='anchore-ci']]".AutoScalingGroupName --profile testing --output text)

    sed -i 's/<EKS_CLUSTER_AUTOSCALING_GROUP_NAME>/${CLUSTER_NAME}/' cluster-autoscaler.yml

    kubectl apply -f cluster-autoscaler.yml
    ```