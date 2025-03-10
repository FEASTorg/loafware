# Testing Notes

1. **Clone the Repository:**

   - SSH into your Raspberry Pi and clone the “loafware” repo:

     ```bash
     git clone https://github.com/yourusername/loafware.git
     ```

   - Change into the repo directory:

     ```bash
     cd loafware
     ```

2. **Create and Activate a Virtual Environment:**

   - In the repo directory (or its parent), create a virtual environment:

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

   - This ensures package installations won’t interfere with the system environment.

3. **Install the Local Package in Development Mode:**

   - Since the package isn’t on PyPI, install it locally so that Python can import it as a module:

     ```bash
     pip install -e .
     ```

   - The `-e` flag installs the package in "editable" mode, meaning changes to the code are immediately reflected.

4. **Ensure pyCRUMBS Dependency is Available:**

   - Install it with:

     ```bash
     cd ~/pyCRUMBS
     pip install -e .
     ```

5. **Verify I2C Connectivity:**

   - Use the command below to verify that your Nano is still visible on the I2C bus:

     ```bash
     i2cdetect -y 1
     ```

   - Confirm that the expected I2C address (for example, 0x0A) is listed.

6. **Run the Example Script:**

   - Navigate to the examples folder and run the test harness:

     ```bash
     cd examples
     python example_rlht.py
     ```

   - You should see usage instructions in the terminal. This script provides a command-line interface to:
     - Request status from the RLHT slice.
     - Change mode, set setpoints, adjust PID tuning, or directly write relay values.

7. **Interact and Validate:**

   - At the prompt, type commands such as:
     - `status` – to poll the Nano’s current status.
     - `mode 1` – to change the slice mode to WRITE (or `mode 0` for CONTROL).
     - `set 75 80` – to change the setpoints for two heaters.
     - `pid 1.0 0.0 0.0 1.0 0.0 0.0` – to update PID tuning parameters.
     - `write 50 50` – to directly write relay duty cycles (only valid in WRITE mode).
   - Check the logs printed in the terminal to confirm that commands are sent and responses are received as expected.

8. **Debugging and Logs:**

   - The library uses Python’s logging facility to output debug and info messages.
   - If you encounter issues, increase the logging level in your script by changing:

     ```python
     logging.basicConfig(level=logging.INFO)
     ```

     to:

     ```python
     logging.basicConfig(level=logging.DEBUG)
     ```

   - This will provide more detailed output for troubleshooting.

9. **Wrap-Up:**

   - Once testing is complete, you can stop the example script (Ctrl+C) and deactivate the virtual environment:

     ```bash
     deactivate
     ```
