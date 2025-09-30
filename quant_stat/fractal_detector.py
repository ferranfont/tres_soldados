"""
Fractal Detector - Zigzag Method Only
Detects tops and bottoms in price data using percentage-based zigzag detection
"""

from enum import Enum
from typing import List, Optional


class FractalType(Enum):
    """Type of fractal point"""
    PEAK = "peak"      # Top/Maximum
    VALLEY = "valley"  # Bottom/Minimum


class FractalState(Enum):
    """State of fractal detection"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"


class ZigzagDirection(Enum):
    """Direction of zigzag trend"""
    UP = "up"      # Looking for peak
    DOWN = "down"  # Looking for valley


class Fractal:
    """Represents a detected fractal point (top or bottom)"""
    def __init__(self, index: int, price: float, fractal_type: FractalType, timestamp: Optional[str] = None):
        self.index = index
        self.price = price
        self.fractal_type = fractal_type
        self.state = FractalState.PENDING
        self.timestamp = timestamp


class ZigzagPoint:
    """Represents a zigzag pivot point"""
    def __init__(self, index: int, price: float, direction: ZigzagDirection, timestamp: Optional[str] = None):
        self.index = index
        self.price = price
        self.direction = direction
        self.timestamp = timestamp
        self.confirmed = False


class UnifiedZigzagDetector:
    """
    Zigzag detector that guarantees alternating peaks and valleys
    Based on percentage change detection
    """
    def __init__(self, min_change_pct: float = 0.15):
        """
        Initialize zigzag detector

        Args:
            min_change_pct: Minimum percentage change to detect a pivot (default 0.15%)
        """
        self.min_change_pct = min_change_pct / 100.0  # Convert to decimal

        # Detector state
        self.candles = []
        self.current_trend = None  # None, UP (looking for peak), DOWN (looking for valley)
        self.last_pivot = None  # Last confirmed pivot point

        # Tracking buffers
        self.current_high = None
        self.current_high_index = None
        self.current_high_time = None
        self.current_low = None
        self.current_low_index = None
        self.current_low_time = None

        # Detected zigzag points
        self.zigzag_points = []

    def add_candle(self, high: float, low: float, index: int, timestamp: str = None) -> Optional[ZigzagPoint]:
        """
        Add a new candle and return a zigzag point if detected

        Args:
            high: High price of the candle
            low: Low price of the candle
            index: Index/position of the candle
            timestamp: Optional timestamp string

        Returns:
            ZigzagPoint if a pivot is detected, None otherwise
        """
        candle = {
            'high': high,
            'low': low,
            'index': index,
            'timestamp': timestamp
        }
        self.candles.append(candle)

        # First candle - initialize
        if len(self.candles) == 1:
            self.current_high = high
            self.current_high_index = index
            self.current_high_time = timestamp
            self.current_low = low
            self.current_low_index = index
            self.current_low_time = timestamp
            return None

        # Second candle - determine initial trend
        if len(self.candles) == 2:
            if high > self.current_high:
                self.current_high = high
                self.current_high_index = index
                self.current_high_time = timestamp
            if low < self.current_low:
                self.current_low = low
                self.current_low_index = index
                self.current_low_time = timestamp

            # Establish initial trend based on which moved more
            high_change = (self.current_high - self.candles[0]['high']) / self.candles[0]['high']
            low_change = (self.candles[0]['low'] - self.current_low) / self.candles[0]['low']

            if high_change > low_change:
                self.current_trend = ZigzagDirection.UP  # Looking for peak
                # First point is a valley
                self.last_pivot = ZigzagPoint(
                    self.current_low_index,
                    self.current_low,
                    ZigzagDirection.DOWN,
                    self.current_low_time
                )
            else:
                self.current_trend = ZigzagDirection.DOWN  # Looking for valley
                # First point is a peak
                self.last_pivot = ZigzagPoint(
                    self.current_high_index,
                    self.current_high,
                    ZigzagDirection.UP,
                    self.current_high_time
                )
            return None

        return self._check_for_pivot(candle)

    def _check_for_pivot(self, candle: dict) -> Optional[ZigzagPoint]:
        """
        Check if current candle creates a pivot point

        Args:
            candle: Dictionary with candle data

        Returns:
            ZigzagPoint if pivot detected, None otherwise
        """
        high = candle['high']
        low = candle['low']
        index = candle['index']
        timestamp = candle['timestamp']

        # Update current extremes
        if high > self.current_high:
            self.current_high = high
            self.current_high_index = index
            self.current_high_time = timestamp
        if low < self.current_low:
            self.current_low = low
            self.current_low_index = index
            self.current_low_time = timestamp

        if not self.last_pivot:
            return None

        # If looking for a peak (uptrend)
        if self.current_trend == ZigzagDirection.UP:
            # Check for significant drop from current high
            if self.current_high > self.last_pivot.price:  # New high
                change_from_high = (self.current_high - low) / self.current_high
                if change_from_high >= self.min_change_pct:
                    # Confirm the peak
                    pivot = ZigzagPoint(
                        self.current_high_index,
                        self.current_high,
                        ZigzagDirection.UP,
                        self.current_high_time
                    )
                    pivot.confirmed = True
                    self.zigzag_points.append(pivot)
                    self.last_pivot = pivot
                    self.current_trend = ZigzagDirection.DOWN  # Now look for valley

                    # Reset tracking for next valley
                    self.current_low = low
                    self.current_low_index = index
                    self.current_low_time = timestamp

                    return pivot

        # If looking for a valley (downtrend)
        elif self.current_trend == ZigzagDirection.DOWN:
            # Check for significant rise from current low
            if self.current_low < self.last_pivot.price:  # New low
                change_from_low = (high - self.current_low) / self.current_low
                if change_from_low >= self.min_change_pct:
                    # Confirm the valley
                    pivot = ZigzagPoint(
                        self.current_low_index,
                        self.current_low,
                        ZigzagDirection.DOWN,
                        self.current_low_time
                    )
                    pivot.confirmed = True
                    self.zigzag_points.append(pivot)
                    self.last_pivot = pivot
                    self.current_trend = ZigzagDirection.UP  # Now look for peak

                    # Reset tracking for next peak
                    self.current_high = high
                    self.current_high_index = index
                    self.current_high_time = timestamp

                    return pivot

        return None

    def get_zigzag_points(self) -> List[ZigzagPoint]:
        """Return all detected zigzag points"""
        return self.zigzag_points.copy()

    def get_fractals(self) -> List[Fractal]:
        """Convert zigzag points to fractal format"""
        fractals = []
        for point in self.zigzag_points:
            fractal_type = FractalType.PEAK if point.direction == ZigzagDirection.UP else FractalType.VALLEY
            fractal = Fractal(point.index, point.price, fractal_type, point.timestamp)
            fractal.state = FractalState.CONFIRMED
            fractals.append(fractal)
        return fractals