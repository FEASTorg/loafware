# src/loafware/motor_controller_slice.py
from typing import Any, Optional, List, Tuple
from pyCRUMBS import CRUMBSMessage
from .slice_base import Slice
import logging

logger = logging.getLogger("loafware.motor_controller_slice")

# Control modes MUST match the device firmware config.h enum:
CLOSED_LOOP_POSITION = 0
CLOSED_LOOP_SPEED = 1
OPEN_LOOP = 2

# Command IDs (aligned with firmware)
CMD_STATUS = 0
CMD_MODE = 1
CMD_SETPOINT = 2
CMD_PID = 3
CMD_BRAKE = 4
CMD_WRITE_PWM = 6

# Device TYPE_ID (must match config.h on the device)
DEVICE_TYPE_ID = 2  # DCMT firmware defines TYPE_ID 2


class MotorControllerSlice(Slice):
    """
    Motor controller slice abstraction. Wraps CRUMBS comms to provide a high-level API
    for the DCMT firmware. All payloads use 6 float slots; unused slots are zero.
    """

    def __init__(self, target_address: int, crumbs_wrapper: Any) -> None:
        super().__init__(target_address, crumbs_wrapper)
        # runtime state (mirrors firmware data fields)
        self.mode: int = OPEN_LOOP
        self.motor1_pwm: float = 0.0
        self.motor2_pwm: float = 0.0
        self.motor1_pos_sp: float = 0.0
        self.motor2_pos_sp: float = 0.0
        self.motor1_pos: float = 0.0
        self.motor2_pos: float = 0.0
        self.motor1_speed_sp: float = 0.0
        self.motor2_speed_sp: float = 0.0
        self.motor1_speed: float = 0.0
        self.motor2_speed: float = 0.0
        self.motor1_brake: bool = False
        self.motor2_brake: bool = False
        # PID tunings (for sending; firmware applies depending on mode)
        self.pid1: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.pid2: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def handle_message(self, message: CRUMBSMessage) -> None:
        """
        Parse and update internal state based on the firmware's response layout.
        Firmware response layout (handleRequest):
          - If OPEN_LOOP:
              data[0]=mode, data[1]=motor1PWM, data[2]=motor2PWM, data[5]=brakeFlag
          - If CLOSED_LOOP_POSITION:
              data[0]=mode,
              data[1]=motor1PositionSetpoint,
              data[2]=motor2PositionSetpoint,
              data[3]=motor1Position,
              data[4]=motor2Position,
              data[5]=brakeFlag
          - If CLOSED_LOOP_SPEED:
              data[0]=mode,
              data[1]=motor1SpeedSetpoint,
              data[2]=motor2SpeedSetpoint,
              data[3]=motor1Speed,
              data[4]=motor2Speed,
              data[5]=brakeFlag
        """
        try:
            # Validate type ID first
            if int(getattr(message, "typeID", -1)) != DEVICE_TYPE_ID:
                logger.warning(
                    "handle_message: unexpected typeID %s (expected %d) from 0x%02X",
                    getattr(message, "typeID", None),
                    DEVICE_TYPE_ID,
                    self.target_address,
                )
                # continue parsing anyway (be forgiving), but note mismatch

            mode = int(message.data[0])
            self.mode = mode

            # parse depending on mode
            if mode == OPEN_LOOP:
                self.motor1_pwm = float(message.data[1])
                self.motor2_pwm = float(message.data[2])
                self.motor1_pos = 0.0
                self.motor2_pos = 0.0
                self.motor1_speed = 0.0
                self.motor2_speed = 0.0
            elif mode == CLOSED_LOOP_POSITION:
                self.motor1_pos_sp = float(message.data[1])
                self.motor2_pos_sp = float(message.data[2])
                self.motor1_pos = float(message.data[3])
                self.motor2_pos = float(message.data[4])
            elif mode == CLOSED_LOOP_SPEED:
                self.motor1_speed_sp = float(message.data[1])
                self.motor2_speed_sp = float(message.data[2])
                self.motor1_speed = float(message.data[3])
                self.motor2_speed = float(message.data[4])
            else:
                logger.warning(
                    "handle_message: unknown mode %s from device 0x%02X",
                    mode,
                    self.target_address,
                )

            brake_flag = int(message.data[5])
            # firmware sets brakeFlag = motor1Brake || motor2Brake
            # we keep a simple interpretation: if brake flag set, mark both as true only if mode is OPEN_LOOP
            if brake_flag:
                # We can't precisely separate motor1 vs motor2 brake from single flag;
                # keep conservative approach: set both True (firmware uses combined flag).
                self.motor1_brake = True
                self.motor2_brake = True
            else:
                self.motor1_brake = False
                self.motor2_brake = False

            logger.info(
                "Parsed status 0x%02X: mode=%d pwm=(%.1f,%.1f) pos_sp=(%.2f,%.2f) pos=(%.2f,%.2f) speed_sp=(%.2f,%.2f) speed=(%.2f,%.2f) brakes=(%s,%s)",
                self.target_address,
                self.mode,
                self.motor1_pwm,
                self.motor2_pwm,
                self.motor1_pos_sp,
                self.motor2_pos_sp,
                self.motor1_pos,
                self.motor2_pos,
                self.motor1_speed_sp,
                self.motor2_speed_sp,
                self.motor1_speed,
                self.motor2_speed,
                self.motor1_brake,
                self.motor2_brake,
            )
        except Exception as e:
            logger.exception(
                "handle_message: failed to parse message from 0x%02X: %s",
                self.target_address,
                e,
            )

    def request_status(self) -> Optional[CRUMBSMessage]:
        """
        Request a status message from the device.
        Returns the CRUMBSMessage on success, None on failure.
        """
        logger.debug(
            "request_status: requesting status from 0x%02X", self.target_address
        )
        try:
            # Many pyCRUMBS wrappers implement request_message(address) which returns CRUMBSMessage or None.
            response: Optional[CRUMBSMessage] = self.crumbs.request_message(
                self.target_address
            )
            if response is None:
                logger.error(
                    "request_status: no response from 0x%02X", self.target_address
                )
                return None
            # verify length and decode: the wrapper already decodes; pass to handler
            self.handle_message(response)
            return response
        except Exception as e:
            logger.exception(
                "request_status: exception when requesting status from 0x%02X: %s",
                self.target_address,
                e,
            )
            return None

    def send_command(self, command_type: int, data: List[float]) -> bool:
        """
        Send an arbitrary command to the motor slice. Data MUST be len==6.
        Returns True if message was written to bus (doesn't guarantee remote state).
        """
        if not isinstance(data, (list, tuple)) or len(data) != 6:
            logger.error("send_command: payload must be sequence of 6 floats")
            return False
        try:
            msg = CRUMBSMessage()
            msg.typeID = DEVICE_TYPE_ID
            msg.commandType = command_type
            # ensure floats
            msg.data = [float(x) for x in data]
            msg.errorFlags = 0
            self.crumbs.send_message(msg, self.target_address)
            logger.debug(
                "send_command: sent cmd=%d to 0x%02X data=%s",
                command_type,
                self.target_address,
                msg.data,
            )
            return True
        except Exception as e:
            logger.exception(
                "send_command: failed to send to 0x%02X: %s", self.target_address, e
            )
            return False

    # --- Convenience wrappers matching firmware semantics ---

    def change_mode(self, mode: int) -> bool:
        """
        Set the control mode on the device.
        Accepts CLOSED_LOOP_POSITION (0), CLOSED_LOOP_SPEED (1), OPEN_LOOP (2).
        """
        if mode not in (CLOSED_LOOP_POSITION, CLOSED_LOOP_SPEED, OPEN_LOOP):
            logger.error("change_mode: invalid mode %s", mode)
            return False
        self.mode = int(mode)
        payload = [float(mode), 0.0, 0.0, 0.0, 0.0, 0.0]
        return self.send_command(CMD_MODE, payload)

    def set_position_setpoints(self, sp1: float, sp2: float) -> bool:
        """Set position setpoints (valid when in CLOSED_LOOP_POSITION)."""
        self.motor1_pos_sp = float(sp1)
        self.motor2_pos_sp = float(sp2)
        payload = [float(sp1), float(sp2), 0.0, 0.0, 0.0, 0.0]
        return self.send_command(CMD_SETPOINT, payload)

    def set_speed_setpoints(self, sp1: float, sp2: float) -> bool:
        """Set speed setpoints (valid when in CLOSED_LOOP_SPEED)."""
        self.motor1_speed_sp = float(sp1)
        self.motor2_speed_sp = float(sp2)
        payload = [float(sp1), float(sp2), 0.0, 0.0, 0.0, 0.0]
        return self.send_command(CMD_SETPOINT, payload)

    def change_pid_tunings(
        self, pid1: Tuple[float, float, float], pid2: Tuple[float, float, float]
    ) -> bool:
        """
        Send PID tunings. Firmware uses PID fields depending on current control mode.
        pid1 and pid2 are (Kp, Ki, Kd).
        """
        if len(pid1) != 3 or len(pid2) != 3:
            logger.error("change_pid_tunings: pid tuples must be length 3")
            return False
        self.pid1 = (float(pid1[0]), float(pid1[1]), float(pid1[2]))
        self.pid2 = (float(pid2[0]), float(pid2[1]), float(pid2[2]))
        payload = [
            self.pid1[0],
            self.pid1[1],
            self.pid1[2],
            self.pid2[0],
            self.pid2[1],
            self.pid2[2],
        ]
        return self.send_command(CMD_PID, payload)

    def set_brakes(self, motor1_brake: bool, motor2_brake: bool) -> bool:
        """
        Engage or release brakes.
        Firmware appears to accept data[0]=1/0 for motor1, data[1]=1/0 for motor2.
        """
        self.motor1_brake = bool(motor1_brake)
        self.motor2_brake = bool(motor2_brake)
        payload = [
            1.0 if motor1_brake else 0.0,
            1.0 if motor2_brake else 0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        return self.send_command(CMD_BRAKE, payload)

    def write_pwm(self, pwm1: float, pwm2: float) -> bool:
        """
        Directly set PWM values (open loop). Firmware expects 0-255.
        We accept 0-100 (%) or 0-255 value; detect and scale if necessary.
        """
        if self.mode != OPEN_LOOP:
            logger.error("write_pwm: attempt to write PWM while not in OPEN_LOOP mode")
            return False

        def norm(v: float) -> float:
            v = float(v)
            if 0.0 <= v <= 1.0:  # treat as 0..1 fraction
                return v * 255.0
            if 0.0 <= v <= 100.0:  # treat as percent
                return (v / 100.0) * 255.0
            # assume already 0-255
            return max(0.0, min(255.0, v))

        pwm1_val = norm(pwm1)
        pwm2_val = norm(pwm2)
        # ensure integers on device side
        payload = [float(int(pwm1_val)), float(int(pwm2_val)), 0.0, 0.0, 0.0, 0.0]
        return self.send_command(CMD_WRITE_PWM, payload)
