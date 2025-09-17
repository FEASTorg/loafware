# src/loafware/relay_heater_slice.py
from typing import Any, Optional, Tuple, List
from pyCRUMBS import CRUMBSMessage
from .slice_base import Slice
import logging

logger = logging.getLogger("loafware.relay_heater_slice")

# Device constants (must match firmware)
DEVICE_TYPE_ID = 1  # RLHT firmware TYPE_ID

# Modes (match RLHT firmware Mode enum)
CONTROL = 0
WRITE = 1


class RelayHeaterSlice(Slice):
    """
    RLHT (relay-heater) slice wrapper.
    - request_status() returns the CRUMBSMessage (and updates internal state) or None.
    - send_command(...) returns True if the message was written to the bus (not a remote success guarantee).
    """

    def __init__(self, target_address: int, crumbs_wrapper: Any) -> None:
        super().__init__(target_address, crumbs_wrapper)
        # Mirror firmware state fields
        self.mode: int = CONTROL
        self.temperature1: float = 0.0
        self.temperature2: float = 0.0
        self.setpoint1: float = 0.0
        self.setpoint2: float = 0.0
        self.relay_on_time1: float = 0.0
        self.relay_on_time2: float = 0.0
        self.relay_period1: int = 1000
        self.relay_period2: int = 1000
        self.pid_tuning1: Tuple[float, float, float] = (1.0, 0.0, 0.0)
        self.pid_tuning2: Tuple[float, float, float] = (1.0, 0.0, 0.0)
        self.error_flags: int = 0

    def handle_message(self, message: CRUMBSMessage) -> None:
        """
        Parse an incoming status message from RLHT and update internal state.
        Firmware handleRequest returns (for commandType 0):
          data[0] = temperature1
          data[1] = temperature2
          data[2] = setpoint1
          data[3] = setpoint2
          data[4] = relayOnTime1
          data[5] = relayOnTime2
        """
        try:
            # Optional: warn if typeID mismatch
            if int(getattr(message, "typeID", -1)) != DEVICE_TYPE_ID:
                logger.warning(
                    "handle_message: unexpected typeID %s (expected %d) from 0x%02X",
                    getattr(message, "typeID", None),
                    DEVICE_TYPE_ID,
                    self.target_address,
                )

            # Parse fields (be defensive about length)
            d = list(message.data) if hasattr(message, "data") else [0.0] * 6
            # pad/truncate to 6
            if len(d) < 6:
                d = d + [0.0] * (6 - len(d))
            else:
                d = d[:6]

            self.temperature1 = float(d[0])
            self.temperature2 = float(d[1])
            self.setpoint1 = float(d[2])
            self.setpoint2 = float(d[3])
            self.relay_on_time1 = float(d[4])
            self.relay_on_time2 = float(d[5])
            self.error_flags = int(getattr(message, "errorFlags", 0))

            logger.info(
                "RLHT @0x%02X status: T1=%.2f T2=%.2f SP1=%.2f SP2=%.2f onTime1=%.1f onTime2=%.1f err=0x%02X",
                self.target_address,
                self.temperature1,
                self.temperature2,
                self.setpoint1,
                self.setpoint2,
                self.relay_on_time1,
                self.relay_on_time2,
                self.error_flags,
            )
        except Exception as e:
            logger.exception(
                "handle_message: failed to parse message from 0x%02X: %s",
                self.target_address,
                e,
            )

    def request_status(self) -> Optional[CRUMBSMessage]:
        """
        Request a status update from the RLHT slice (commandType 0).
        Returns the CRUMBSMessage if received and decoded, otherwise None.
        """
        logger.debug(
            "request_status: requesting status from 0x%02X", self.target_address
        )
        try:
            response: Optional[CRUMBSMessage] = self.crumbs.request_message(
                self.target_address
            )
            if response is None:
                logger.error(
                    "request_status: no response from 0x%02X", self.target_address
                )
                return None
            # Let handler parse and update local state
            self.handle_message(response)
            return response
        except Exception as e:
            logger.exception(
                "request_status: exception requesting status from 0x%02X: %s",
                self.target_address,
                e,
            )
            return None

    def send_command(self, command_type: int, data: List[float]) -> bool:
        """
        Send a command to RLHT. Data must be length 6 (pads/truncates if needed).
        Returns True if the message was written to the bus.
        """
        try:
            # normalize payload to 6 floats
            if not isinstance(data, (list, tuple)):
                logger.error("send_command: payload must be list/tuple of floats")
                return False
            payload = [float(x) for x in data]
            if len(payload) < 6:
                payload += [0.0] * (6 - len(payload))
            elif len(payload) > 6:
                payload = payload[:6]

            msg = CRUMBSMessage()
            msg.typeID = DEVICE_TYPE_ID
            msg.commandType = int(command_type)
            msg.data = payload
            msg.errorFlags = 0

            self.crumbs.send_message(msg, self.target_address)
            logger.debug(
                "send_command: sent cmd=%d to 0x%02X data=%s",
                command_type,
                self.target_address,
                payload,
            )
            return True
        except Exception as e:
            logger.exception(
                "send_command: failed to send to 0x%02X: %s", self.target_address, e
            )
            return False

    # Convenience wrappers -------------------------------------------------

    def change_mode(self, mode: int) -> bool:
        """Change mode: CONTROL=0 or WRITE=1."""
        if mode not in (CONTROL, WRITE):
            logger.error("change_mode: invalid mode %s", mode)
            return False
        self.mode = int(mode)
        return self.send_command(1, [float(mode)] + [0.0] * 5)

    def change_setpoints(self, setpoint1: float, setpoint2: float) -> bool:
        """Change setpoints for heater 1 and heater 2 (commandType 2)."""
        self.setpoint1 = float(setpoint1)
        self.setpoint2 = float(setpoint2)
        return self.send_command(2, [self.setpoint1, self.setpoint2] + [0.0] * 4)

    def change_pid_tuning(
        self, pid1: Tuple[float, float, float], pid2: Tuple[float, float, float]
    ) -> bool:
        """Change PID tuning parameters (commandType 3)."""
        if len(pid1) != 3 or len(pid2) != 3:
            logger.error("change_pid_tuning: pid tuples must be length 3")
            return False
        self.pid_tuning1 = (float(pid1[0]), float(pid1[1]), float(pid1[2]))
        self.pid_tuning2 = (float(pid2[0]), float(pid2[1]), float(pid2[2]))
        data: List[float] = [*self.pid_tuning1, *self.pid_tuning2]
        return self.send_command(3, data)

    def change_relay_periods(self, period1_ms: int, period2_ms: int) -> bool:
        """Change relay periods (commandType 4)."""
        self.relay_period1 = int(period1_ms)
        self.relay_period2 = int(period2_ms)
        return self.send_command(
            4, [float(self.relay_period1), float(self.relay_period2)] + [0.0] * 4
        )

    def change_thermo_select(self, t1: int, t2: int) -> bool:
        """Select thermocouples for relays (commandType 5)."""
        return self.send_command(5, [float(t1), float(t2)] + [0.0] * 4)

    def write_relays(self, relay1_pct: float, relay2_pct: float) -> bool:
        """
        Directly set relay duty cycle (0-100%). This command is valid only in WRITE mode.
        Firmware expects 0-100 values and maps them to onTime using relayPeriod.
        """
        if self.mode != WRITE:
            logger.error("write_relays: cannot write unless in WRITE mode")
            return False
        r1 = float(max(0.0, min(100.0, relay1_pct)))
        r2 = float(max(0.0, min(100.0, relay2_pct)))
        return self.send_command(6, [r1, r2, 0.0, 0.0, 0.0, 0.0])
