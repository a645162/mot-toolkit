# MOT Toolkit

Multiple Object Tracking (MOT) Toolkit

## Features

- [x] Statistics of the dataset
- [ ] Delete a certain target in subsequent frames
- [ ] Preview certain target

## Compatability

### File Format

- X-AnyLabeling JSON Format

### Annotation Format

- Rectangle

## Remote Run GUI On Linux Server

Recommend to use `X11 Forwarding` to run GUI on a remote server.

**Notice:**

Please make sure the server has been configured to allow `X11 Forwarding` in the `sshd_config` file.
Default configuration file path is `/etc/ssh/sshd_config`,and the configuration item is `X11Forwarding yes`.
Default is `yes`, if not, please modify it and restart the `sshd` service.

You can use `xclock` or `xeyes` to test the feature.

### Windows

- MobaXTerm(Recommend)
- PuTTY + Xming
- Xming
- VcXsrv
- Remote Desktop Manager

### macOS

- XQuartz

## Notice

### Linux

`PySide6` may need to install `xcb-cursor` lib.

Using `apt` on `Ubuntu` or `Debian`:

```bash
# Minimal Version
sudo apt-get install libxcb-cursor0
# or Full Version
sudo apt-get install libxcb-cursor-dev
```

or using `dnf`/`rpm` on `RHEL` series or `Fedora`:

```bash
sudo dnf install xcb-util-cursor
```

## License

This project is licensed on [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
