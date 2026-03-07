#!/usr/bin/env python3
"""
Webhook notifications for Slack and Discord
Send alerts to chat platforms
"""

import requests
import json
from datetime import datetime


class SlackWebhook:
    """Send alerts to Slack via webhooks"""
    
    def __init__(self, webhook_url=None):
        """
        Initialize Slack webhook
        
        Args:
            webhook_url: Slack webhook URL (or set SLACK_WEBHOOK_URL env var)
        """
        import os
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
    
    def send_alert(self, airline, price, threshold, flight_details=None):
        """
        Send Slack message alert
        
        Args:
            airline: Flight airline(s)
            price: Current price per person
            threshold: Alert threshold
            flight_details: Optional flight info dict
        
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            print("⚠️  Slack webhook not configured.")
            return False
        
        try:
            savings = threshold - price
            percent_savings = (savings / threshold) * 100
            
            # Build rich message
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "✈️ Flight Deal Alert!",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Airline:*\n{airline}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Price:*\n${price}/person"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Your Threshold:*\n${threshold}/person"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*You Save:*\n${savings} ({percent_savings:.1f}%)"
                            }
                        ]
                    }
                ]
            }
            
            # Add flight details if available
            if flight_details:
                detail_text = (
                    f"🛫 *Departure:* {flight_details.get('departure', 'N/A')}\n"
                    f"🛬 *Arrival:* {flight_details.get('arrival', 'N/A')}\n"
                    f"⏱️ *Duration:* {flight_details.get('duration', 'N/A')}\n"
                    f"🛑 *Stops:* {flight_details.get('stops', 'N/A')}\n"
                    f"🔄 *Layover:* {flight_details.get('layover', 'N/A')}"
                )
                
                payload["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": detail_text
                    }
                })
            
            payload["blocks"].append({
                "type": "divider"
            })
            
            payload["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_Book now before prices go back up!_"
                }
            })
            
            # Send
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            print(f"✅ Slack alert sent")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False


class DiscordWebhook:
    """Send alerts to Discord via webhooks"""
    
    def __init__(self, webhook_url=None):
        """
        Initialize Discord webhook
        
        Args:
            webhook_url: Discord webhook URL (or set DISCORD_WEBHOOK_URL env var)
        """
        import os
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
    
    def send_alert(self, airline, price, threshold, flight_details=None):
        """
        Send Discord message alert
        
        Args:
            airline: Flight airline(s)
            price: Current price per person
            threshold: Alert threshold
            flight_details: Optional flight info dict
        
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            print("⚠️  Discord webhook not configured.")
            return False
        
        try:
            savings = threshold - price
            percent_savings = (savings / threshold) * 100
            
            # Build embed
            embed = {
                "title": "✈️ Flight Deal Alert!",
                "description": f"Found a great deal on {airline}",
                "color": 0x667eea,  # Purple
                "fields": [
                    {
                        "name": "Price",
                        "value": f"${price}/person",
                        "inline": True
                    },
                    {
                        "name": "Your Threshold",
                        "value": f"${threshold}/person",
                        "inline": True
                    },
                    {
                        "name": "You Save",
                        "value": f"${savings} ({percent_savings:.1f}%)",
                        "inline": True
                    },
                    {
                        "name": "Airline",
                        "value": airline,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Flight Tracker | Book now before prices go back up!"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add flight details
            if flight_details:
                if flight_details.get('departure'):
                    embed["fields"].append({
                        "name": "Departure",
                        "value": flight_details['departure'],
                        "inline": True
                    })
                
                if flight_details.get('arrival'):
                    embed["fields"].append({
                        "name": "Arrival",
                        "value": flight_details['arrival'],
                        "inline": True
                    })
                
                if flight_details.get('duration'):
                    embed["fields"].append({
                        "name": "Duration",
                        "value": flight_details['duration'],
                        "inline": True
                    })
                
                if flight_details.get('layover'):
                    embed["fields"].append({
                        "name": "Layover",
                        "value": flight_details['layover'],
                        "inline": False
                    })
            
            payload = {"embeds": [embed]}
            
            # Send
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            print(f"✅ Discord alert sent")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send Discord alert: {e}")
            return False


def send_slack_alert(webhook_url, alert_data):
    """
    Convenience function to send Slack alert
    
    Args:
        webhook_url: Slack webhook URL
        alert_data: Dict with airline, price, threshold, flight_details
    """
    slack = SlackWebhook(webhook_url)
    return slack.send_alert(
        alert_data.get('airline', 'Unknown'),
        alert_data.get('price', 0),
        alert_data.get('threshold', 1200),
        alert_data.get('flight_details', {})
    )


def send_discord_alert(webhook_url, alert_data):
    """
    Convenience function to send Discord alert
    
    Args:
        webhook_url: Discord webhook URL
        alert_data: Dict with airline, price, threshold, flight_details
    """
    discord = DiscordWebhook(webhook_url)
    return discord.send_alert(
        alert_data.get('airline', 'Unknown'),
        alert_data.get('price', 0),
        alert_data.get('threshold', 1200),
        alert_data.get('flight_details', {})
    )


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    test_alert = {
        'airline': 'United, Air Canada',
        'price': 1120,
        'threshold': 1200,
        'flight_details': {
            'departure': '06:30 AM',
            'arrival': '08:30 PM +1',
            'duration': '15h 00m',
            'layover': '3h 45m in YYC'
        }
    }
    
    # Test Slack
    slack = SlackWebhook()
    slack.send_alert(
        test_alert['airline'],
        test_alert['price'],
        test_alert['threshold'],
        test_alert['flight_details']
    )
    
    # Test Discord
    discord = DiscordWebhook()
    discord.send_alert(
        test_alert['airline'],
        test_alert['price'],
        test_alert['threshold'],
        test_alert['flight_details']
    )
