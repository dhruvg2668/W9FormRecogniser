import logging

class Logger:
    """Logger class with static methods for info and error logging."""
    
    @staticmethod
    def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
        """
        Sets up and returns a logger with the specified name and log level.
        
        Args:
            name (str): Name of the logger. Defaults to __name__.
            level (int): Logging level. Defaults to logging.INFO.
        
        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        return logger

    @staticmethod
    def info(message: str, name: str = __name__) -> None:
        """
        Logs an informational message.
        
        Args:
            message (str): The message to log.
            name (str): Name of the logger. Defaults to __name__.
        """
        logger = Logger.setup_logger(name)
        logger.info(message)

    @staticmethod
    def error(message: str, name: str = __name__) -> None:
        """
        Logs an error message.
        
        Args:
            message (str): The message to log.
            name (str): Name of the logger. Defaults to __name__.
        """
        logger = Logger.setup_logger(name)
        logger.error(message)



logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)