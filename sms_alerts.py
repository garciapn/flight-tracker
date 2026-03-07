#!/usr/bin/env python3
"""
SMS alert system using Twilio
Send price drop alerts via SMS
"""

import os
from datetime import datetime

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class SMSAlerter:
    """Send SMS alerts for flight price drops"""
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number and TWILIO_AVAILABLE)
        
        if self.enabled:
            self.client = Client(self.account_sid, self.auth_token)
    
    def send_alert(self, phone_number, airline, price, threshold, flight_details=None):
        """
        Send SMS price alert
        
        Args:
            phone_number: Recipient phone number (E.164 format: +1234567890)
            airline: Flight airline(s)
            price: Current price per person
            threshold: Alert threshold
            flight_details: Optional dict with flight info
        
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            print("⚠️  SMS alerts not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER.")
            return False
        
        try:
            # Build message
            savings = threshold - price
            message = self._build_sms(airline, price, threshold, savings, flight_details)
            
            # Send
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            
            print(f"✅ SMS alert sent to {phone_number} (SID: {msg.sid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
            return False
    
    def _build_sms(self, airline, price, threshold, savings, details):
        """Build SMS message (160 chars for single SMS)"""
        message = f"✈️ FLIGHT DEAL! {airline}: ${price}/person (below ${threshold})! Save ${savings}. "
        
        if details and details.get('departure'):
            message += f"Departs {details['departure']}. "
        
        message += "Check it out now!"
        
        # Truncate to SMS limit if needed
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message


def send_sms_alert(phone_number, alert_data):
    """
    Convenience function to send SMS alert
    
    Args:
        phone_number: Phone number in E.164 format (+1234567890)
        alert_data: Dict with airline, price, threshold, flight_details
    
    Returns:
        bool: Success status
    """
    alerter = SMSAlerter()
    return alerter.send_alert(
        phone_number,
        alert_data.get('airline', 'Unknown'),
        alert_data.get('price', 0),
        alert_data.get('threshold', 1200),
        alert_data.get('flight_details', {})
    )


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    alerter = SMSAlerter()
    
    test_alert = {
        'airline': 'United, Air Canada',
        'price': 1120,
        'threshold': 1200,
        'flight_details': {
            'departure': '06:30 AM'
        }
    }
    
    # Replace with your phone number in E.164 format
    alerter.send_alert(
        '+15551234567',
        test_alert['airline'],
        test_alert['price'],
        test_alert['threshold'],
        test_alert['flight_details']
    )
