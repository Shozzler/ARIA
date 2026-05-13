"""
ARIA - Automated Residential Intelligence Assistant
Main entry point for the MCP server
"""

import logging
from colorlog import ColoredFormatter

# Configure logging (so we can see what's happening when the server runs)
def setup_logging():
    """Set up colored logging for better readability"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create console handler with color
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        '%(log_color)s[%(levelname)s]%(reset)s %(asctime)s - %(name)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def main():
    """Main function - entry point of the application"""
    # Set up logging first
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("ARIA - Starting up...")
    logger.info("=" * 60)

    logger.info("ARIA MCP Server initialized successfully!")
    logger.info("Ready to control your smart home devices")

    # For now, just keep the program running
    # We'll add the actual server code next
    try:
        logger.info("Server is running. Press Ctrl+C to stop.")
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
