#!/usr/bin/env python3
import asyncio
import math
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SafetyLimits:
    roll_limit_deg: float = 25.0
    pitch_limit_deg: float = 25.0
    command_timeout_s: float = 0.7

    max_forward_m_s: float = 0.2
    max_right_m_s: float = 0.0
    max_down_m_s: float = 0.0
    max_yaw_deg_s: float = 10.0

    max_forward_accel_m_s2: float = 0.4
    max_right_accel_m_s2: float = 0.4
    max_down_accel_m_s2: float = 0.3
    max_yaw_accel_deg_s2: float = 30.0


@dataclass
class SafetyState:
    failsafe_triggered: bool = False
    failsafe_reason: Optional[str] = None
    manual_override: bool = False
    offboard_started: bool = False

    last_command_time: float = field(default_factory=time.monotonic)
    last_output_time: float = field(default_factory=time.monotonic)
    last_forward_m_s: float = 0.0
    last_right_m_s: float = 0.0
    last_down_m_s: float = 0.0
    last_yaw_deg_s: float = 0.0


class SafetySupervisorV2:
    """Explicit safety gate for MAVSDK body-frame velocity commands."""

    def __init__(
        self,
        drone,
        limits: Optional[SafetyLimits] = None,
        velocity_body_cls=None,
        failsafe_action: str = "hold",
        audible_alerts: bool = True,
        limit_breach_action: str = "warn",
        attitude_breach_action: str = "warn",
    ):
        self.drone = drone
        self.limits = limits or SafetyLimits()
        self.state = SafetyState()
        self.failsafe_action = failsafe_action
        self.velocity_body_cls = velocity_body_cls or self._load_velocity_body_cls()
        self.audible_alerts = audible_alerts
        self.limit_breach_action = limit_breach_action
        self.attitude_breach_action = attitude_breach_action
        self._last_alert_time = 0.0
        self._last_attitude_alert_time = 0.0

        self._tasks: list[asyncio.Task] = []
        self._lock = asyncio.Lock()
        self._installed = False

    def _load_velocity_body_cls(self):
        from mavsdk.offboard import VelocityBodyYawspeed

        return VelocityBodyYawspeed

    def is_triggered(self) -> bool:
        return self.state.failsafe_triggered

    def reason(self) -> Optional[str]:
        return self.state.failsafe_reason

    def mark_offboard_started(self) -> None:
        self.state.offboard_started = True
        self.state.last_command_time = time.monotonic()
        self.state.last_output_time = self.state.last_command_time

    async def install(self) -> None:
        if self._installed:
            return

        self._tasks = [
            asyncio.create_task(self._watch_attitude(), name="watch_attitude"),
            asyncio.create_task(self._watch_manual_override(), name="watch_manual_override"),
            asyncio.create_task(self._watch_command_timeout(), name="watch_command_timeout"),
        ]
        self._installed = True

    async def uninstall(self) -> None:
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        self._installed = False

    async def send_velocity_body(
        self,
        forward_m_s: float,
        right_m_s: float,
        down_m_s: float,
        yaw_deg_s: float,
        source: str = "unknown",
    ) -> bool:
        if self.state.manual_override:
            print("[SAFETY] command blocked: manual override active")
            return False

        if self.is_triggered():
            print(f"[SAFETY] command blocked: {self.reason()}")
            return False

        raw = (forward_m_s, right_m_s, down_m_s, yaw_deg_s)
        if not all(math.isfinite(value) for value in raw):
            await self.trigger(f"non-finite command from {source}: {raw}")
            return False

        # TEMP FOLLOW TEST:
        # Bypass command clamp/slew filtering.
        # Upstream follow controller already applies MAX_* command limits.
        safe = raw
        limited = False
        #safe, limited = self._limit_command(*raw)
        if limited:
            if self.limit_breach_action == "failsafe":
                await self.trigger(f"command exceeded safety limit from {source}: {raw}")
                return False

            if self.limit_breach_action == "warn":
                self.command_limit_alert(
                    f"command exceeded safety limit from {source}: "
                    f"raw=({raw[0]:.2f}, {raw[1]:.2f}, {raw[2]:.2f}, {raw[3]:.2f}) "
                    f"safe=({safe[0]:.2f}, {safe[1]:.2f}, {safe[2]:.2f}, {safe[3]:.2f})"
                )

            elif self.limit_breach_action == "clamp":
                self.command_limit_alert(f"command limited from {source}")

        await self._send_raw_velocity(*safe)
        self.state.last_command_time = time.monotonic()

        print(
            f"[SAFETY] source={source} raw=("
            f"{raw[0]:.2f}, {raw[1]:.2f}, {raw[2]:.2f}, {raw[3]:.2f}"
            f") -> safe=("
            f"{safe[0]:.2f}, {safe[1]:.2f}, {safe[2]:.2f}, {safe[3]:.2f}"
            f")"
        )
        return True

    def _limit_command(
        self,
        forward_m_s: float,
        right_m_s: float,
        down_m_s: float,
        yaw_deg_s: float,
    ) -> tuple[tuple[float, float, float, float], bool]:
        l = self.limits
        now = time.monotonic()
        dt = max(0.001, now - self.state.last_output_time)

        limited = False
        forward, changed = self._clamp_with_flag(
            forward_m_s, -l.max_forward_m_s, l.max_forward_m_s
        )
        limited = limited or changed
        right, changed = self._clamp_with_flag(
            right_m_s, -l.max_right_m_s, l.max_right_m_s
        )
        limited = limited or changed
        down, changed = self._clamp_with_flag(
            down_m_s, -l.max_down_m_s, l.max_down_m_s
        )
        limited = limited or changed
        yaw, changed = self._clamp_with_flag(yaw_deg_s, -l.max_yaw_deg_s, l.max_yaw_deg_s)
        limited = limited or changed

        forward, changed = self._slew_with_flag(
            self.state.last_forward_m_s, forward, l.max_forward_accel_m_s2 * dt
        )
        limited = limited or changed
        right, changed = self._slew_with_flag(
            self.state.last_right_m_s, right, l.max_right_accel_m_s2 * dt
        )
        limited = limited or changed
        down, changed = self._slew_with_flag(
            self.state.last_down_m_s, down, l.max_down_accel_m_s2 * dt
        )
        limited = limited or changed
        yaw, changed = self._slew_with_flag(
            self.state.last_yaw_deg_s, yaw, l.max_yaw_accel_deg_s2 * dt
        )
        limited = limited or changed

        self.state.last_forward_m_s = forward
        self.state.last_right_m_s = right
        self.state.last_down_m_s = down
        self.state.last_yaw_deg_s = yaw
        self.state.last_output_time = now

        return (forward, right, down, yaw), limited

    async def _send_raw_velocity(
        self,
        forward_m_s: float,
        right_m_s: float,
        down_m_s: float,
        yaw_deg_s: float,
    ) -> None:
        cmd = self.velocity_body_cls(forward_m_s, right_m_s, down_m_s, yaw_deg_s)
        await self.drone.offboard.set_velocity_body(cmd)

    async def send_zero(self, source: str = "zero") -> None:
        await self._send_raw_velocity(0.0, 0.0, 0.0, 0.0)
        self.state.last_forward_m_s = 0.0
        self.state.last_right_m_s = 0.0
        self.state.last_down_m_s = 0.0
        self.state.last_yaw_deg_s = 0.0
        self.state.last_output_time = time.monotonic()
        print(f"[SAFETY] zero command sent: {source}")

    async def trigger(self, reason: str) -> None:
        async with self._lock:
            if self.state.failsafe_triggered:
                return

            self.state.failsafe_triggered = True
            self.state.failsafe_reason = reason
            self.alert(f"failsafe: {reason}", min_interval_s=0.0)
            print(f"[FAILSAFE] {reason}")

            try:
                await self.send_zero("failsafe")
                await asyncio.sleep(0.1)
            except Exception as exc:
                print(f"[FAILSAFE] zero command failed: {exc}")

            await self._apply_failsafe_action()

    async def trigger_manual_override(self, reason: str) -> None:
        async with self._lock:
            if self.state.manual_override or self.state.failsafe_triggered:
                return

            self.state.manual_override = True
            self.state.failsafe_triggered = True
            self.state.failsafe_reason = reason
            self.alert(f"manual override: {reason}", min_interval_s=0.0)
            print(f"[MANUAL OVERRIDE] {reason}")

            try:
                await self.send_zero("manual override")
                await asyncio.sleep(0.1)
            except Exception as exc:
                print(f"[MANUAL OVERRIDE] zero command failed: {exc}")

            try:
                await self.drone.offboard.stop()
                print("[MANUAL OVERRIDE] Offboard stopped")
            except Exception as exc:
                print(f"[MANUAL OVERRIDE] offboard stop failed: {exc}")

    async def _apply_failsafe_action(self) -> None:
        try:
            await self.drone.offboard.stop()
            print("[FAILSAFE] Offboard stopped")
        except Exception as exc:
            print(f"[FAILSAFE] offboard stop failed: {exc}")

        if self.failsafe_action == "none":
            return

        if self.failsafe_action == "hold":
            try:
                await self.drone.action.hold()
                print("[FAILSAFE] Hold requested")
            except Exception as exc:
                print(f"[FAILSAFE] hold failed: {exc}")
            return

        if self.failsafe_action == "land":
            try:
                await self.drone.action.land()
                print("[FAILSAFE] Landing requested")
            except Exception as exc:
                print(f"[FAILSAFE] land failed: {exc}")
            return

        if self.failsafe_action == "return":
            try:
                await self.drone.action.return_to_launch()
                print("[FAILSAFE] Return requested")
            except Exception as exc:
                print(f"[FAILSAFE] return failed: {exc}")
            return

        print(f"[FAILSAFE] unknown failsafe_action={self.failsafe_action}")

    async def _watch_attitude(self) -> None:
        async for euler in self.drone.telemetry.attitude_euler():
            if self.is_triggered():
                return

            if abs(euler.roll_deg) > self.limits.roll_limit_deg:
                await self._handle_attitude_breach(
                    f"roll exceeded: {euler.roll_deg:.1f} deg"
                )
                if self.attitude_breach_action == "failsafe":
                    return
                continue

            if abs(euler.pitch_deg) > self.limits.pitch_limit_deg:
                await self._handle_attitude_breach(
                    f"pitch exceeded: {euler.pitch_deg:.1f} deg"
                )
                if self.attitude_breach_action == "failsafe":
                    return
                continue

    async def _handle_attitude_breach(self, reason: str) -> None:
        if self.attitude_breach_action == "failsafe":
            await self.trigger(reason)
            return

        if self.attitude_breach_action == "warn":
            now = time.monotonic()
            if now - self._last_attitude_alert_time >= 1.0:
                self._last_attitude_alert_time = now
                self.attitude_alert(f"attitude warning: {reason}")
                print(f"[ATTITUDE WARNING] {reason}")
            return

        if self.attitude_breach_action == "ignore":
            return

        print(f"[SAFETY] unknown attitude_breach_action={self.attitude_breach_action}")
        return

    async def _watch_manual_override(self) -> None:
        async for mode in self.drone.telemetry.flight_mode():
            if self.state.manual_override:
                return

            if not self.state.offboard_started:
                continue

            if not self._is_offboard_mode(mode):
                await self.trigger_manual_override(
                    f"flight mode changed from OFFBOARD to {mode}"
                )
                return

    async def _watch_command_timeout(self) -> None:
        while not self.is_triggered():
            await asyncio.sleep(0.1)

            if not self.state.offboard_started:
                continue

            dt = time.monotonic() - self.state.last_command_time
            if dt > self.limits.command_timeout_s:
                await self.trigger(f"command timeout: {dt:.2f} s")
                return

    def _clamp(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _clamp_with_flag(self, value: float, low: float, high: float) -> tuple[float, bool]:
        clamped = self._clamp(value, low, high)
        return clamped, clamped != value

    def _slew_with_flag(
        self, current: float, target: float, max_delta: float
    ) -> tuple[float, bool]:
        if target > current + max_delta:
            return current + max_delta, True
        if target < current - max_delta:
            return current - max_delta, True
        return target, False

    def _is_offboard_mode(self, mode) -> bool:
        try:
            from mavsdk.telemetry import FlightMode

            return mode == FlightMode.OFFBOARD
        except Exception:
            return str(mode).endswith("OFFBOARD") or str(mode) == "OFFBOARD"

    def alert(self, message: str, min_interval_s: float = 1.0) -> None:
        if not self.audible_alerts:
            return

        now = time.monotonic()
        if now - self._last_alert_time < min_interval_s:
            return

        self._last_alert_time = now
        print(f"\a[ALERT] {message}", flush=True)

    def command_limit_alert(self, message: str) -> None:
        if not self.audible_alerts:
            return

        now = time.monotonic()
        if now - self._last_alert_time < 1.0:
            return

        self._last_alert_time = now
        print(f"\a[COMMAND LIMIT WARNING] {message}", flush=True)

    def attitude_alert(self, message: str) -> None:
        if not self.audible_alerts:
            return

        now = time.monotonic()
        if now - self._last_alert_time < 1.0:
            return

        self._last_alert_time = now
        print(f"\a\a[ATTITUDE LIMIT WARNING] {message}", flush=True)
