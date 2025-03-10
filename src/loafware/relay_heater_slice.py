from pyCRUMBS import CRUMBSMessage
from .slice_base import Slice
import logging

logger = logging.getLogger("loafware.relay_heater_slice")

# Define some constants to mimic the C++ definitions
CONTROL = 0
WRITE = 1


class RelayHeaterSlice(Slice):
    def __init__(self, target_address: int, crumbs_wrapper):
        super().__init__(target_address, crumbs_wrapper)
        # Initial state variables, using defaults similar to your RLHT firmware:
        self.mode = CONTROL
        self.setpoint1 = 0.0
        self.setpoint2 = 0.0
        self.pid_tuning1 = (1.0, 0.0, 0.0)  # (Kp, Ki, Kd) for heater 1
        self.pid_tuning2 = (1.0, 0.0, 0.0)  # for heater 2
        self.relay_period1 = 1000
        self.relay_period2 = 1000
        # Other parameters can be added as needed

    def handle_message(self, message: CRUMBSMessage):
        """
        Process an incoming message from the slice.
        This would typically be invoked after a status request.
        """
        # For MVP, simply log the received status
        logger.info("Received response from slice: %s", message)

    def request_status(self):
        """
        Request a status update from the RLHT slice.
        Uses command type 0.
        """
        msg = CRUMBSMessage()
        msg.typeID = 1  # expected SLICE type for RLHT
        msg.commandType = 0  # data request command
        # Set data fields to zero (or as needed)
        msg.data = [0.0] * 6
        msg.errorFlags = 0
        logger.info(
            "Requesting status from slice at address 0x%02X", self.target_address
        )
        response = self.crumbs.request_message(self.target_address)
        if response:
            self.handle_message(response)
        else:
            logger.error(
                "No valid response received from slice at address 0x%02X",
                self.target_address,
            )

    def send_command(self, command_type: int, data: list):
        """
        Send a command to the RLHT slice.
        :param command_type: Command type (e.g., 1 for mode change, 2 for setpoint change, etc.)
        :param data: List of 6 floats for the payload.
        """
        if len(data) != 6:
            logger.error("send_command: Data payload must have 6 float values.")
            return
        msg = CRUMBSMessage()
        msg.typeID = 1  # RLHT slice type ID
        msg.commandType = command_type
        msg.data = data
        msg.errorFlags = 0
        logger.info(
            "Sending command type %d to slice at address 0x%02X with data %s",
            command_type,
            self.target_address,
            data,
        )
        self.crumbs.send_message(msg, self.target_address)

    # Convenience methods for common commands:

    def change_mode(self, mode: int):
        """Change mode: 0 for CONTROL, 1 for WRITE."""
        self.mode = mode
        self.send_command(1, [float(mode)] + [0.0] * 5)

    def change_setpoints(self, setpoint1: float, setpoint2: float):
        """Change setpoints for heater 1 and heater 2."""
        self.setpoint1 = setpoint1
        self.setpoint2 = setpoint2
        self.send_command(2, [setpoint1, setpoint2] + [0.0] * 4)

    def change_pid_tuning(self, pid1: tuple, pid2: tuple):
        """
        Change PID tuning parameters.
        :param pid1: (Kp, Ki, Kd) for heater 1.
        :param pid2: (Kp, Ki, Kd) for heater 2.
        """
        self.pid_tuning1 = pid1
        self.pid_tuning2 = pid2
        data = list(pid1) + list(pid2)
        self.send_command(3, data)

    def write_relays(self, relay1: float, relay2: float):
        """
        Directly set relay duty cycle (0-100%). This command is valid in WRITE mode.
        """
        # For safety, ensure mode is WRITE
        if self.mode != WRITE:
            logger.error("Cannot write relays unless in WRITE mode.")
            return
        # Clamp values and send (scale to the appropriate period if necessary)
        data = [min(max(relay1, 0.0), 100.0), min(max(relay2, 0.0), 100.0)] + [0.0] * 4
        self.send_command(6, data)
