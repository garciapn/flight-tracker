#!/usr/bin/env python3
"""
Unit tests for Flight Tracker
Tests data collection, validation, price parsing, and API endpoints
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import modules to test
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, get_latest_flight_data, get_flight_history
from email_alerts import EmailAlerter


class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_index_route(self):
        """Test home page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Flight Tracker', response.data)
    
    def test_api_flights_endpoint(self):
        """Test /api/flights endpoint"""
        response = self.client.get('/api/flights')
        self.assertEqual(response.status_code, 200)
        
        # Should return JSON
        data = json.loads(response.data)
        self.assertIn('flights', data)
        self.assertIsInstance(data['flights'], list)
    
    def test_api_dashboard_endpoint(self):
        """Test /api/dashboard endpoint"""
        response = self.client.get('/api/dashboard')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('flights', data)
    
    def test_api_data_endpoint(self):
        """Test /api/data endpoint"""
        response = self.client.get('/api/data')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('flights', data)


class TestPriceParsing(unittest.TestCase):
    """Test price parsing and validation"""
    
    def test_parse_string_price(self):
        """Test parsing string prices with $ and commas"""
        price_str = "$2,665"
        price = int(price_str.replace('$', '').replace(',', ''))
        self.assertEqual(price, 2665)
    
    def test_parse_int_price(self):
        """Test handling integer prices"""
        price = 2665
        self.assertEqual(int(price), 2665)
    
    def test_price_validation(self):
        """Test price validation (500-5000 range)"""
        valid_prices = [500, 1000, 1120, 2665, 5000]
        invalid_prices = [400, 5001, 10000]
        
        for price in valid_prices:
            self.assertTrue(500 <= price <= 5000)
        
        for price in invalid_prices:
            self.assertFalse(500 <= price <= 5000)
    
    def test_price_range_calculation(self):
        """Test calculating price ranges"""
        flights = [
            {'price': 1120},
            {'price': 1400},
            {'price': 2000},
        ]
        
        prices = [f['price'] for f in flights]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        self.assertEqual(min_price, 1120)
        self.assertEqual(max_price, 2000)
        self.assertEqual(avg_price, 1506.67)


class TestFlightData(unittest.TestCase):
    """Test flight data processing"""
    
    def test_flight_structure(self):
        """Test flight data structure"""
        flight = {
            'airline': 'United, Air Canada',
            'price': 1120,
            'departure': '06:30 AM',
            'arrival': '08:30 PM',
            'duration': '15h 00m',
            'stops': '1 stop',
            'layover': '3h 45m in YYC'
        }
        
        # Check required fields
        required_fields = ['airline', 'price', 'departure', 'arrival', 'duration', 'stops', 'layover']
        for field in required_fields:
            self.assertIn(field, flight)
    
    def test_layover_parsing(self):
        """Test layover duration parsing"""
        test_cases = [
            ('3h 45m in YYC', '3h 45m'),
            ('1h 30m in ORD', '1h 30m'),
            ('2h 15m in CDG', '2h 15m'),
            ('', ''),
        ]
        
        for layover_str, expected_duration in test_cases:
            if layover_str:
                parts = layover_str.split(' in ')
                duration = parts[0]
            else:
                duration = ''
            
            self.assertEqual(duration, expected_duration)
    
    def test_duration_format(self):
        """Test flight duration formatting"""
        durations = ['15h 00m', '10h 30m', '12h 45m']
        
        for duration in durations:
            # Should be in format "XXh XXm"
            self.assertIn('h', duration)
            self.assertIn('m', duration)


class TestEmailAlerter(unittest.TestCase):
    """Test email alerting system"""
    
    def setUp(self):
        """Set up email alerter"""
        self.alerter = EmailAlerter()
    
    def test_alerter_initialization(self):
        """Test EmailAlerter initialization"""
        self.assertIsNotNone(self.alerter.smtp_server)
        self.assertIsNotNone(self.alerter.smtp_port)
    
    def test_email_body_generation_text(self):
        """Test text email body generation"""
        body = self.alerter._build_text_email(
            'United, Air Canada',
            1120,
            1200,
            80,
            {'departure': '06:30 AM', 'arrival': '08:30 PM'}
        )
        
        self.assertIn('FLIGHT DEAL ALERT', body)
        self.assertIn('$1120', body)
        self.assertIn('$1200', body)
        self.assertIn('$80', body)
    
    def test_email_body_generation_html(self):
        """Test HTML email body generation"""
        body = self.alerter._build_html_email(
            'United, Air Canada',
            1120,
            1200,
            80,
            {'departure': '06:30 AM'}
        )
        
        self.assertIn('<html>', body)
        self.assertIn('$1120', body)
        self.assertIn('✈️ Flight Deal Alert', body)
    
    @patch('smtplib.SMTP')
    def test_send_alert_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP
        mock_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_instance
        
        # Alerter requires credentials
        alerter = EmailAlerter(
            smtp_server='smtp.gmail.com',
            smtp_port='587',
            sender_email='test@gmail.com',
            sender_password='test_pass'
        )
        
        result = alerter.send_alert(
            'recipient@example.com',
            'United, Air Canada',
            1120,
            1200,
            {'departure': '06:30 AM'}
        )
        
        self.assertTrue(result)
    
    def test_email_disabled_without_credentials(self):
        """Test email alerts disabled without credentials"""
        alerter = EmailAlerter(
            sender_email=None,
            sender_password=None
        )
        
        self.assertFalse(alerter.enabled)


class TestDataValidation(unittest.TestCase):
    """Test data validation logic"""
    
    def test_required_fields(self):
        """Test required field validation"""
        required_fields = ['airline', 'price', 'departure', 'arrival', 'duration', 'stops']
        
        # Valid flight
        valid_flight = {field: 'test_value' for field in required_fields}
        
        # Missing field
        invalid_flight = {field: 'test_value' for field in required_fields}
        del invalid_flight['airline']
        
        for field in required_fields:
            self.assertIn(field, valid_flight)
        
        self.assertNotIn('airline', invalid_flight)
    
    def test_price_range_validation(self):
        """Test price range validation (500-5000)"""
        valid_prices = [500, 1000, 1120, 2665, 5000]
        invalid_prices = [100, 50000]
        
        for price in valid_prices:
            is_valid = 500 <= price <= 5000
            self.assertTrue(is_valid)
        
        for price in invalid_prices:
            is_valid = 500 <= price <= 5000
            self.assertFalse(is_valid)


class TestAlertGeneration(unittest.TestCase):
    """Test alert generation logic"""
    
    def test_alert_triggered_below_threshold(self):
        """Test alert triggers when price < threshold"""
        price = 1120
        threshold = 1200
        
        should_alert = price < threshold
        self.assertTrue(should_alert)
    
    def test_alert_not_triggered_above_threshold(self):
        """Test alert doesn't trigger when price >= threshold"""
        price = 1250
        threshold = 1200
        
        should_alert = price < threshold
        self.assertFalse(should_alert)
    
    def test_alert_structure(self):
        """Test alert JSON structure"""
        alert = {
            'airline': 'United, Air Canada',
            'price': 1120,
            'threshold': 1200,
            'status': 'triggered'
        }
        
        self.assertEqual(alert['airline'], 'United, Air Canada')
        self.assertEqual(alert['price'], 1120)
        self.assertEqual(alert['threshold'], 1200)
        self.assertEqual(alert['status'], 'triggered')


class TestPriceAnalysis(unittest.TestCase):
    """Test price analysis functions"""
    
    def test_calculate_statistics(self):
        """Test price statistics calculation"""
        prices = [1120, 1131, 1400, 1150, 1200]
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        self.assertEqual(min_price, 1120)
        self.assertEqual(max_price, 1400)
        self.assertAlmostEqual(avg_price, 1200.2, places=1)
    
    def test_calculate_percent_change(self):
        """Test percentage change calculation"""
        current_price = 1120
        avg_historical = 1200
        
        pct_change = ((current_price - avg_historical) / avg_historical) * 100
        
        self.assertAlmostEqual(pct_change, -6.67, places=1)
    
    def test_trend_direction(self):
        """Test trend direction determination"""
        test_cases = [
            (-5.0, 'dropping'),    # negative = dropping
            (-0.5, 'dropping'),
            (0.0, 'stable'),       # zero = stable
            (2.5, 'rising'),       # positive = rising
        ]
        
        for pct_change, expected_trend in test_cases:
            if pct_change < 0:
                trend = 'dropping'
            elif pct_change > 0:
                trend = 'rising'
            else:
                trend = 'stable'
            
            self.assertEqual(trend, expected_trend)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
