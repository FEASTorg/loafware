#!/usr/bin/env python3
"""
Loafware RLHT interactive example.
"""

import logging
from loafware.pycrumbs_wrapper import PyCRUMBSWrapper
from loafware.relay_heater_slice import RelayHeaterSlice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example_rlht")

I2C_ADDRESS = 0x10

def print_usage():
    print("Loafware RLHT Example")
    print("Commands:")
    print("  status                       -> Request status from the RLHT slice")
    print("  mode [0|1]                   -> Change mode (0: CONTROL, 1: WRITE)")
    print("  set [sp1] [sp2]              -> Change setpoints for heater 1 and 2")
    print("  pid [Kp1] [Ki1] [Kd1] [Kp2] [Ki2] [Kd2] -> Change PID tuning")
    print(
        "  write [r1] [r2]              -> Write relay values (0-100, WRITE mode only)"
    )
    print("  exit                         -> Exit the program")


def show_status(rlht: RelayHeaterSlice):
    print(
        f"Addr 0x{rlht.target_address:02X} | Mode: {rlht.mode} | "
        f"T1={rlht.temperature1:.2f}C T2={rlht.temperature2:.2f}C | "
        f"SP1={rlht.setpoint1:.2f} SP2={rlht.setpoint2:.2f} | "
        f"onTime1={rlht.relay_on_time1:.1f} onTime2={rlht.relay_on_time2:.1f} | "
        f"err=0x{rlht.error_flags:02X}"
    )


def main():
    target_address = I2C_ADDRESS
    crumbs = PyCRUMBSWrapper(bus_number=1)
    rlht = RelayHeaterSlice(target_address, crumbs)

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
                    resp = rlht.request_status()
                    if resp:
                        show_status(rlht)
                    else:
                        print("No response or failed to parse status.")
                elif parts[0] == "mode" and len(parts) == 2:
                    ok = rlht.change_mode(int(parts[1]))
                    print("OK" if ok else "Failed")
                elif parts[0] == "set" and len(parts) == 3:
                    ok = rlht.change_setpoints(float(parts[1]), float(parts[2]))
                    print("OK" if ok else "Failed")
                elif parts[0] == "pid" and len(parts) == 7:
                    pid1 = (float(parts[1]), float(parts[2]), float(parts[3]))
                    pid2 = (float(parts[4]), float(parts[5]), float(parts[6]))
                    ok = rlht.change_pid_tuning(pid1, pid2)
                    print("OK" if ok else "Failed")
                elif parts[0] == "write" and len(parts) == 3:
                    ok = rlht.write_relays(float(parts[1]), float(parts[2]))
                    print("OK" if ok else "Failed (mode must be WRITE)")
                else:
                    print("Invalid command or parameters.")
                    print_usage()
            except ValueError as ve:
                logger.error("Invalid numeric value: %s", ve)
    finally:
        crumbs.close()
        print("Exiting RLHT example.")


if __name__ == "__main__":
    main()
