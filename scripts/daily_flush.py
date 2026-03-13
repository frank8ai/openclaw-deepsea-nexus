#!/usr/bin/env python
"""
Daily Flush Daemon
Automatically flush sessions at configured time
"""

import sys
import time
import signal
import logging
from datetime import datetime, time as dt_time
from threading import Event

from _legacy_layout import daily_flush_legacy_layout


class DailyFlushDaemon:
    """Daemon for automatic daily flush"""
    
    def __init__(self, flush_time="03:00", interval=60):
        """
        Args:
            flush_time: Time to perform flush (HH:MM format)
            interval: Check interval in seconds
        """
        self.flush_time = flush_time
        self.interval = interval
        self.stop_event = Event()
        self.last_flush_date = None
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logging"""
        logger = logging.getLogger("DailyFlushDaemon")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _parse_time(self, time_str):
        """Parse time string to datetime.time"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return dt_time(hour, minute)
        except ValueError:
            self.logger.error(f"Invalid time format: {time_str}, using 03:00")
            return dt_time(3, 0)
    
    def _should_flush(self):
        """Check if it's time to flush"""
        now = datetime.now().time()
        flush_t = self._parse_time(self.flush_time)
        today = datetime.now().strftime("%Y-%m-%d")

        if self.last_flush_date == today:
            return False
        
        # Check if current time is at or past flush time (within the hour)
        return (now.hour == flush_t.hour and now.minute >= flush_t.minute)
    
    def flush(self):
        """Perform the flush operation"""
        self.logger.info("Starting scheduled flush...")
        try:
            stats = daily_flush_legacy_layout()
            self.last_flush_date = stats["date"]
            self.logger.info(
                f"Flush completed: {stats['flushed_count']} sessions "
                f"moved to {stats['archive_dir']}"
            )
            return stats
        except Exception as e:
            self.logger.error(f"Flush failed: {e}")
            return None
    
    def run(self):
        """Run the daemon"""
        self.logger.info(f"Daily Flush Daemon started (flush at {self.flush_time})")
        
        # Initial flush if it's already past flush time
        if self._should_flush():
            self.flush()
        
        while not self.stop_event.is_set():
            time.sleep(self.interval)
            
            if self._should_flush():
                self.flush()
    
    def stop(self):
        """Stop the daemon"""
        self.logger.info("Stopping Daily Flush Daemon...")
        self.stop_event.set()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    daemon.stop()
    sys.exit(0)


def run_once():
    """Run flush once and exit"""
    stats = daily_flush_legacy_layout()
    if stats:
        print(f"Flushed {stats['flushed_count']} sessions to {stats['archive_dir']}")
    return stats


def run_daemon(flush_time="03:00"):
    """Run as daemon"""
    global daemon
    daemon = DailyFlushDaemon(flush_time=flush_time)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    daemon.run()


# Global daemon instance
daemon = None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Flush Daemon")
    parser.add_argument('--time', type=str, default="03:00",
                        help='Flush time (HH:MM format, default: 03:00)')
    parser.add_argument('--daemon', action='store_true',
                        help='Run as daemon')
    parser.add_argument('--once', action='store_true',
                        help='Run flush once and exit')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    elif args.daemon:
        run_daemon(args.time)
    else:
        # Default: run once
        print("Running single flush...")
        run_once()
