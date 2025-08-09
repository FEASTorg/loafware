from typing import Optional
from pyCRUMBS import CRUMBS, CRUMBSMessage
import logging

logger = logging.getLogger("loafware.pycrumbs_wrapper")


class PyCRUMBSWrapper:
    """Wrapper for the pyCRUMBS CRUMBS I2C communication library."""

    def __init__(self, bus_number: int = 1) -> None:
        """Initialize the CRUMBS I2C master on the given bus number."""
        self.crumbs = CRUMBS(bus_number)
        self.crumbs.begin()
        logger.info("pyCRUMBSWrapper: I2C bus %d opened as master.", bus_number)

    def send_message(self, message: CRUMBSMessage, target_address: int) -> None:
        """Send a CRUMBSMessage to the specified target address."""
        self.crumbs.send_message(message, target_address)

    def request_message(self, target_address: int) -> Optional[CRUMBSMessage]:
        """Request a CRUMBSMessage from the specified target address."""
        return self.crumbs.request_message(target_address)

    def close(self) -> None:
        """Close the CRUMBS I2C connection."""
        self.crumbs.close()
