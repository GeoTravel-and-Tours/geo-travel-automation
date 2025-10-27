# src/utils/notifications.py

from email.mime import message
import os
import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.utils.logger import GeoLogger
from src.utils.html_templates import get_test_report_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NotificationManager:
    def __init__(self, project_name=None, environment=None):
        self.project_name = project_name or os.getenv("PROJECT_NAME", "Geo-Travel-Automation")
        self.environment = environment or os.getenv("ENVIRONMENT", "qa")
        self.logger = GeoLogger(name="NotificationManager")

    def get_slack_webhook_url(self):
        url = os.getenv("SLACK_WEBHOOK_URL")
        if not url:
            self.logger.error("SLACK_WEBHOOK_URL environment variable is missing!")
        return url

    def get_slack_channel(self):
        return os.getenv("SLACK_CHANNEL", "#geo-automation")
    
    def get_slack_token(self):
        return os.getenv("SLACK_BOT_TOKEN")

    def get_email_config(self):
        return {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", 587)),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "to_email": os.getenv("EMAIL_TO"),
        }


class SlackNotifier(NotificationManager):
    def __init__(self):
        super().__init__()

    def validate_notification_setup(self):
        """Check if notification system is properly configured"""
        webhook_url = self.get_slack_webhook_url()
        if not webhook_url:
            self.logger.error("Slack notifications disabled: SLACK_WEBHOOK_URL not set")
            return False

        # Test the webhook
        test_payload = {"text": "🔧 Test notification from automation framework"}
        try:
            response = requests.post(webhook_url, json=test_payload, timeout=5)
            if response.status_code == 200:
                self.logger.success("Slack notifications configured correctly")
                return True
            else:
                self.logger.error(f"Slack webhook test failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Slack webhook test error: {e}")
            return False

    def send_webhook_message(self, message, attachments=None):
        """Send message via Slack webhook with SDK fallback"""
        webhook_url = self.get_slack_webhook_url()

        # Try webhook first for better formatting
        if webhook_url:
            payload = {
                "text": message,
                "username": f"{self.project_name}-Bot",
                "icon_emoji": ":robot_face:",
            }
            if attachments:
                payload["attachments"] = attachments

            try:
                response = requests.post(
                    webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                self.logger.info(f"Slack webhook response: {response.status_code}")

                if response.status_code == 200:
                    return True
                else:
                    self.logger.warning(f"Webhook failed ({response.status_code}), falling back to SDK")
                    # Webhook failed, fall through to SDK

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Webhook request failed, falling back to SDK: {e}")
                # Fall through to SDK
            except Exception as e:
                self.logger.warning(f"Unexpected webhook error, falling back to SDK: {e}")
                # Fall through to SDK

        else:
            self.logger.info("Slack webhook URL not configured, using SDK")

        # Fallback to SDK if webhook fails or not configured
        return self.send_sdk_message(message)

    def send_sdk_message(self, message, channel=None):
        """Send message using Slack SDK"""
        token = self.get_slack_token()

        # Try SDK first
        if token:
            try:
                client = WebClient(token=token)
                channel = channel or self.get_slack_channel()

                response = client.chat_postMessage(
                    channel=channel, 
                    text=message, 
                    username=f"{self.project_name}-Bot",
                    icon_emoji=":robot_face:"
                )
                return response["ok"]
            except SlackApiError as e:
                self.logger.warning(f"Slack SDK failed, falling back to webhook: {e.response['error']}")

    def send_test_status(self, test_name, status, error_message=None, duration=None):
        """Send formatted test status message"""
        status_emoji = "✅" if status == "PASS" else "❌"
        message = f"{status_emoji} *{self.project_name}* - {self.environment}\n"
        message += f"*Test:* {test_name}\n"
        message += f"*Status:* {status}"

        if duration:
            message += f"\n*Duration:* {duration:.2f}s"

        if error_message and status != "PASS":
            message += f"\n*Error:* {error_message}"

        return self.send_sdk_message(message)


class EmailNotifier(NotificationManager):
    def __init__(self):
        super().__init__()

    def send_email(self, subject, body, html_body=None):
        """Send email notification"""
        config = self.get_email_config()

        if not all([config["username"], config["password"], config["to_email"]]):
            print("Email configuration incomplete")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = config["username"]
            msg["To"] = config["to_email"]
            msg["Subject"] = f"[{self.project_name}] {subject}"

            # Add body
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(config["smtp_server"], config["port"])
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
            server.quit()

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_test_report(self, test_name, status, details=None):
        """Send formatted test report email using template"""
        subject, plain_text, html_body = get_test_report_template(
            self.project_name, 
            self.environment, 
            test_name, 
            status, 
            details
        )
        return self.send_email(subject, plain_text, html_body)


# Global instances for easy access
slack_notifier = SlackNotifier()
email_notifier = EmailNotifier()
