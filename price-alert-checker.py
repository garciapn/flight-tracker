#!/usr/bin/env python3
"""
Price Alert Checker - PHASE 5
Detects price drops >5% from 7-day average.
Sends alerts to Telegram when drops detected.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class PriceAlertChecker:
    def __init__(self):
        self.repo_dir = Path(__file__).parent
        self.data_dir = self.repo_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.history_file = self.data_dir / "price-history.json"
        self.alerts_file = self.data_dir / "price-alerts.json"
        self.logs_dir = self.repo_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"price-alerts-{self.run_id}.log"
        
        self.threshold = 0.05  # 5% drop triggers alert
    
    def log(self, message: str, level: str = "INFO"):
        """Log message."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        print(log_line)
        
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
    
    def load_history(self) -> dict:
        """Load price history."""
        
        if not self.history_file.exists():
            return {
                "flights": {},
                "last_updated": None,
                "entries": []
            }
        
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.log(f"⚠️  Error loading history: {e}", level="WARN")
            return {
                "flights": {},
                "last_updated": None,
                "entries": []
            }
    
    def save_history(self, history: dict):
        """Save price history."""
        
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)
        
        self.log(f"💾 History saved: {self.history_file}")
    
    def load_current_prices(self) -> Optional[dict]:
        """Load the latest aggregated flight results."""
        
        # Find the most recent aggregated-flights.json
        try:
            agg_file = self.data_dir / "aggregated-flights.json"
            if agg_file.exists():
                with open(agg_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"⚠️  Error loading current prices: {e}", level="WARN")
        
        return None
    
    def update_history(self, current_prices: dict) -> dict:
        """Update price history with current data."""
        
        history = self.load_history()
        
        if not current_prices or "flights" not in current_prices:
            self.log("⚠️  No valid flight data to track", level="WARN")
            return history
        
        flights = current_prices.get("flights", [])
        stats = current_prices.get("stats", {})
        
        # Create entry for this check
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "min_price": stats.get("min_price", 0),
            "avg_price": stats.get("avg_price", 0),
            "max_price": stats.get("max_price", 0),
            "flights_found": len(flights)
        }
        
        # Add individual flight prices
        for flight in flights[:15]:
            flight_key = f"{flight.get('airline', 'unknown')}_{flight.get('departure', '')}".lower()
            
            if flight_key not in history["flights"]:
                history["flights"][flight_key] = {
                    "airline": flight.get("airline", "Unknown"),
                    "prices": []
                }
            
            history["flights"][flight_key]["prices"].append({
                "timestamp": entry["timestamp"],
                "price": flight.get("price", 0),
                "price_per_person": flight.get("price_per_person", 0)
            })
        
        # Keep only last 20 entries
        history["entries"].append(entry)
        history["entries"] = history["entries"][-20:]
        history["last_updated"] = entry["timestamp"]
        
        return history
    
    def detect_alerts(self, history: dict) -> List[dict]:
        """Detect price drops >5% from 7-day average."""
        
        alerts = []
        
        # Get current prices
        current = history.get("entries", [])
        if len(current) < 2:
            self.log("⚠️  Insufficient history for price comparison", level="WARN")
            return alerts
        
        current_entry = current[-1]
        current_min = current_entry.get("min_price", 0)
        
        # Calculate 7-day average (or all available if <7 days)
        cutoff_date = (datetime.fromisoformat(current_entry["timestamp"].replace("Z", "+00:00")) - timedelta(days=7)).isoformat()
        
        historical_entries = [e for e in current[:-1] if e.get("timestamp", "") >= cutoff_date]
        
        if not historical_entries:
            self.log("ℹ️  No historical data for comparison", level="INFO")
            return alerts
        
        historical_prices = [e.get("min_price", 0) for e in historical_entries]
        avg_7day = sum(historical_prices) / len(historical_prices) if historical_prices else 0
        
        if avg_7day == 0:
            return alerts
        
        # Check for drops
        drop_percent = (avg_7day - current_min) / avg_7day
        
        self.log(f"📊 Price Analysis:")
        self.log(f"   Current minimum: ${current_min}")
        self.log(f"   7-day average: ${avg_7day:.2f}")
        self.log(f"   Change: {drop_percent*100:.1f}%")
        
        if drop_percent >= self.threshold:
            alerts.append({
                "timestamp": current_entry["timestamp"],
                "type": "price_drop",
                "current_price": current_min,
                "previous_average": round(avg_7day, 2),
                "drop_percent": round(drop_percent * 100, 1),
                "savings": round(avg_7day - current_min, 2)
            })
            
            self.log(f"🎯 ALERT: Price drop detected! {drop_percent*100:.1f}% below 7-day average")
        
        return alerts
    
    def format_alert_message(self, alert: dict) -> str:
        """Format alert for Telegram."""
        
        message = "🚨 *FLIGHT PRICE ALERT*\n\n"
        message += "✈️ *Route:* SAN → ATH\n"
        message += "📅 *Dates:* June 12-22, 2026\n\n"
        
        message += "💰 *Price Drop Detected!*\n"
        message += f"• Current price: ${alert.get('current_price', 0)}/person\n"
        message += f"• 7-day average: ${alert.get('previous_average', 0)}/person\n"
        message += f"• Drop: *{alert.get('drop_percent', 0)}%*\n"
        message += f"• Savings: *${alert.get('savings', 0)}* per person\n\n"
        
        message += "🚀 *ACTION:* Check flights now!\n"
        message += "[Google Flights](https://www.google.com/flights?flt=SAN&to=ATH&depart_date=20260612&return_date=20260622&passengers=2)"
        
        return message
    
    def send_alert_to_telegram(self, message: str, chat_id: str = "5851420265") -> bool:
        """Send alert to Telegram."""
        
        try:
            import requests
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("JAMAL_BOT_TOKEN")
            
            if not bot_token:
                self.log("⚠️  No Telegram bot token configured", level="WARN")
                return False
            
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.log(f"✅ Alert sent to Telegram")
                return True
            else:
                self.log(f"❌ Telegram error: {response.status_code}", level="ERROR")
                return False
                
        except ImportError:
            self.log("⚠️  requests library not available", level="WARN")
            return False
        except Exception as e:
            self.log(f"❌ Send failed: {e}", level="ERROR")
            return False
    
    def save_alerts(self, alerts: List[dict]):
        """Save alerts to history."""
        
        existing_alerts = []
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, "r") as f:
                    existing_alerts = json.load(f)
            except:
                existing_alerts = []
        
        # Append new alerts
        existing_alerts.extend(alerts)
        
        # Keep last 100 alerts
        existing_alerts = existing_alerts[-100:]
        
        with open(self.alerts_file, "w") as f:
            json.dump(existing_alerts, f, indent=2)
        
        self.log(f"💾 Alerts saved: {self.alerts_file}")
    
    def run(self) -> bool:
        """Execute price alert check."""
        
        try:
            self.log("🔍 Starting price alert check...")
            
            # Load current prices
            current_prices = self.load_current_prices()
            
            if not current_prices:
                self.log("⚠️  No current price data available", level="WARN")
                return False
            
            # Update history
            history = self.update_history(current_prices)
            self.save_history(history)
            
            # Detect alerts
            alerts = self.detect_alerts(history)
            
            if alerts:
                self.log(f"🎯 Detected {len(alerts)} alert(s)")
                
                for alert in alerts:
                    # Format and send
                    message = self.format_alert_message(alert)
                    self.send_alert_to_telegram(message)
                
                # Save
                self.save_alerts(alerts)
            else:
                self.log("✅ No price drops detected")
            
            self.log("🎉 Price alert check complete!")
            return True
            
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", level="ERROR")
            return False


def main():
    """Main entry point."""
    
    checker = PriceAlertChecker()
    success = checker.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
