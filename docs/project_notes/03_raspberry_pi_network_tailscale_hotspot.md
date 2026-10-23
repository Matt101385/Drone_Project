# 03 Raspberry Pi Network: Tailscale and Hotspot

## Purpose

Record laptop-to-Raspberry-Pi connection methods used during development.

## Tailscale

Tailscale creates a private WireGuard-based network.

Example:

```text
Laptop: 100.101.1.5
Pi:     100.101.1.8
```

Enable at boot:

```bash
sudo systemctl enable tailscaled
```

Start and check:

```bash
tailscale up
tailscale status
```

## Raspberry Pi Hotspot

Hotspot name:

```text
Matt drone
```

IP layout:

```text
Mac: 10.42.0.100
Pi:  10.42.0.1
```

SSH:

```bash
ssh matt@10.42.0.1
```

Enable autoconnect:

```bash
sudo nmcli connection modify "Matt drone" connection.autoconnect yes
```

Bring hotspot up after reboot:

```bash
sudo nmcli connection up "Matt drone"
```

## Practical Rule

Use Tailscale when both devices have internet. Use the Pi hotspot when working directly with the drone/Pi without external Wi-Fi.
