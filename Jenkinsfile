pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
    }

    environment {
        BACKEND_IMAGE = 'shachafpardo/shelfsense-backend'
        FRONTEND_IMAGE = 'shachafpardo/shelfsense-frontend'
        HELM_RELEASE = 'shelfsense'
        HELM_CHART = 'kubernetes/helm-chart'
        KUBE_NAMESPACE = 'shelfsense'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Repository sanity') {
            steps {
                script {
                    env.BUILD_KIND = env.CHANGE_ID ? 'pull-request' : (env.BRANCH_NAME == 'main' ? 'main-release' : 'branch-validation')
                    echo "Build policy: ${env.BUILD_KIND}"
                }
                sh '''
                    set -eu
                    test -f requirements-dev.txt
                    test -f frontend/package-lock.json
                    test -f docker/backend/Dockerfile
                    test -f docker/frontend/Dockerfile
                    test -f kubernetes/helm-chart/Chart.yaml
                    git diff --check
                '''
            }
        }

        stage('Kubernetes reachability before Docker') {
            steps {
                sh '''#!/bin/sh
                    set +e
                    set +x

                    printf 'Process: pid=%s ppid=%s\n' "$$" "$PPID"
                    printf 'Identity: '
                    id || true
                    echo 'Cgroup:'
                    cat /proc/self/cgroup || true
                    printf 'Network namespace: '
                    readlink /proc/self/ns/net || true
                    printf 'Mount namespace: '
                    readlink /proc/self/ns/mnt || true
                    for executable in sh curl kubectl; do
                        printf 'Executable %s: ' "$executable"
                        command -v "$executable" || true
                    done
                    echo 'Route to 10.0.1.219:'
                    ip route get 10.0.1.219 || true
                    curl --insecure --silent \
                      --connect-timeout 5 --max-time 8 \
                      --output /dev/null \
                      --write-out 'Kubernetes reachability before Docker: HTTP status=%{http_code} remote IP=%{remote_ip} curl error=%{errormsg}\n' \
                      https://10.0.1.219:6443/version || true
                '''
            }
        }

        stage('Backend dependencies') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .ci-venv
                    .ci-venv/bin/python -m pip install --disable-pip-version-check -r requirements-dev.txt
                '''
            }
        }

        stage('Backend tests') {
            steps {
                sh '.ci-venv/bin/python -m pytest -q'
            }
        }

        stage('Frontend dependencies') {
            steps {
                dir('frontend') {
                    sh 'npm ci --no-audit --no-fund'
                }
            }
        }

        stage('Frontend typecheck') {
            steps {
                dir('frontend') {
                    sh 'npm run typecheck'
                }
            }
        }

        stage('Frontend production build') {
            steps {
                dir('frontend') {
                    sh 'npm run build'
                }
            }
        }

        stage('Docker build validation') {
            steps {
                script {
                    env.COMMIT_TAG = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
                sh '''
                    set -eu
                    docker build --tag "${BACKEND_IMAGE}:ci-${COMMIT_TAG}" --file docker/backend/Dockerfile .
                    docker build --tag "${FRONTEND_IMAGE}:ci-${COMMIT_TAG}" --file docker/frontend/Dockerfile .
                '''
            }
        }

        stage('Calculate release version') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([gitUsernamePassword(
                    credentialsId: 'github-credentials',
                    gitToolName: 'Default'
                )]) {
                    script {
                        env.RELEASE_VERSION = sh(
                            script: '''
                                set -eu
                                git fetch --force --tags origin

                                latest_tag="$(git tag --list 'v*' --sort=-v:refname | awk '/^v[0-9]+\\.[0-9]+\\.[0-9]+$/ { print; exit }')"
                                if [ -z "$latest_tag" ]; then
                                    release_version='1.0.0'
                                else
                                    version="${latest_tag#v}"
                                    major="${version%%.*}"
                                    remainder="${version#*.}"
                                    minor="${remainder%%.*}"
                                    patch="${remainder##*.}"
                                    release_version="${major}.${minor}.$((patch + 1))"
                                fi

                                intended_tag="v${release_version}"
                                if git show-ref --verify --quiet "refs/tags/${intended_tag}"; then
                                    echo "Release calculation failed: local tag ${intended_tag} already exists." >&2
                                    exit 1
                                fi

                                remote_tag_status=0
                                git ls-remote --exit-code --tags origin "refs/tags/${intended_tag}" > /dev/null 2>&1 || remote_tag_status=$?
                                case "$remote_tag_status" in
                                    0)
                                        echo "Release calculation failed: remote tag ${intended_tag} already exists." >&2
                                        exit 1
                                        ;;
                                    2)
                                        ;;
                                    *)
                                        echo "Release calculation failed: could not verify remote tag ${intended_tag}." >&2
                                        exit 1
                                        ;;
                                esac

                                printf '%s' "$release_version"
                            ''',
                            returnStdout: true
                        ).trim()
                        echo "Release version: ${env.RELEASE_VERSION}; immutable tag: ${env.COMMIT_TAG}"
                    }
                }
            }
        }

        stage('Push release images') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_PASSWORD'
                )]) {
                    sh '''
                        set +x
                        printf '%s' "$DOCKERHUB_PASSWORD" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
                        set -x
                        docker tag "${BACKEND_IMAGE}:ci-${COMMIT_TAG}" "${BACKEND_IMAGE}:${RELEASE_VERSION}"
                        docker tag "${BACKEND_IMAGE}:ci-${COMMIT_TAG}" "${BACKEND_IMAGE}:${COMMIT_TAG}"
                        docker tag "${FRONTEND_IMAGE}:ci-${COMMIT_TAG}" "${FRONTEND_IMAGE}:${RELEASE_VERSION}"
                        docker tag "${FRONTEND_IMAGE}:ci-${COMMIT_TAG}" "${FRONTEND_IMAGE}:${COMMIT_TAG}"
                        docker push "${BACKEND_IMAGE}:${RELEASE_VERSION}"
                        docker push "${BACKEND_IMAGE}:${COMMIT_TAG}"
                        docker push "${FRONTEND_IMAGE}:${RELEASE_VERSION}"
                        docker push "${FRONTEND_IMAGE}:${COMMIT_TAG}"
                    '''
                }
            }
        }

        stage('Kubernetes reachability after Docker') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    curl --insecure --silent \
                      --connect-timeout 5 --max-time 8 \
                      --output /dev/null \
                      --write-out 'Kubernetes reachability after Docker: HTTP status=%{http_code} remote IP=%{remote_ip} curl error=%{errormsg}\n' \
                      https://10.0.1.219:6443/version || true
                '''
            }
        }

        stage('Deploy with Helm') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    file(credentialsId: 'shelfsense-kubeconfig', variable: 'JENKINS_KUBECONFIG'),
                    string(credentialsId: 'shelfsense-db-password', variable: 'SHELFSENSE_DB_PASSWORD')
                ]) {
                    sh '''
                        set -eu
                        set +x
                        export KUBECONFIG="$JENKINS_KUBECONFIG"

                        api_server="$(kubectl config view --minify --output jsonpath='{.clusters[0].cluster.server}')"
                        if [ -z "$api_server" ]; then
                            echo 'Kubernetes preflight failed: kubeconfig has no API server URL.' >&2
                            exit 1
                        fi
                        printf 'Kubernetes API server: %s\n' "$api_server"

                        network_namespace="$(readlink /proc/self/ns/net 2>/dev/null || true)"
                        printf 'Network namespace: %s\n' "${network_namespace:-unavailable}"

                        if command -v ss > /dev/null 2>&1; then
                            if ss -H -ltn 'sport = :6443' 2>/dev/null | grep -q .; then
                                echo 'Port 6443 listener visible: yes'
                            else
                                echo 'Port 6443 listener visible: no'
                            fi
                        else
                            echo 'Port 6443 listener visible: unavailable (ss not installed)'
                        fi

                        api_http_status="$(curl -sk --connect-timeout 3 --max-time 5 \
                          --output /dev/null --write-out '%{http_code}' "${api_server%/}/version" || true)"
                        printf 'Kubernetes API /version diagnostic HTTP status: %s\n' "${api_http_status:-000}"

                        for proxy_name in HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy; do
                            if proxy_value="$(printenv "$proxy_name")"; then
                                sanitized_proxy="$(printf '%s' "$proxy_value" \
                                  | tr '\r\n' '  ' \
                                  | sed -E \
                                      -e 's#(https?://)[^/@[:space:]]+@#\1[REDACTED]@#g' \
                                      -e 's#[A-Za-z0-9+/_=.-]{32,}#[REDACTED]#g')"
                                printf '%s=%s\n' "$proxy_name" "$sanitized_proxy"
                            fi
                        done

                        kubectl_error_file="$(mktemp "${WORKSPACE}/.kubectl-preflight.XXXXXX")"
                        chmod 600 "$kubectl_error_file"
                        trap 'rm -f "$kubectl_error_file"' EXIT

                        attempt=1
                        max_attempts=9
                        while true; do
                            : > "$kubectl_error_file"
                            if kubectl --request-timeout=5s version > /dev/null 2> "$kubectl_error_file"; then
                                break
                            fi

                            printf 'kubectl error (attempt %s/%s):\n' "$attempt" "$max_attempts"
                            if [ -s "$kubectl_error_file" ]; then
                                sed -E \
                                  -e 's#(https?://)[^/@[:space:]]+@#\1[REDACTED]@#g' \
                                  -e 's#([Aa]uthorization:?[[:space:]]*)[^[:space:]].*#\1[REDACTED]#g' \
                                  -e 's#([Bb]earer[[:space:]]+)[A-Za-z0-9._~+/-]+#\1[REDACTED]#g' \
                                  -e 's#([Tt]oken[=:][[:space:]]*)[^[:space:]]+#\1[REDACTED]#g' \
                                  -e 's#[A-Za-z0-9+/_=.-]{32,}#[REDACTED]#g' \
                                  "$kubectl_error_file"
                            else
                                echo '(kubectl produced no stderr)'
                            fi

                            if [ "$attempt" -ge "$max_attempts" ]; then
                                echo 'Kubernetes preflight failed: API did not become ready within 90 seconds.' >&2
                                exit 1
                            fi
                            printf 'Kubernetes API not ready (attempt %s/%s); retrying in 5 seconds...\n' \
                              "$attempt" "$max_attempts"
                            attempt=$((attempt + 1))
                            sleep 5
                        done
                        rm -f "$kubectl_error_file"
                        trap - EXIT
                        printf 'Kubernetes API ready (attempt %s/%s).\n' "$attempt" "$max_attempts"

                        current_context="$(kubectl config current-context)"
                        context_namespace="$(kubectl config view --minify --output jsonpath='{..namespace}')"
                        if [ -z "$current_context" ] || [ "$context_namespace" != "$KUBE_NAMESPACE" ]; then
                            echo "Kubernetes preflight failed: current context must target namespace ${KUBE_NAMESPACE}." >&2
                            exit 1
                        fi

                        if ! kubectl --namespace "$KUBE_NAMESPACE" --request-timeout=5s get deployments > /dev/null; then
                            echo "Kubernetes preflight failed: credential cannot get deployments in ${KUBE_NAMESPACE}." >&2
                            exit 1
                        fi

                        can_update="$(kubectl auth can-i update deployments.apps --namespace "$KUBE_NAMESPACE")"
                        if [ "$can_update" != 'yes' ]; then
                            echo "Kubernetes preflight failed: credential cannot update deployments in ${KUBE_NAMESPACE}." >&2
                            exit 1
                        fi
                        echo 'Kubernetes namespace and deployment permissions verified.'

                        password_file="$(mktemp "${WORKSPACE}/.postgres-password.XXXXXX")"
                        chmod 600 "$password_file"
                        trap 'rm -f "$password_file"' EXIT
                        printf '%s' "$SHELFSENSE_DB_PASSWORD" > "$password_file"
                        test -s "$password_file"
                        set -x
                        helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
                          --namespace "$KUBE_NAMESPACE" \
                          --atomic --wait --wait-for-jobs --timeout 10m \
                          --set-string "backend.image.repository=${BACKEND_IMAGE}" \
                          --set-string "backend.image.tag=${RELEASE_VERSION}" \
                          --set-string "frontend.image.repository=${FRONTEND_IMAGE}" \
                          --set-string "frontend.image.tag=${RELEASE_VERSION}" \
                          --set-file database.auth.password="$password_file"
                    '''
                }
            }
        }

        stage('Rollout and smoke checks') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([file(credentialsId: 'shelfsense-kubeconfig', variable: 'JENKINS_KUBECONFIG')]) {
                    script {
                        try {
                            sh '''
                                set -eu
                                export KUBECONFIG="$JENKINS_KUBECONFIG"
                                kubectl --namespace "$KUBE_NAMESPACE" rollout status deployment/shelfsense-backend --timeout=5m
                                kubectl --namespace "$KUBE_NAMESPACE" rollout status deployment/shelfsense-frontend --timeout=5m
                                kubectl --namespace "$KUBE_NAMESPACE" rollout status statefulset/shelfsense-postgres --timeout=5m

                                backend_log="$(mktemp "${WORKSPACE}/.backend-port-forward.XXXXXX")"
                                frontend_log="$(mktemp "${WORKSPACE}/.frontend-port-forward.XXXXXX")"
                                kubectl --namespace "$KUBE_NAMESPACE" port-forward service/shelfsense-backend 18000:8000 > "$backend_log" 2>&1 &
                                backend_pid=$!
                                kubectl --namespace "$KUBE_NAMESPACE" port-forward service/shelfsense-frontend 18080:80 > "$frontend_log" 2>&1 &
                                frontend_pid=$!
                                cleanup() {
                                    kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
                                    wait "$backend_pid" "$frontend_pid" 2>/dev/null || true
                                    rm -f "$backend_log" "$frontend_log"
                                }
                                trap cleanup EXIT

                                attempt=1
                                until curl --fail --silent --show-error http://127.0.0.1:18000/ready > /dev/null && \
                                      curl --fail --silent --show-error http://127.0.0.1:18080/ > /dev/null; do
                                    if [ "$attempt" -ge 30 ]; then
                                        echo 'Application smoke tests did not become ready.' >&2
                                        exit 1
                                    fi
                                    attempt=$((attempt + 1))
                                    sleep 2
                                done
                            '''
                        } catch (err) {
                            echo 'Post-deploy validation failed; rolling back with Helm before failing the build.'
                            sh '''
                                set -eu
                                export KUBECONFIG="$JENKINS_KUBECONFIG"
                                helm rollback "$HELM_RELEASE" 0 --namespace "$KUBE_NAMESPACE" --wait --timeout 10m
                            '''
                            throw err
                        }
                    }
                }
            }
        }

        stage('Create Git release tag') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([gitUsernamePassword(
                    credentialsId: 'github-credentials',
                    gitToolName: 'Default'
                )]) {
                    sh '''
                        set -eu
                        git tag -a "v${RELEASE_VERSION}" -m "Release v${RELEASE_VERSION}"
                        git push origin "v${RELEASE_VERSION}"
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                set +e
                set +x
                docker logout >/dev/null 2>&1
                rm -f "${WORKSPACE}"/.postgres-password.* \
                      "${WORKSPACE}"/.backend-port-forward.* \
                      "${WORKSPACE}"/.frontend-port-forward.*
                docker image rm \
                  "${BACKEND_IMAGE}:ci-${COMMIT_TAG:-unknown}" \
                  "${FRONTEND_IMAGE}:ci-${COMMIT_TAG:-unknown}" \
                  "${BACKEND_IMAGE}:${RELEASE_VERSION:-unknown}" \
                  "${BACKEND_IMAGE}:${COMMIT_TAG:-unknown}" \
                  "${FRONTEND_IMAGE}:${RELEASE_VERSION:-unknown}" \
                  "${FRONTEND_IMAGE}:${COMMIT_TAG:-unknown}" >/dev/null 2>&1 || true
            '''
            deleteDir()
        }
    }
}
