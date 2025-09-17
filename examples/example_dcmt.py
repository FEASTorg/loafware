#!/usr/bin/env python3
"""
Loafware DCMT (motor controller) interactive example.
"""

import logging
from loafware.pycrumbs_wrapper import PyCRUMBSWrapper
from loafware.motor_controller_slice import (
    MotorControllerSlice,
    CLOSED_LOOP_POSITION,
    CLOSED_LOOP_SPEED,
    OPEN_LOOP,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example_dcmt")

I2C_ADDRESS = 0x1a  # change to your motor slice address


def print_usage():
    print("Loafware DCMT Example")
    print("Commands:")
    print("  status                     -> Request status from motor slice")
    print("  mode [0|1|2]               -> Set mode (0: POS, 1: SPEED, 2: OPEN_LOOP)")
    print("  posset [sp1] [sp2]         -> Set position setpoints (pos mode)")
    print("  speeds [sp1] [sp2]         -> Set speed setpoints (speed mode)")
    print("  pid [Kp1] [Ki1] [Kd1] [Kp2] [Ki2] [Kd2] -> Update PID tunings")
    print("  brake [0|1] [0|1]          -> Set brakes for motor1 and motor2")
    print(
        "  pwm [p1] [p2]              -> Write PWM (open loop). Accepts 0-100(%) or 0-255"
    )
    print("  exit                       -> Exit")


def show_status(m: MotorControllerSlice):
    print(f"Addr 0x{m.target_address:02X} | Mode={m.mode}")
    if m.mode == OPEN_LOOP:
        print(
            f"PWM1={m.motor1_pwm:.1f} PWM2={m.motor2_pwm:.1f} | Brakes={m.motor1_brake},{m.motor2_brake}"
        )
    elif m.mode == CLOSED_LOOP_POSITION:
        print(
            f"PosSP1={m.motor1_pos_sp:.2f} PosSP2={m.motor2_pos_sp:.2f} | Pos1={m.motor1_pos:.2f} Pos2={m.motor2_pos:.2f}"
        )
    elif m.mode == CLOSED_LOOP_SPEED:
        print(
            f"SpdSP1={m.motor1_speed_sp:.2f} SpdSP2={m.motor2_speed_sp:.2f} | Spd1={m.motor1_speed:.2f} Spd2={m.motor2_speed:.2f}"
        )
    else:
        print("Unknown mode or no data.")


def main():
    target_address = I2C_ADDRESS
    crumbs = PyCRUMBSWrapper(bus_number=1)
    motor = MotorControllerSlice(target_address, crumbs)

    print("Connected to DCMT slice at I2C address 0x%02X", target_address)

    print_usage()
    try:
        while True:
            try:
                cmd = input("Enter command: ").strip()
            except EOFError:
                break
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit"):
                break

            parts = cmd.split()
            try:
                if parts[0] == "status":
                    resp = motor.request_status()
                    if resp:
                        show_status(motor)
                    else:
                        print("No response.")
                elif parts[0] == "mode" and len(parts) == 2:
                    ok = motor.change_mode(int(parts[1]))
                    print("OK" if ok else "Failed")
                elif parts[0] == "posset" and len(parts) == 3:
                    ok = motor.set_position_setpoints(float(parts[1]), float(parts[2]))
                    print("OK" if ok else "Failed")
                elif parts[0] == "speeds" and len(parts) == 3:
                    ok = motor.set_speed_setpoints(float(parts[1]), float(parts[2]))
                    print("OK" if ok else "Failed")
                elif parts[0] == "pid" and len(parts) == 7:
                    pid1 = (float(parts[1]), float(parts[2]), float(parts[3]))
                    pid2 = (float(parts[4]), float(parts[5]), float(parts[6]))
                    ok = motor.change_pid_tunings(pid1, pid2)
                    print("OK" if ok else "Failed")
                elif parts[0] == "brake" and len(parts) == 3:
                    b1 = bool(int(parts[1]))
                    b2 = bool(int(parts[2]))
                    ok = motor.set_brakes(b1, b2)
                    print("OK" if ok else "Failed")
                elif parts[0] == "pwm" and len(parts) == 3:
                    ok = motor.write_pwm(float(parts[1]), float(parts[2]))
                    print("OK" if ok else "Failed (ensure mode is OPEN_LOOP)")
                else:
                    print("Invalid command or parameters.")
                    print_usage()
            except ValueError as ve:
                logger.error("Invalid numeric value: %s", ve)
    finally:
        crumbs.close()
        print("Exiting DCMT example.")


if __name__ == "__main__":
    main()
