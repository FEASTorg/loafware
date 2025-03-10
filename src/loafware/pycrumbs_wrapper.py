from pyCRUMBS import CRUMBS, CRUMBSMessage
import logging

logger = logging.getLogger("loafware.pycrumbs_wrapper")


class PyCRUMBSWrapper:
    def __init__(self, bus_number: int = 1):
        self.crumbs = CRUMBS(bus_number)
        self.crumbs.begin()
        logger.info("pyCRUMBSWrapper: I2C bus %d opened as master.", bus_number)

    def send_message(self, message: CRUMBSMessage, target_address: int):
        self.crumbs.send_message(message, target_address)

    def request_message(self, target_address: int) -> CRUMBSMessage:
        return self.crumbs.request_message(target_address)

    def close(self):
        self.crumbs.close()
