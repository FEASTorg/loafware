import abc

class Slice(abc.ABC):
    """
    Abstract base class representing a BREAD slice.
    Subclasses must implement the message handling and command mapping.
    """

    def __init__(self, target_address: int, crumbs_wrapper):
        self.target_address = target_address
        self.crumbs = crumbs_wrapper

    @abc.abstractmethod
    def handle_message(self, message):
        """
        Process an incoming CRUMBSMessage.
        """
        pass

    @abc.abstractmethod
    def request_status(self):
        """
        Request a status update from the slice.
        """
        pass

    @abc.abstractmethod
    def send_command(self, command_type: int, data: list):
        """
        Send a command to the slice.
        :param command_type: The CRUMBS command type.
        :param data: List of 6 float values for the payload.
        """
        pass
