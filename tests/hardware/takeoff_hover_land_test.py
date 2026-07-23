#!/usr/bin/env python3
"""
Minimal PX4/MAVSDK takeoff-hover-land test.

Examples:
    # SITL
    python -u 13_takeoff_hover_land_test.py --addr udp://:14540 --real

    # Raspberry Pi to Pixhawk serial
    python -u 13_takeoff_hover_land_test.py --addr serial:///dev/serial0:57600 --alt 2.5 --hover 8 --real

The script intentionally requires --real plus a typed confirmation before arming.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import math
import time


async def wait_until_connected(drone) -> None:
    print("[PX4] waiting for connection...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[PX4] connected")
            return


async def wait_for_health(drone, timeout_s: float, require_global_position: bool) -> None:
    print("[PX4] waiting for health checks...")
    start = time.monotonic()
    last_print = 0.0

    async for health in drone.telemetry.health():
        now = time.monotonic()
        gps_ok = health.is_global_position_ok and health.is_home_position_ok
        basic_ok = health.is_armable
        ok = basic_ok and (gps_ok if require_global_position else True)

        if now - last_print >= 1.0:
            print(
                "[PX4] health "
                f"armable={health.is_armable} "
                f"global={health.is_global_position_ok} "
                f"home={health.is_home_position_ok} "
                f"local={health.is_local_position_ok}"
            )
            last_print = now

        if ok:
            print("[PX4] health OK")
            return

        if now - start > timeout_s:
            raise TimeoutError("PX4 health check timeout")


async def get_relative_altitude_m(drone) -> float | None:
    with contextlib.suppress(Exception):
        pos = await anext(drone.telemetry.position())
        if math.isfinite(pos.relative_altitude_m):
            return float(pos.relative_altitude_m)
    return None


async def monitor_altitude_until(drone, target_m: float, timeout_s: float) -> None:
    print(f"[PX4] climbing to about {target_m:.1f} m...")
    start = time.monotonic()
    last_print = 0.0

    async for pos in drone.telemetry.position():
        alt = float(pos.relative_altitude_m)
        now = time.monotonic()

        if now - last_print >= 0.5:
            print(f"[PX4] altitude {alt:.2f} m")
            last_print = now

        if alt >= target_m - 0.35:
            print(f"[PX4] reached test altitude: {alt:.2f} m")
            return

        if now - start > timeout_s:
            raise TimeoutError(f"takeoff altitude timeout, last altitude={alt:.2f} m")


async def wait_until_landed(drone, timeout_s: float) -> None:
    print("[PX4] waiting until landed...")
    start = time.monotonic()
    last_print = 0.0

    async for in_air in drone.telemetry.in_air():
        now = time.monotonic()
        if now - last_print >= 1.0:
            alt = await get_relative_altitude_m(drone)
            alt_text = "--" if alt is None else f"{alt:.2f} m"
            print(f"[PX4] in_air={in_air} altitude={alt_text}")
            last_print = now

        if not in_air:
            print("[PX4] landed")
            return

        if now - start > timeout_s:
            raise TimeoutError("landing timeout")


async def run_test(args: argparse.Namespace) -> None:
    if not args.real:
        print("Refusing to arm: add --real when you intentionally want this test to fly.")
        return

    print("")
    print("REAL FLIGHT TEST")
    print(f"Address: {args.addr}")
    print(f"Takeoff altitude: {args.alt:.1f} m")
    print(f"Hover time: {args.hover:.1f} s")
    print("")
    confirm = input("Type TAKEOFF to arm and start this test: ").strip()
    if confirm != "TAKEOFF":
        print("Canceled.")
        return

    from mavsdk import System
    from mavsdk.action import ActionError

    drone = System()
    await drone.connect(system_address=args.addr)
    await wait_until_connected(drone)
    await wait_for_health(drone, args.health_timeout, not args.no_gps_wait)

    landed = False
    try:
        print(f"[PX4] setting takeoff altitude to {args.alt:.1f} m")
        await drone.action.set_takeoff_altitude(args.alt)

        print("[PX4] arming...")
        await drone.action.arm()

        print("[PX4] takeoff...")
        await drone.action.takeoff()
        await monitor_altitude_until(drone, args.alt, args.takeoff_timeout)

        with contextlib.suppress(ActionError):
            print("[PX4] hold mode...")
            await drone.action.hold()

        print(f"[PX4] hovering for {args.hover:.1f} s")
        await asyncio.sleep(args.hover)

        print("[PX4] landing...")
        await drone.action.land()
        await wait_until_landed(drone, args.land_timeout)
        landed = True

    finally:
        if not landed:
            print("[PX4] cleanup: landing command")
            with contextlib.suppress(Exception):
                await drone.action.land()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PX4 takeoff-hover-land smoke test")
    parser.add_argument("--addr", default="serial:///dev/serial0:57600")
    parser.add_argument("--alt", type=float, default=2.5)
    parser.add_argument("--hover", type=float, default=8.0)
    parser.add_argument("--health-timeout", type=float, default=60.0)
    parser.add_argument("--takeoff-timeout", type=float, default=20.0)
    parser.add_argument("--land-timeout", type=float, default=45.0)
    parser.add_argument("--no-gps-wait", action="store_true")
    parser.add_argument("--real", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.alt < 1.0 or args.alt > 5.0:
        raise SystemExit("--alt must be between 1.0 and 5.0 for this smoke test")
    if args.hover < 1.0 or args.hover > 30.0:
        raise SystemExit("--hover must be between 1.0 and 30.0 for this smoke test")

    asyncio.run(run_test(args))


if __name__ == "__main__":
    main()
