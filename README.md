# MOT Toolkit

Multiple Object Tracking (MOT) Toolkit

## Features

- [x] Statistics of the dataset
- [x] Preview
- [x] Edit `Annotation Rectangle` (Move, Resize)
- [x] Delete a certain target in subsequent frames
- [x] Multi-Level File Explorer (Apple macOS Finder)
- [ ] Support `XBox Controller`
- [ ] Preview certain target
- [ ] Export the dataset
- [ ] Support Text Annotation (Refer-MOT)
- [ ] Dataset Format Convertor

## Compatability

Aim to compatible with `X-AnyLabeling` and `LabelMe` and these following:

- [x] `X-AnyLabeling`
- [x] `LabelMe`
- [x] `DanceTrack` (Python script)
- [x] `ultralytics (YOLO Series)` (Python script)
- [ ] Export to `COCO Format` (Python script)
- [ ] Export to `MOT Challenge` (Python script)
- [ ] Export to `DanceTrack` (GUI)
- [ ] Export to `ultralytics (YOLO Series)` (GUI)
- [ ] Export to `COCO Format` (GUI)

## Installation

### 1. Use `rye`

```bash
rye sync --update-all
```

### 2. Use `pip`

1. (Optional) Create a virtual environment:

```bash
conda create -n mot-toolkit python=3.12 -y
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

### System

- Microsoft Windows
- Apple macOS
- Linux Desktop (X.Org)
- Linux Desktop (Wayland)
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
sudo apt-get install libxcb-cursor0 -y
# or Full Version
sudo apt-get install libxcb-cursor-dev -y
```

or using `dnf`/`yum` on `RHEL` series or `Fedora`:

```bash
sudo dnf install xcb-util-cursor -y
# or
# sudo yum install xcb-util-cursor -y
```

or using `pacman` on `Arch` series
(Such as `Manjaro` and `EndavourOS`):

```bash
pacman -S xcb-util-cursor
```

## Wayland

You can't use `Global Menu` on `Wayland`.

## Python 3.13

May not compatible with `PySide6` on `Python 3.13`.

https://wiki.qt.io/Qt_for_Python_Development_Notes

## Thanks

Thanks to the following projects:

- [PySide6](https://doc.qt.io/qtforpython/)
- [X-Anylabeling](https://github.com/CVHub520/X-AnyLabeling)
- [OpenCV](https://opencv.org/)

## License

This project is licensed on [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
