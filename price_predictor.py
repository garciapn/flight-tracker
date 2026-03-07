#!/usr/bin/env python3
"""
Price prediction model for flight prices
Uses historical data to predict future prices
"""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path


class PricePredictor:
    """Predict flight prices using historical data"""
    
    def __init__(self):
        """Initialize predictor"""
        self.history_file = Path(os.path.expanduser('~/.flighttracker/price_history.json'))
        self.history = self._load_history()
    
    def _load_history(self):
        """Load historical price data"""
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return {}
    
    def _save_history(self):
        """Save historical price data"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_price(self, airline, price, date=None):
        """
        Add price observation
        
        Args:
            airline: Flight airline
            price: Price per person
            date: Date of observation (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if airline not in self.history:
            self.history[airline] = []
        
        self.history[airline].append({
            'price': price,
            'date': date,
            'timestamp': datetime.now().isoformat()
        })
        
        self._save_history()
    
    def predict(self, airline, days_ahead=7):
        """
        Predict price for airline days ahead
        
        Uses simple linear regression on historical data
        
        Args:
            airline: Flight airline
            days_ahead: Number of days to predict ahead
        
        Returns:
            dict with prediction, confidence, trend
        """
        if airline not in self.history or len(self.history[airline]) < 2:
            return {
                'prediction': None,
                'confidence': 0,
                'trend': 'insufficient_data',
                'message': 'Not enough historical data'
            }
        
        prices = self.history[airline]
        
        # Convert to numeric data
        try:
            x_vals = list(range(len(prices)))
            y_vals = [p['price'] for p in prices]
        except:
            return {
                'prediction': None,
                'confidence': 0,
                'trend': 'error',
                'message': 'Error parsing data'
            }
        
        # Simple linear regression
        n = len(x_vals)
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        
        numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return {
                'prediction': y_mean,
                'confidence': 0,
                'trend': 'stable',
                'message': 'No trend detected'
            }
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Predict
        x_pred = n - 1 + days_ahead
        y_pred = slope * x_pred + intercept
        
        # Calculate confidence (R-squared)
        ss_res = sum((y_vals[i] - (slope * x_vals[i] + intercept)) ** 2 for i in range(n))
        ss_tot = sum((y_vals[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend
        if slope < -10:
            trend = 'dropping'
        elif slope > 10:
            trend = 'rising'
        else:
            trend = 'stable'
        
        return {
            'airline': airline,
            'prediction': round(y_pred, 2),
            'confidence': round(r_squared * 100, 1),  # 0-100%
            'trend': trend,
            'slope': round(slope, 2),
            'days_ahead': days_ahead,
            'current_price': y_vals[-1],
            'expected_change': round(y_pred - y_vals[-1], 2),
            'data_points': n
        }
    
    def predict_multiple(self, airlines, days_ahead=7):
        """
        Predict prices for multiple airlines
        
        Args:
            airlines: List of airline names
            days_ahead: Days to predict ahead
        
        Returns:
            List of predictions
        """
        return [self.predict(airline, days_ahead) for airline in airlines]
    
    def get_price_range(self, airline):
        """
        Get price statistics for airline
        
        Args:
            airline: Flight airline
        
        Returns:
            dict with min, max, avg, trend
        """
        if airline not in self.history or not self.history[airline]:
            return None
        
        prices = [p['price'] for p in self.history[airline]]
        
        return {
            'airline': airline,
            'min': min(prices),
            'max': max(prices),
            'avg': round(sum(prices) / len(prices), 2),
            'current': prices[-1],
            'data_points': len(prices),
            'dates': [p['date'] for p in self.history[airline]]
        }
    
    def get_best_booking_date(self, airline, lead_days=30):
        """
        Analyze when to book (simple heuristic)
        
        Args:
            airline: Flight airline
            lead_days: How far ahead to look
        
        Returns:
            dict with recommendation
        """
        prediction = self.predict(airline, days_ahead=lead_days)
        
        if prediction['confidence'] < 30:
            return {
                'recommendation': 'book_soon',
                'reason': 'Insufficient data for prediction',
                'confidence': prediction['confidence']
            }
        
        current = prediction['current_price']
        predicted = prediction['prediction']
        trend = prediction['trend']
        
        if trend == 'dropping':
            return {
                'recommendation': 'wait',
                'reason': f'Prices dropping (trend: {trend}). Wait a few days.',
                'expected_savings': round(current - predicted, 2),
                'confidence': prediction['confidence']
            }
        elif trend == 'rising':
            return {
                'recommendation': 'book_now',
                'reason': f'Prices rising (trend: {trend}). Book ASAP.',
                'expected_cost_increase': round(predicted - current, 2),
                'confidence': prediction['confidence']
            }
        else:
            return {
                'recommendation': 'book_now',
                'reason': f'Prices stable. Good time to book.',
                'confidence': prediction['confidence']
            }


def predict_prices(airline, days_ahead=7):
    """Convenience function"""
    predictor = PricePredictor()
    return predictor.predict(airline, days_ahead)


if __name__ == '__main__':
    # Example usage
    predictor = PricePredictor()
    
    # Add sample data
    airlines = ['United, Air Canada', 'Delta, Lufthansa', 'Turkish Airlines']
    
    # Simulate price history (last 30 days)
    for days_ago in range(30, 0, -1):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        for airline in airlines:
            # Generate realistic price variations
            base_price = 1150
            trend = -5 * (30 - days_ago) / 30  # Downward trend
            noise = hash(f"{airline}{date}") % 100 - 50
            price = int(base_price + trend + noise)
            predictor.add_price(airline, price, date)
    
    # Make predictions
    print("\n📊 Price Predictions (7 days ahead):")
    for airline in airlines:
        pred = predictor.predict(airline, days_ahead=7)
        print(f"\n{airline}:")
        print(f"  Current: ${pred['current_price']}")
        print(f"  Predicted: ${pred['prediction']}")
        print(f"  Trend: {pred['trend']}")
        print(f"  Confidence: {pred['confidence']}%")
        
        # Booking recommendation
        booking = predictor.get_best_booking_date(airline)
        print(f"  Recommendation: {booking['recommendation']}")
        print(f"  Reason: {booking['reason']}")
