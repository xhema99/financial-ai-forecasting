"""
Automatic alerting system for financial forecasting pipeline.
Integrates with Slack, Teams, Make, and Zapier.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages financial alerts and sends notifications through
    configured channels (Slack, Teams, Webhook).
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.alerts: list[dict] = []

    def _load_config(self, path: Optional[str]) -> dict:
        default = {
            "channels": {
                "slack": {"enabled": False, "webhook_url": ""},
                "teams": {"enabled": False, "webhook_url": ""},
                "webhook": {"enabled": False, "url": ""},
            },
            "thresholds": {
                "revenue_drop_pct": 15.0,
                "margin_min_pct": 25.0,
                "cash_risk_days": 45,
                "anomaly_min_score": 2.0,
            },
        }
        if path and Path(path).exists():
            with open(path) as f:
                user_config = json.load(f)
                default["channels"].update(user_config.get("channels", {}))
                default["thresholds"].update(user_config.get("thresholds", {}))
        return default

    def evaluate_risk(self, forecaster, monthly_df) -> list[dict]:
        alerts = []
        monthly = monthly_df.sort_values("ds")
        latest = monthly.iloc[-1]
        prev = monthly.iloc[-2]

        rev_change = (latest["Ingresos"] - prev["Ingresos"]) / prev["Ingresos"] * 100
        if rev_change < -self.config["thresholds"]["revenue_drop_pct"]:
            alerts.append({
                "type": "revenue_drop",
                "severity": "high",
                "message": (
                    f"Revenue dropped {rev_change:.1f}% MoM "
                    f"(€{prev['Ingresos']:,.0f} → €{latest['Ingresos']:,.0f})"
                ),
                "timestamp": datetime.now().isoformat(),
            })

        if latest["margen_pct"] < self.config["thresholds"]["margin_min_pct"]:
            alerts.append({
                "type": "margin_warning",
                "severity": "warning",
                "message": (
                    f"Gross margin at {latest['margen_pct']:.1f}% "
                    f"(below {self.config['thresholds']['margin_min_pct']}% threshold)"
                ),
                "timestamp": datetime.now().isoformat(),
            })

        if forecaster and forecaster.forecast is not None:
            future = forecaster.forecast[
                forecaster.forecast["ds"] > monthly["ds"].max()
            ]
            if not future.empty:
                min_revenue = future["yhat_lower"].min()
                avg_revenue = monthly["Ingresos"].mean()
                if min_revenue < avg_revenue * 0.7:
                    alerts.append({
                        "type": "cash_risk",
                        "severity": "critical",
                        "message": (
                            f"Cash risk: projected revenue could drop to "
                            f"€{min_revenue:,.0f} (70% of avg €{avg_revenue:,.0f})"
                        ),
                        "timestamp": datetime.now().isoformat(),
                    })

        self.alerts = alerts
        return alerts

    def send_slack(self, message: str) -> bool:
        if not self.config["channels"]["slack"]["enabled"]:
            logger.info("Slack disabled — would send: %s", message[:80])
            return False
        import requests
        payload = {"text": message}
        try:
            resp = requests.post(
                self.config["channels"]["slack"]["webhook_url"],
                json=payload, timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error("Slack send failed: %s", e)
            return False

    def send_teams(self, message: str) -> bool:
        if not self.config["channels"]["teams"]["enabled"]:
            logger.info("Teams disabled — would send: %s", message[:80])
            return False
        import requests
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Financial Alert",
            "title": "🚨 Financial AI Alert",
            "text": message,
        }
        try:
            resp = requests.post(
                self.config["channels"]["teams"]["webhook_url"],
                json=payload, timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error("Teams send failed: %s", e)
            return False

    def send_webhook(self, payload: dict) -> bool:
        if not self.config["channels"]["webhook"]["enabled"]:
            logger.info("Webhook disabled — would send payload")
            return False
        import requests
        try:
            resp = requests.post(
                self.config["channels"]["webhook"]["url"],
                json=payload, timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error("Webhook send failed: %s", e)
            return False

    def notify_all(self) -> list[dict]:
        if not self.alerts:
            logger.info("No alerts to send")
            return []

        results = []
        for alert in self.alerts:
            msg = (
                f"[{alert['severity'].upper()}] {alert['message']}\n"
                f"Timestamp: {alert['timestamp']}"
            )
            slack_ok = self.send_slack(msg)
            teams_ok = self.send_teams(msg)
            webhook_ok = self.send_webhook(alert)
            results.append({
                "alert": alert["type"],
                "slack": slack_ok,
                "teams": teams_ok,
                "webhook": webhook_ok,
            })
        return results

    def generate_alert_report(self, path: str = "reports/alerts.json"):
        report = {
            "generated_at": datetime.now().isoformat(),
            "thresholds": self.config["thresholds"],
            "alerts": self.alerts,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        return path

    def get_integration_guide(self) -> str:
        return """
## Automation Integration Guide

### Slack
1. Create a Slack Webhook: https://api.slack.com/messaging/webhooks
2. Set `SLACK_WEBHOOK_URL` in `.env`
3. Enable in config: `alert_manager.config['channels']['slack']['enabled'] = True`

### Microsoft Teams
1. Create an Incoming Webhook in Teams channel
2. Set `TEAMS_WEBHOOK_URL` in `.env`
3. Enable in config

### Make.com (formerly Integromat)
Webhook URL receives JSON payload:
```json
{
  "type": "revenue_drop|cash_risk|margin_warning",
  "severity": "low|warning|high|critical",
  "message": "...",
  "timestamp": "2025-01-01T00:00:00"
}
```

### Zapier
Use Webhook trigger → Catch Hook → then route to:
- Google Sheets (log)
- Email (critical only)
- Slack (all alerts)

### Scheduling (Cron / Task Scheduler)
Run daily:
```bash
# Linux/Mac (crontab)
0 8 * * 1-5 cd /path/to/project && python main.py

# Windows (Task Scheduler)
schtasks /create /tn "KeedioFinancialAI" /tr "python main.py" /sc daily /st 08:00
```
"""
