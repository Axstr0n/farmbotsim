from datetime import datetime, timedelta

class DateTimeManager:
    def __init__(self, start_date="01.01.2025 00:00:00"):
        """
        Manages simulation time.
        """
        self.current_time = datetime.strptime(start_date, "%d.%m.%Y %H:%M:%S")

    def advance_time(self, seconds):
        self.current_time += timedelta(seconds=seconds)

    def get_time(self):
        """Returns the current simulation time."""
        return self.current_time.strftime("%d.%m.%Y %H:%M:%S")
    
    def get_month(self):
        """Returns month (1-12)"""
        return self.current_time.month

    def reset(self, start_date="01.01.2025 00:00:00"):
        """Resets the simulation time."""
        self.current_time = datetime.strptime(start_date, "%d.%m.%Y %H:%M:%S")
