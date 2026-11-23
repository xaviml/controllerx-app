#!/usr/bin/env bash
# ==============================================================================
# Prepares a release of the ControllerX app: updates the version, the
# ControllerX checksum, the image and the changelog. It doesn't commit.
#
#   release.sh controllerx vX.Y.Z        Bundle a ControllerX release as X.Y.Z-1
#   release.sh app "<changelog entry>"   Release app-only changes as X.Y.Z-(N+1)
#
# App versions are always X.Y.Z-N, never a plain X.Y.Z: Home Assistant
# compares them as SemVer, where X.Y.Z-N is a pre-release of X.Y.Z, so a
# plain X.Y.Z followed by X.Y.Z-N would look like a downgrade. See README.md.
#
# Writes "release" (true/false) and "version" to $GITHUB_OUTPUT.
# ==============================================================================
set -euo pipefail

readonly APP_DIR="controllerx"
readonly CONFIG="${APP_DIR}/config.yaml"
readonly DOCKERFILE="${APP_DIR}/Dockerfile"
readonly CHANGELOG="${APP_DIR}/CHANGELOG.md"
readonly IMAGE="ghcr.io/xaviml/controllerx-app/{arch}"
readonly RELEASES_URL="https://github.com/xaviml/controllerx/releases"
readonly OUTPUT="${GITHUB_OUTPUT:-/dev/stdout}"

fail() {
    echo "::error::$*" >&2
    exit 1
}

output() {
    {
        echo "release=$1"
        echo "version=$2"
    } >> "${OUTPUT}"
}

# Returns success if version $1 is lower than version $2
version_lt() {
    [[ "$1" != "$2" ]] \
        && [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n 1)" == "$1" ]]
}

has_image() {
    grep -q '^image: ' "${CONFIG}"
}

set_version() {
    sed -i "s/^version: .*/version: $1/" "${CONFIG}"
}

set_image() {
    if ! has_image; then
        sed -i "/^url: /a image: ${IMAGE}" "${CONFIG}"
    fi
}

# Adds "## <version>" with one entry on top of the changelog, unless it exists
add_changelog() {
    if grep -qxF "## $1" "${CHANGELOG}"; then
        return
    fi
    VERSION="$1" ENTRY="$2" awk '
        !done && /^## / {
            print "## " ENVIRON["VERSION"] "\n\n- " ENVIRON["ENTRY"] "\n"
            done = 1
        }
        { print }
        END {
            if (!done) print "\n## " ENVIRON["VERSION"] "\n\n- " ENVIRON["ENTRY"]
        }
    ' "${CHANGELOG}" > "${CHANGELOG}.tmp"
    mv "${CHANGELOG}.tmp" "${CHANGELOG}"
}

release_controllerx() {
    local tag="$1"
    local version
    local new_version
    local sha256

    [[ "${tag}" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]] \
        || fail "Invalid ControllerX version '${tag}', expected vX.Y.Z"
    version="${BASH_REMATCH[1]}"

    if version_lt "${version}" "${current_base}"; then
        fail "ControllerX ${tag} is older than the bundled ${current_base}"
    fi
    if [[ "${version}" == "${current_base}" ]] && has_image; then
        echo "::notice::ControllerX ${tag} is already released (${current_version}), nothing to do"
        output false "${current_version}"
        return
    fi

    sha256=$(curl -fsSL "${RELEASES_URL}/download/${tag}/controllerx.zip.sha256" \
        | cut -d ' ' -f 1) \
        || fail "Could not download controllerx.zip.sha256 from the ${tag} release"
    [[ "${sha256}" =~ ^[0-9a-f]{64}$ ]] \
        || fail "Invalid checksum in controllerx.zip.sha256 from the ${tag} release"

    if [[ "${version}" == "${current_base}" ]]; then
        # First publish of the bundled version, keep the version as it is
        new_version="${current_version}"
        grep -qF "ARG CONTROLLERX_SHA256=\"${sha256}\"" "${DOCKERFILE}" \
            || fail "The checksum in ${DOCKERFILE} doesn't match the ${tag} release"
    else
        new_version="${version}-1"
        set_version "${new_version}"
        sed -i "s/^ARG CONTROLLERX_SHA256=.*/ARG CONTROLLERX_SHA256=\"${sha256}\"/" \
            "${DOCKERFILE}"
    fi

    set_image
    add_changelog "${new_version}" \
        "Update ControllerX to [${tag}](${RELEASES_URL}/tag/${tag})."
    output true "${new_version}"
}

release_app() {
    local entry="$1"
    local last_tag="v${current_version}"
    local revision=0
    local new_version

    [[ -n "${entry//[[:space:]]/}" ]] || fail "The changelog entry is empty"
    has_image \
        || fail "There is no published release yet, run the ControllerX release first"
    git rev-parse -q --verify "refs/tags/${last_tag}" > /dev/null \
        || fail "Tag ${last_tag} for the current version doesn't exist"
    if git diff --quiet "${last_tag}" HEAD -- "${APP_DIR}"; then
        fail "Nothing changed in ${APP_DIR}/ since ${last_tag}"
    fi

    # Versions released before X.Y.Z-N was the rule have no "-N", count them as 0
    if [[ "${current_version}" == *-* ]]; then
        revision="${current_version##*-}"
    fi
    new_version="${current_base}-$((revision + 1))"

    set_version "${new_version}"
    add_changelog "${new_version}" "${entry}"
    output true "${new_version}"
}

current_version=$(sed -n 's/^version: *//p' "${CONFIG}")
current_base="${current_version%%-*}"
readonly current_version current_base

case "${1:-}" in
    controllerx) release_controllerx "${2:-}" ;;
    app) release_app "${2:-}" ;;
    *) fail "Usage: $0 controllerx vX.Y.Z | $0 app \"<changelog entry>\"" ;;
esac
