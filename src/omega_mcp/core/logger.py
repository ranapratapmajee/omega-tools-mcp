# src/omega_mcp/core/logger.py
import logging
import sys

def setup_logger(name: str = "omega_mcp") -> logging.Logger:
    """
    Configures a production-safe logger that outputs strictly to sys.stderr.
    This prevents standard library logs from breaking the MCP stdout channel.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format logs cleanly for debugging panels
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Direct stream handler explicitly to stderr
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Globally accessible logger instance
logger = setup_logger()