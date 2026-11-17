# ControllerX app for Home Assistant

Home Assistant app repository with a single app, **ControllerX**: an
[AppDaemon](https://appdaemon.readthedocs.io/) instance with
[ControllerX](https://xaviml.github.io/controllerx/) preinstalled.

[![Add repository to Home Assistant][repository-badge]][repository-url]

This is an extra installation method. You can still install ControllerX
manually into the AppDaemon app, as explained in the
[ControllerX documentation](https://xaviml.github.io/controllerx/start/installation).

See [controllerx/DOCS.md](controllerx/DOCS.md) for how to configure it.

## Releases

Releases are made by GitHub Actions. Don't change `version` in
`controllerx/config.yaml` or `CONTROLLERX_SHA256` in `controllerx/Dockerfile`
by hand.

- **New ControllerX version:** each ControllerX release triggers the
  **Release ControllerX** workflow. It sets the app version to the ControllerX
  version and pins the checksum from the release's `controllerx.zip.sha256`.
  To run it by hand, start it from the Actions tab with the release tag, like
  `v5.2.4`. Running it again for a released version does nothing.
- **Changes to the app only** (for example, a new base image): after merging
  them, run the **Release app** workflow from the Actions tab with a changelog
  entry. It releases `5.2.3-1`, then `5.2.3-2`, and so on, so Home Assistant
  offers the update. Dependabot checks weekly for a new AppDaemon base
  image and opens a PR for it.

Both workflows add the changelog entry, then build and push the amd64 and
aarch64 images to `ghcr.io/xaviml/controllerx-app/<arch>`. Only then do they
update `main` and tag the release, so users never see a version whose images
don't exist yet.

Pull requests only build the images.

## Testing locally

To try changes before releasing them, deploy the app to your own Home
Assistant as a local app. It's built on the Home Assistant host from the
Dockerfile, so nothing is pushed to ghcr and users never see it.

You need SSH access to the host with the
[Advanced SSH & Web Terminal](https://github.com/hassio-addons/app-ssh) app
(key authentication, protection mode can stay on). Then run:

```shell
# This repository as it is, with the ControllerX release of config.yaml
HA_HOST=hassio@192.168.0.10 scripts/deploy-local.sh

# Same, but with the ControllerX code of a local checkout
HA_HOST=hassio@192.168.0.10 scripts/deploy-local.sh ../controllerx
```

`HA_HOST` is the SSH destination, the user is the `username` of the SSH app.
The script copies the app to `/addons/controllerx` and installs and starts
**ControllerX (local)** (slug `local_controllerx`). Later runs rebuild and
restart it, which takes a minute or so. Run it again after every change, there
is no need to commit.

- Its files are in `/addon_configs/local_controllerx/`, separate from the
  released app. On the first start it creates an example `apps/apps.yaml`.
- Stop the released ControllerX app (and any AppDaemon app with ControllerX)
  while testing, or both will act on the same controllers.
- Logs: `ssh <HA_HOST> ha apps logs local_controllerx`, or the app's Log tab.
- To remove it, uninstall **ControllerX (local)** and delete the folder with
  `ssh <HA_HOST> sudo rm -r /addons/controllerx`.

[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fxaviml%2Fcontrollerx-app
