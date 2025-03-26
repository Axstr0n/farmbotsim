import math

class Battery():
    """Abstract base class for batteries."""

    def __init__(self, folder_path, initial_soc: float = 100):
        self.folder_path = folder_path
        self._initialize_battery_params()
        self.soc = initial_soc  # State of Charge in %
        self.energy_wh = (initial_soc / 100) * self.capacity_wh  # Current available energy in Wh
        

    def _initialize_battery_params(self):
        with open(f'{self.folder_path}/config.txt', 'r') as f:
            for line in f:
                param, value = line.split(": ")
                value = value.strip()
                if param == "capacity_wh": self.capacity_wh = float(value)
                elif param == "voltage": self.voltage = float(value)
                elif param == "jan_max": self.jan_max_data = self._get_month_data_points(f'{self.folder_path}/{value}')
                elif param == "jan_min": self.jan_min_data = self._get_month_data_points(f'{self.folder_path}/{value}')
                elif param == "jun_max": self.jun_max_data = self._get_month_data_points(f'{self.folder_path}/{value}')

    def _get_month_data_points(self, file_path):
        result = []
        with open(file_path, "r") as f:
            for i,line in enumerate(f):
                if i==0: continue
                parts = line.split()
                result.append( (int(float(parts[0])*3600), float(parts[-1])) )
        return result

    def discharge(self, power_w: float, time_s: int):
        if self.energy_wh <= 0:
            return  # Battery is empty
        # TO DO # implement from data points
        energy_removed_wh = (power_w * time_s) / 3600  # Convert W to Wh
        self.energy_wh = max(0, self.energy_wh - energy_removed_wh)
        self.soc = (self.energy_wh / self.capacity_wh) * 100  # Update SoC

    def charge(self, time_s: int, month: int):
        """month (1-12)"""
        if self.energy_wh >= self.capacity_wh:
            return  # Battery is full
        
        # jan_time_s = self._find_x_for_y(self.jan_min_data, self.energy_wh)
        # jun_time_s = self._find_x_for_y(self.jun_max_data, self.energy_wh)
        jan_time_s = self._find_x_for_y_month("jan", self.energy_wh)
        jun_time_s = self._find_x_for_y_month("jun", self.energy_wh)
        jan_next_time = jan_time_s+time_s
        jun_next_time = jun_time_s+time_s
        # jan_new_wh = self._find_y_for_x(self.jan_min_data, jan_next_time)
        # jun_new_wh = self._find_y_for_x(self.jun_max_data, jun_next_time)
        jan_new_wh = self._find_y_for_x_month("jan", jan_next_time)
        jun_new_wh = self._find_y_for_x_month("jun", jun_next_time)
        # print()
        # print(f'{jan_time_s} {next_time}')
        # print(f'{jan_time_s/3600:.4f} {next_time/3600:.4f}')
        # print(f'{self.energy_wh:.4f} {jan_new_wh:.4f}')

        weight1 = (1 + math.cos(math.pi * (month-1) / 6)) / 2
        weight2 = 1 - weight1

        new_wh = weight1*jan_new_wh + weight2*jun_new_wh

        self.energy_wh = new_wh
        self.soc = (self.energy_wh / self.capacity_wh) * 100  # Update SoC
    

    def _linear_interpolate(self, x0, y0, x1, y1, x):
        """
        Perform linear interpolation to find y for a given x between two points (x0, y0) and (x1, y1).
        """
        if x1 == x0:  # Avoid division by zero
            return y0
        return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

    def _find_y_for_x_month(self, month_name, x):
        """
        Given a list of (x, y) tuples, find the corresponding y for a given x using linear interpolation.
        """
        if month_name == "jan":
            # Find the two points surrounding the x value
            for i in range(1, len(self.jan_min_data)):
                x0, y0 = self.jan_min_data[i-1]
                x1, y1 = self.jan_min_data[i]
                
                if x0 <= x <= x1:  # x is between x0 and x1
                    return self._linear_interpolate(x0, y0, x1, y1, x)
        else:
            # Find the two points surrounding the x value
            for i in range(1, len(self.jun_max_data)):
                x0, y0 = self.jun_max_data[i-1]
                x1, y1 = self.jun_max_data[i]
                
                if x0 <= x <= x1:  # x is between x0 and x1
                    return self._linear_interpolate(x0, y0, x1, y1, x)
        
        # If x is out of the bounds of the data points, return None or raise an error
        raise ValueError(f"No y for x: {x}")
    
    def _find_x_for_y_month(self, month_name, y):
        """
        Given a list of (x, y) tuples, find the corresponding x for a given y using linear interpolation.
        """
        if month_name == "jan":
            # Find the two points surrounding the y value
            for i in range(1, len(self.jan_min_data)):
                x0, y0 = self.jan_min_data[i-1]
                x1, y1 = self.jan_min_data[i]
                
                if y0 <= y <= y1:  # y is between y0 and y1
                    return self._linear_interpolate(y0, x0, y1, x1, y)
            
        else:
            # Find the two points surrounding the y value
            for i in range(1, len(self.jun_max_data)):
                x0, y0 = self.jun_max_data[i-1]
                x1, y1 = self.jun_max_data[i]
                
                if y0 <= y <= y1:  # y is between y0 and y1
                    return self._linear_interpolate(y0, x0, y1, x1, y)
        
        # If y is out of the bounds of the data points, return None or raise an error
        raise ValueError(f"No x for y: {y}")


    def _find_y_for_x(self, data, x):
        """
        Given a list of (x, y) tuples, find the corresponding y for a given x using linear interpolation.
        """
        
        # Find the two points surrounding the x value
        for i in range(1, len(data)):
            x0, y0 = data[i-1]
            x1, y1 = data[i]
            
            if x0 <= x <= x1:  # x is between x0 and x1
                return self._linear_interpolate(x0, y0, x1, y1, x)
        
        # If x is out of the bounds of the data points, return None or raise an error
        raise ValueError(f"No y for x: {x}")

    def _find_x_for_y(self, data, y):
        """
        Given a list of (x, y) tuples, find the corresponding x for a given y using linear interpolation.
        """
        # Find the two points surrounding the y value
        for i in range(1, len(data)):
            x0, y0 = data[i-1]
            x1, y1 = data[i]
            
            if y0 <= y <= y1:  # y is between y0 and y1
                return self._linear_interpolate(y0, x0, y1, x1, y)
        
        # If y is out of the bounds of the data points, return None or raise an error
        raise ValueError(f"No x for y: {y}")


    def get_soc(self) -> float:
        """Return the current State of Charge (SoC) in percentage."""
        return (self.energy_wh / self.capacity_wh) * 100

    def get_energy(self) -> float:
        """Return the remaining energy in Wh."""
        return self.energy_wh

    def get_voltage(self) -> float:
        """Return the battery voltage (constant for now)."""
        return self.voltage

