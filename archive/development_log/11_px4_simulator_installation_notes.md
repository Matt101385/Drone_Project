# 11 PX4 Simulator Installation Notes

## Purpose

Record setup notes for PX4 SITL and Gazebo on Mac.

## Basic Tools

Install Xcode command-line tools:

```bash
xcode-select --install
```

Check Homebrew:

```bash
brew --version
```

## Open File Limit

Add to `~/.zshrc`:

```bash
ulimit -S -n 2048
```

Reload:

```bash
source ~/.zshrc
```

## Target Simulator Workflow

```text
PX4 SITL -> Gazebo simulation -> QGroundControl -> Python control script
```

## Key Takeaway

The simulator is separate from real hardware and is used to test offboard control safely before real aircraft tests.
