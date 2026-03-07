#!/usr/bin/env python3
"""
Email alert system for Flight Tracker
Sends email notifications when prices drop below threshold
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailAlerter:
    """Send email alerts for flight price drops"""
    
    def __init__(self, smtp_server=None, smtp_port=None, sender_email=None, sender_password=None):
        """Initialize email alerter with SMTP credentials"""
        self.smtp_server = smtp_server or os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(smtp_port or os.getenv('EMAIL_SMTP_PORT', 587))
        self.sender_email = sender_email or os.getenv('EMAIL_SENDER')
        self.sender_password = sender_password or os.getenv('EMAIL_PASSWORD')
        self.enabled = bool(self.sender_email and self.sender_password)
    
    def send_alert(self, recipient_email, airline, price, threshold, flight_details=None):
        """
        Send price alert email
        
        Args:
            recipient_email: Email address to send to
            airline: Flight airline(s)
            price: Current price
            threshold: Alert threshold price
            flight_details: Optional dict with departure, arrival, stops, etc.
        
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            print("⚠️  Email alerts not configured. Set EMAIL_SENDER and EMAIL_PASSWORD.")
            return False
        
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"✈️ Flight Deal Alert: ${price}/person (Below ${threshold}!)"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Build email content
            savings = threshold - price
            text_body = self._build_text_email(airline, price, threshold, savings, flight_details)
            html_body = self._build_html_email(airline, price, threshold, savings, flight_details)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Email alert sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def _build_text_email(self, airline, price, threshold, savings, details):
        """Build plain text email body"""
        text = f"""✈️ FLIGHT DEAL ALERT

Great news! We found a flight below your threshold!

DEAL DETAILS:
- Airline: {airline}
- Price: ${price}/person
- Your Threshold: ${threshold}/person
- You Save: ${savings}/person

"""
        if details:
            text += "FLIGHT INFO:\n"
            text += f"- Departure: {details.get('departure', 'N/A')}\n"
            text += f"- Arrival: {details.get('arrival', 'N/A')}\n"
            text += f"- Duration: {details.get('duration', 'N/A')}\n"
            text += f"- Stops: {details.get('stops', 'N/A')}\n"
            text += f"- Layover: {details.get('layover', 'N/A')}\n\n"
        
        text += f"""Book now before prices go back up!

Flight Tracker
San Diego (SAN) ↔ Athens (ATH)
Powered by Amadeus API

---
Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return text
    
    def _build_html_email(self, airline, price, threshold, savings, details):
        """Build HTML email body"""
        html = f"""
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px;">
                        <h1 style="margin: 0; font-size: 28px;">✈️ Flight Deal Alert!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">Price below threshold</p>
                    </div>
                    
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 15px 0; color: #667eea;">Deal Details</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px 0; font-weight: bold;">Airline:</td>
                                <td style="padding: 10px 0;">{airline}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px 0; font-weight: bold;">Price:</td>
                                <td style="padding: 10px 0; color: #27ae60; font-size: 20px; font-weight: bold;">${price}/person</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px 0; font-weight: bold;">Your Threshold:</td>
                                <td style="padding: 10px 0;">${threshold}/person</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 0; font-weight: bold;">You Save:</td>
                                <td style="padding: 10px 0; color: #27ae60; font-weight: bold;">${savings}/person 🎉</td>
                            </tr>
                        </table>
                    </div>
        """
        
        if details:
            html += f"""
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 15px 0; color: #667eea;">Flight Information</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px 0; font-weight: bold;">Departure:</td>
                                <td style="padding: 8px 0;">{details.get('departure', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px 0; font-weight: bold;">Arrival:</td>
                                <td style="padding: 8px 0;">{details.get('arrival', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px 0; font-weight: bold;">Duration:</td>
                                <td style="padding: 8px 0;">{details.get('duration', 'N/A')}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 8px 0; font-weight: bold;">Stops:</td>
                                <td style="padding: 8px 0;">{details.get('stops', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Layover:</td>
                                <td style="padding: 8px 0;">{details.get('layover', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
            """
        
        html += f"""
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                        <p style="margin: 0; font-size: 16px; color: #27ae60;">
                            <strong>Book now before prices go back up!</strong>
                        </p>
                    </div>
                    
                    <div style="text-align: center; color: #888; font-size: 12px;">
                        <p>Flight Tracker | San Diego (SAN) ↔ Athens (ATH)</p>
                        <p>Powered by Amadeus API</p>
                        <p>Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html


def send_price_alert_email(alert_data, recipient_email):
    """
    Convenience function to send alert based on alert JSON
    
    Args:
        alert_data: Dict with keys: airline, price, threshold, flight_details (optional)
        recipient_email: Email to send to
    
    Returns:
        bool: Success status
    """
    alerter = EmailAlerter()
    return alerter.send_alert(
        recipient_email,
        alert_data.get('airline', 'Unknown'),
        alert_data.get('price', 0),
        alert_data.get('threshold', 1200),
        alert_data.get('flight_details', {})
    )


if __name__ == '__main__':
    # Test email sending
    from dotenv import load_dotenv
    load_dotenv()
    
    alerter = EmailAlerter()
    
    test_alert = {
        'airline': 'United, Air Canada',
        'price': 1120,
        'threshold': 1200,
        'flight_details': {
            'departure': '06:30 AM',
            'arrival': '08:30 PM +1',
            'duration': '15h 00m',
            'stops': '1 stop',
            'layover': '3h 45m in YYC'
        }
    }
    
    # Replace with your email
    alerter.send_alert(
        'your-email@example.com',
        test_alert['airline'],
        test_alert['price'],
        test_alert['threshold'],
        test_alert['flight_details']
    )
