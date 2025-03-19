from abc import ABC, abstractmethod

class BaseBattery(ABC):
    """Abstract base class for batteries."""

    def __init__(self, capacity_wh: float, voltage: float, initial_soc: float = 100):
        self.capacity_wh = capacity_wh  # Total energy capacity in Wh
        self.voltage = voltage  # Battery voltage (constant for now)
        self.soc = initial_soc  # State of Charge in %
        self.energy_wh = (initial_soc / 100) * capacity_wh  # Current available energy in Wh

    @abstractmethod
    def discharge(self, power_w: float, time_s: int):
        """Discharge the battery by consuming power (W) for a given time (s)."""
        pass

    @abstractmethod
    def charge(self, power_w: float, time_s: int):
        """Charge the battery using a given power (W) for a given time (s)."""
        pass

    def get_soc(self) -> float:
        """Return the current State of Charge (SoC) in percentage."""
        return (self.energy_wh / self.capacity_wh) * 100

    def get_energy(self) -> float:
        """Return the remaining energy in Wh."""
        return self.energy_wh

    def get_voltage(self) -> float:
        """Return the battery voltage (constant for now)."""
        return self.voltage


class StandardBattery(BaseBattery):
    def __init__(self, capacity_wh=423, voltage=24, initial_soc = 100):
        super().__init__(capacity_wh, voltage, initial_soc)

    def discharge(self, power_w: float, time_s: int):
        if self.energy_wh <= 0:
            return  # Battery is empty

        energy_removed_wh = (power_w * time_s) / 3600  # Convert W to Wh
        self.energy_wh = max(0, self.energy_wh - energy_removed_wh)
        self.soc = (self.energy_wh / self.capacity_wh) * 100  # Update SoC

    def charge(self, power_w: float, time_s: int):
        if self.energy_wh >= self.capacity_wh:
            return  # Battery is full

        energy_added_wh = (power_w * time_s) / 3600  # Convert W to Wh
        self.energy_wh = min(self.capacity_wh, self.energy_wh + energy_added_wh)
        self.soc = (self.energy_wh / self.capacity_wh) * 100  # Update SoC


