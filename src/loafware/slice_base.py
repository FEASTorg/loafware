# src/loafware/slice_base.py
from typing import Any, List, Optional
import abc


class Slice(abc.ABC):
    """
    Abstract base class representing a BREAD slice.
    Subclasses must implement the message handling and command mapping.
    """

    def __init__(self, target_address: int, crumbs_wrapper: Any) -> None:
        """
        Initialize the slice with a target address and crumbs wrapper.
        :param target_address: The I2C address of the slice.
        :param crumbs_wrapper: Wrapper for CRUMBS communication.
        """
        self.target_address = target_address
        self.crumbs = crumbs_wrapper

    @abc.abstractmethod
    def handle_message(self, message: Any) -> None:
        """
        Process an incoming CRUMBSMessage.
        :param message: The CRUMBSMessage to process.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def request_status(self) -> Optional[Any]:
        """
        Request a status update from the slice.
        Should return the decoded CRUMBSMessage or None on failure.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def send_command(self, command_type: int, data: List[float]) -> bool:
        """
        Send a command to the slice.
        :param command_type: The CRUMBS command type.
        :param data: List of 6 float values for the payload.
        :return: True if the send was issued (doesn't guarantee remote success).
        """
        raise NotImplementedError
