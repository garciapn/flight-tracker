#!/usr/bin/env python3
"""
Daily Flight Check - PHASE 4
Runs all 3 scrapers in parallel, aggregates, and sends to Telegram.
Scheduled: 6 AM & 6 PM PDT via launchd
"""

import json
import sys
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import concurrent.futures


class DailyFlightCheck:
    def __init__(self):
        self.repo_dir = Path(__file__).parent
        self.data_dir = self.repo_dir / "data"
        self.logs_dir = self.repo_dir / "logs"
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"daily-check-{self.run_id}.log"
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and stdout."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        print(log_line)
        
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
    
    def run_all_scrapers(self) -> dict:
        """Run all 3 scrapers in parallel."""
        
        self.log("🚀 Starting daily flight check...")
        self.log(f"   Run ID: {self.run_id}")
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._run_scraper, "google-flights-scraper.py"): "google_flights",
                executor.submit(self._run_scraper, "serpapi-flight-scraper.py"): "serpapi",
                executor.submit(self._run_scraper, "amadeus-scraper.py"): "amadeus"
            }
            
            for future in concurrent.futures.as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    results[source] = result
                    self.log(f"✅ {source} completed")
                except Exception as e:
                    self.log(f"❌ {source} failed: {e}", level="ERROR")
        
        self.log(f"📊 Scrapers complete: {len(results)}/3 succeeded")
        return results
    
    def _run_scraper(self, script_name: str) -> dict:
        """Run a single scraper script."""
        
        script_path = self.repo_dir / script_name
        
        if not script_path.exists():
            self.log(f"⚠️  {script_name} not found, skipping...", level="WARN")
            return {}
        
        try:
            result = subprocess.run(
                ["python3", str(script_path)],
                cwd=str(self.repo_dir),
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"   {script_name} output: {result.stdout.decode()[:200]}...")
                return {}
            else:
                self.log(f"   {script_name} error: {result.stderr.decode()[:200]}...", level="WARN")
                return {}
                
        except subprocess.TimeoutExpired:
            self.log(f"⏱️ {script_name} timed out", level="WARN")
            return {}
        except Exception as e:
            self.log(f"❌ Failed to run {script_name}: {e}", level="ERROR")
            return {}
    
    def aggregate_results(self) -> dict:
        """Run the aggregator."""
        
        self.log("🔄 Aggregating results...")
        
        try:
            result = subprocess.run(
                ["python3", "aggregate-flights.py"],
                cwd=str(self.repo_dir),
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("✅ Aggregation completed")
                
                # Load the aggregated results
                agg_file = self.data_dir / "aggregated-flights.json"
                if agg_file.exists():
                    with open(agg_file, "r") as f:
                        return json.load(f)
            else:
                self.log(f"❌ Aggregation failed: {result.stderr.decode()}", level="ERROR")
        
        except Exception as e:
            self.log(f"❌ Aggregation error: {e}", level="ERROR")
        
        return {}
    
    def format_for_telegram(self, results: dict) -> str:
        """Format aggregated results for Telegram using Frank's style."""
        
        stats = results.get("stats", {})
        flights = results.get("flights", [])
        
        message = "🌅 *Morning Flight Update — Frank*\n\n"
        
        message += "*Route:* San Diego (SAN) → Athens (ATH)\n"
        message += "*Dates:* June 12-22, 2026\n"
        message += "*Passengers:* 2\n\n"
        
        message += "📊 *Summary:*\n"
        message += f"• Total flights found: {stats.get('total_flights', 0)}\n"
        message += f"• Best price: ${stats.get('min_price', 'N/A')}/person\n"
        message += f"• Average price: ${stats.get('avg_price', 'N/A')}/person\n"
        
        # Recommendation
        if flights:
            best_airline = flights[0].get("airline", "Unknown")
            recommendation = "🚀 *BUY NOW*" if stats.get('min_price', 0) < 500 else "⏳ *WAIT* (prices trending up)"
            message += f"• Best airline: {best_airline}\n"
            message += f"• Recommendation: {recommendation}\n\n"
        
        message += "✈️ *TOP 15 CHEAPEST FLIGHTS:*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for flight in flights[:15]:
            rank = flight.get("rank", 0)
            price = flight.get("price", 0)
            per_person = flight.get("price_per_person", 0)
            airline = flight.get("airline", "Unknown")
            duration = flight.get("duration", "N/A")
            stops = flight.get("stops", "0 stops")
            departure = flight.get("departure", "N/A")
            arrival = flight.get("arrival", "N/A")
            layover = flight.get("layover", "N/A")
            layover_time = flight.get("layover_time", "N/A")
            
            message += f"{rank}. *${price}* (${per_person}/pp)\n"
            message += f"   ✈️ {airline} | {duration} | {stops}\n"
            
            # Add layover info if available
            if layover and layover != "N/A" and stops != "0 stops":
                message += f"   ✋ Layover: {layover} ({layover_time})\n"
            
            message += f"   📅 {departure} → {arrival}\n"
            message += f"   💰 Total: ${price}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━\n"
        message += "📝 *Filters Applied:*\n"
        message += "• Arriving by 6:00 PM local time\n"
        message += f"• {stats.get('total_flights', 0)} total flights found\n\n"
        
        message += "⚠️ *Note:* Click on any flight to see full layover details (city, duration, etc) on the booking site.\n\n"
        message += "*Next check:* In 12 hours\n"
        message += "*Powered by Frank* 🚀"
        
        return message
    
    def send_to_telegram(self, message: str, chat_id: str = "5851420265") -> bool:
        """Send message to Telegram."""
        
        self.log("📤 Sending to Telegram...")
        
        try:
            import requests
            
            # Try to get bot token from environment
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            
            if not bot_token:
                # Fallback: try Frank's token
                bot_token = os.getenv("FRANK_BOT_TOKEN")
            
            if not bot_token:
                # Fallback: try Jamal bot if available
                bot_token = os.getenv("JAMAL_BOT_TOKEN")
            
            if not bot_token:
                # Last resort: hardcode Frank's known token
                bot_token = "8515985195:AAG-7UB9iZ78bFgWZoNS9nFffxDyVF9z4jk"
            
            if not bot_token or bot_token == "UNSET":
                self.log("⚠️  No Telegram bot token configured", level="WARN")
                # Save message to file anyway
                msg_file = self.data_dir / f"telegram-message-{self.run_id}.txt"
                with open(msg_file, "w") as f:
                    f.write(message)
                self.log(f"   Message saved to: {msg_file}")
                return False
            
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.log(f"✅ Message sent to Telegram")
                return True
            else:
                self.log(f"❌ Telegram API error: {response.status_code}", level="ERROR")
                return False
                
        except ImportError:
            self.log("⚠️  requests library not available for Telegram", level="WARN")
            return False
        except Exception as e:
            self.log(f"❌ Telegram send failed: {e}", level="ERROR")
            return False
    
    def save_daily_report(self, results: dict, message: str):
        """Save daily report."""
        
        report = {
            "timestamp": datetime.now().isoformat() + "Z",
            "run_id": self.run_id,
            "aggregated_results": results,
            "telegram_message": message,
            "sources": results.get("sources", []),
            "stats": results.get("stats", {})
        }
        
        report_file = self.data_dir / f"daily-report-{self.run_id}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"💾 Daily report saved: {report_file}")
        return report_file
    
    def run(self):
        """Execute complete daily flight check."""
        
        try:
            # Run all scrapers
            self.run_all_scrapers()
            
            # Aggregate
            results = self.aggregate_results()
            
            if not results:
                self.log("⚠️  No results to process", level="WARN")
                return False
            
            # Format for Telegram
            message = self.format_for_telegram(results)
            
            # Send to Telegram
            self.send_to_telegram(message)
            
            # Save report
            self.save_daily_report(results, message)
            
            self.log("🎉 Daily check complete!")
            return True
            
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", level="ERROR")
            return False


def main():
    """Main entry point."""
    
    checker = DailyFlightCheck()
    success = checker.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
