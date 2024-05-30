# MOT Toolkit

Multiple Object Tracking (MOT) Toolkit

## Features

- [x] Statistics of the dataset
- [x] Preview
- [x] Edit `Annotation Rectangle`
- [ ] Preview certain target
- [x] Delete a certain target in subsequent frames

## Compatability

Aim to compatible with `X-AnyLabeling` and these following tools:

### System

- Microsoft Windows
- Apple macOS
- Linux Desktop
- Linux Server (X11 Forwarding)

### Python

Recommend to use `Python 3.10` or higher.
(Because of the 'match' syntax)

**Notice:**

You may need to use `Python 3.11` or lower on macOS.

### File Format

- X-AnyLabeling JSON Format

### Annotation Format

- Rectangle

## Step

1. Automatically label each frame(Using `X-Anylabeling`)
2. Manually label object appearance frames
3. Use `Single Object Tracking (SOT)` algorithm
4. Adjust and delete from the frame where the target disappears.

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

`PySide6` may need to install `xcb-cursor` lib on Linux.

Using `apt` on `Ubuntu` or `Debian`:

```bash
# Minimal Version
sudo apt-get install libxcb-cursor0
# or Full Version
sudo apt-get install libxcb-cursor-dev
```

or using `dnf`/`yum` on `RHEL` series or `Fedora`:

```bash
sudo dnf install xcb-util-cursor
# or
# sudo yum install xcb-util-cursor
```

## Thanks

Thanks to the following projects:

- [PySide6](https://doc.qt.io/qtforpython/)
- [X-Anylabeling](https://github.com/CVHub520/X-AnyLabeling)
- [OpenCV](https://opencv.org/)

## License

This project is licensed on [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
