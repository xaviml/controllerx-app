#!/usr/bin/env bash
# ==============================================================================
# Deploys the app to a Home Assistant host as a local app, to test changes
# before releasing them. Users never see it: a local app only exists on the
# host it's copied to.
#
#   HA_HOST=<user>@<host> scripts/deploy-local.sh [<ControllerX checkout>]
#
# It shows up as "ControllerX (local)" (slug local_controllerx) and is built
# on the host from the Dockerfile, so no image is pushed. Given a ControllerX
# checkout, its apps/controllerx replaces the bundled release, to test
# unreleased ControllerX code.
#
# Needs SSH access to the host with a user that can run sudo and the ha CLI,
# like the one of the "Advanced SSH & Web Terminal" app.
# ==============================================================================
set -euo pipefail

readonly APP_DIR="controllerx"
readonly REMOTE_DIR="/addons/controllerx"
readonly SLUG="local_controllerx"

fail() {
    echo "error: $*" >&2
    exit 1
}

[[ -n "${HA_HOST:-}" ]] \
    || fail "set HA_HOST to the SSH destination, e.g. HA_HOST=hassio@192.168.0.10"

src="${1:-}"
if [[ -n "${src}" ]]; then
    src=$(realpath "${src}")
    [[ -f "${src}/apps/controllerx/controllerx.py" ]] \
        || fail "'${src}' is not a ControllerX checkout"
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

staging=$(mktemp -d)
trap 'rm -fr "${staging}"' EXIT
cp -r "${APP_DIR}/." "${staging}/"

# Same version every time, so the ha CLI rebuilds instead of updating. The
# Dockerfile downloads the ControllerX release before the "-".
base_version=$(sed -n 's/^version: *//p' "${APP_DIR}/config.yaml")
version="${base_version%%-*}-local"
sed -i \
    -e '/^image: /d' \
    -e 's/^name: .*/name: ControllerX (local)/' \
    -e "s/^version: .*/version: ${version}/" \
    "${staging}/config.yaml"

if [[ -n "${src}" ]]; then
    echo "Bundling ControllerX from ${src}"
    rsync -a --exclude __pycache__ \
        "${src}/apps/controllerx/" "${staging}/controllerx-src/"
    cat >> "${staging}/Dockerfile" << 'EOF'

# Local test build: replace the bundled ControllerX with a local checkout
RUN rm -fr /opt/controllerx
COPY controllerx-src /opt/controllerx
EOF
fi

echo "Copying the app to ${HA_HOST}:${REMOTE_DIR}"
rsync -rlptD --delete --chmod=D755 --rsync-path="sudo rsync" \
    "${staging}/" "${HA_HOST}:${REMOTE_DIR}/"

# Login shell, so the ha CLI gets its Supervisor token
echo "Building ${SLUG} ${version} on the host, this takes a few minutes"
if ! ssh "${HA_HOST}" sh -l -s -- "${SLUG}" << 'EOF'; then
set -e
ha store reload > /dev/null
info=$(ha apps info "$1")
installed=$(echo "${info}" | sed -n 's/^version: *//p')
latest=$(echo "${info}" | sed -n 's/^version_latest: *//p')
if [ -z "${installed}" ] || [ "${installed}" = "null" ]; then
    ha apps install "$1"
    ha apps start "$1"
elif [ "${installed}" != "${latest}" ]; then
    ha apps update "$1"
else
    ha apps rebuild "$1"
fi
EOF
    fail "the files were copied, but the ha CLI failed. In Home Assistant," \
        "go to Settings > Apps > App store > ⋮ > Check for updates, then" \
        "install or rebuild ControllerX (local)."
fi

echo "Done. Logs: ssh ${HA_HOST} ha apps logs ${SLUG}"
