"""
ARIA - Automated Residential Intelligence Assistant
Main entry point for the MCP server
"""

import logging
from colorlog import ColoredFormatter
from src.auth import ensure_data_folder
from src.app import app

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

    ensure_data_folder()  # ← Add this line HERE (first thing!)

    logger.info("=" * 60)
    logger.info("ARIA - Starting up...")
    logger.info("=" * 60)

    logger.info("ARIA initialized successfully!")
    logger.info("Starting Flask web application...")

    try:
        logger.info("ARIA is running on http://localhost:5000")
        logger.info("Press Ctrl+C to stop the server")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
