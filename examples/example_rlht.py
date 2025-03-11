#!/usr/bin/env python3

import sys
import os
import pprint
import logging
from loafware.pycrumbs_wrapper import PyCRUMBSWrapper
from loafware.relay_heater_slice import RelayHeaterSlice, CONTROL, WRITE

# Increase logging level to DEBUG for more detailed output.
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("example_rlht")


def debug_sys_path():
    logger.debug("Current sys.path:")
    pprint.pprint(sys.path)


def print_usage():
    print("Loafware RLHT Example")
    print("Commands:")
    print("  status                  -> Request status from the RLHT slice")
    print("  mode [0|1]              -> Change mode (0: CONTROL, 1: WRITE)")
    print("  set [sp1] [sp2]         -> Change setpoints for heater 1 and heater 2")
    print("  pid [Kp1] [Ki1] [Kd1] [Kp2] [Ki2] [Kd2] -> Change PID tuning")
    print("  write [r1] [r2]         -> Write relay values (0-100, WRITE mode only)")
    print("  exit                    -> Exit the program")


def main():
    # Debug: Print the sys.path and current working directory
    debug_sys_path()
    logger.debug("Current working directory: %s", os.getcwd())

    # Log the fact that we're about to initialize our components
    logger.debug("Initializing PyCRUMBSWrapper and RLHT Slice.")

    # Assume the RLHT slice is at I2C address 0x0A (adjust as needed)
    target_address = 0x0A

    # Create the pyCRUMBS wrapper (master)
    crumbs_wrapper = PyCRUMBSWrapper(bus_number=1)

    # Create an instance of the RLHT slice
    rlht_slice = RelayHeaterSlice(target_address, crumbs_wrapper)

    print_usage()

    while True:
        try:
            cmd = input("Enter command: ").strip()
            if cmd == "":
                continue
            if cmd.lower() == "exit":
                break
            parts = cmd.split()
            if parts[0] == "status":
                rlht_slice.request_status()
            elif parts[0] == "mode" and len(parts) == 2:
                mode = int(parts[1])
                rlht_slice.change_mode(mode)
            elif parts[0] == "set" and len(parts) == 3:
                sp1 = float(parts[1])
                sp2 = float(parts[2])
                rlht_slice.change_setpoints(sp1, sp2)
            elif parts[0] == "pid" and len(parts) == 7:
                pid1 = (float(parts[1]), float(parts[2]), float(parts[3]))
                pid2 = (float(parts[4]), float(parts[5]), float(parts[6]))
                rlht_slice.change_pid_tuning(pid1, pid2)
            elif parts[0] == "write" and len(parts) == 3:
                r1 = float(parts[1])
                r2 = float(parts[2])
                rlht_slice.write_relays(r1, r2)
            else:
                print("Invalid command or parameters.")
                print_usage()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("Error: %s", e)
    crumbs_wrapper.close()
    print("Exiting RLHT example.")


if __name__ == "__main__":
    main()
