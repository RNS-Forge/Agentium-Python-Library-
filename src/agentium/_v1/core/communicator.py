"""
Communicator Module - Send messages & notifications across platforms

This module provides communication capabilities for sending messages,
notifications, and alerts across various channels and platforms.
"""

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime

from ..utils.logger_utils import LoggerUtils


class ChannelType(Enum):
    """Types of communication channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    SMS = "sms"
    TELEGRAM = "telegram"
    CONSOLE = "console"
    FILE = "file"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CommunicationConfig:
    """Configuration for communication settings"""
    default_channel: ChannelType = ChannelType.CONSOLE
    retry_attempts: int = 3
    timeout_seconds: int = 30
    enable_logging: bool = True
    credentials: Dict[str, Any] = None


# Alias for consistent naming
CommunicatorConfig = CommunicationConfig


@dataclass
class Message:
    """Message structure"""
    content: str
    subject: Optional[str] = None
    recipients: List[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    attachments: List[str] = None
    metadata: Dict[str, Any] = None
    channel: Optional[ChannelType] = None


class Communicator:
    """
    Advanced communication system for multi-platform messaging.
    
    Features:
    - Multi-channel support (Email, Slack, Discord, Teams, etc.)
    - Message queuing and retry logic
    - Template-based messaging
    - Attachment support
    - Priority-based delivery
    - Delivery tracking and analytics
    """
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        self.config = config or CommunicationConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self.message_history = []
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup credentials from environment or config"""
        self.credentials = self.config.credentials or {}
        
        # Load from environment variables if not in config
        env_credentials = {
            'email_smtp_server': os.getenv('AGENTIUM_EMAIL_SMTP_SERVER'),
            'email_smtp_port': os.getenv('AGENTIUM_EMAIL_SMTP_PORT'),
            'email_username': os.getenv('AGENTIUM_EMAIL_USERNAME'),
            'email_password': os.getenv('AGENTIUM_EMAIL_PASSWORD'),
            'slack_webhook': os.getenv('AGENTIUM_SLACK_WEBHOOK'),
            'discord_webhook': os.getenv('AGENTIUM_DISCORD_WEBHOOK'),
            'teams_webhook': os.getenv('AGENTIUM_TEAMS_WEBHOOK'),
            'telegram_bot_token': os.getenv('AGENTIUM_TELEGRAM_BOT_TOKEN'),
            'telegram_chat_id': os.getenv('AGENTIUM_TELEGRAM_CHAT_ID'),
        }
        
        # Update credentials with environment variables
        for key, value in env_credentials.items():
            if value and key not in self.credentials:
                self.credentials[key] = value
    
    @LoggerUtils.log_operation("send_message")
    def send(self, message: Union[str, Message], channel: Optional[ChannelType] = None, **kwargs) -> Dict[str, Any]:
        """
        Send a message through specified channel
        
        Args:
            message: Message content or Message object
            channel: Communication channel to use
            **kwargs: Additional message parameters
            
        Returns:
            Delivery status and metadata
        """
        # Convert string to Message object
        if isinstance(message, str):
            message = Message(
                content=message,
                subject=kwargs.get('subject'),
                recipients=kwargs.get('recipients', []),
                priority=kwargs.get('priority', MessagePriority.NORMAL),
                attachments=kwargs.get('attachments', []),
                metadata=kwargs.get('metadata', {}),
                channel=channel
            )
        
        # Use default channel if not specified
        if not message.channel:
            message.channel = channel or self.config.default_channel
        
        self.logger.info(f"Sending message via {message.channel.value}")
        
        # Send message based on channel type
        try:
            if message.channel == ChannelType.EMAIL:
                result = self._send_email(message)
            elif message.channel == ChannelType.SLACK:
                result = self._send_slack(message)
            elif message.channel == ChannelType.DISCORD:
                result = self._send_discord(message)
            elif message.channel == ChannelType.TEAMS:
                result = self._send_teams(message)
            elif message.channel == ChannelType.WEBHOOK:
                result = self._send_webhook(message, kwargs.get('webhook_url'))
            elif message.channel == ChannelType.SMS:
                result = self._send_sms(message)
            elif message.channel == ChannelType.TELEGRAM:
                result = self._send_telegram(message)
            elif message.channel == ChannelType.CONSOLE:
                result = self._send_console(message)
            elif message.channel == ChannelType.FILE:
                result = self._send_file(message, kwargs.get('file_path', 'messages.log'))
            else:
                raise ValueError(f"Unsupported channel type: {message.channel}")
            
            # Log successful delivery
            self._log_message(message, result, True)
            return result
            
        except Exception as e:
            # Log failed delivery
            error_result = {'success': False, 'error': str(e), 'timestamp': datetime.now().isoformat()}
            self._log_message(message, error_result, False)
            
            # Retry if configured
            if self.config.retry_attempts > 0:
                return self._retry_send(message, kwargs)
            
            raise
    
    def _send_email(self, message: Message) -> Dict[str, Any]:
        """Send email message"""
        if not all(key in self.credentials for key in ['email_smtp_server', 'email_username', 'email_password']):
            raise ValueError("Email credentials not configured")
        
        smtp_server = self.credentials['email_smtp_server']
        smtp_port = int(self.credentials.get('email_smtp_port', 587))
        username = self.credentials['email_username']
        password = self.credentials['email_password']
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['Subject'] = message.subject or "Message from Agentium"
        
        if not message.recipients:
            raise ValueError("Email recipients not specified")
        
        msg['To'] = ', '.join(message.recipients)
        
        # Add body
        body = MIMEText(message.content, 'plain')
        msg.attach(body)
        
        # Add attachments
        if message.attachments:
            for file_path in message.attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            text = msg.as_string()
            server.sendmail(username, message.recipients, text)
        
        return {
            'success': True,
            'channel': 'email',
            'recipients': message.recipients,
            'message_id': msg['Message-ID'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_slack(self, message: Message) -> Dict[str, Any]:
        """Send Slack message"""
        webhook_url = self.credentials.get('slack_webhook')
        if not webhook_url:
            raise ValueError("Slack webhook URL not configured")
        
        payload = {
            'text': message.content,
            'username': 'Agentium Bot',
            'icon_emoji': ':robot_face:'
        }
        
        if message.subject:
            payload['text'] = f"*{message.subject}*\n{message.content}"
        
        # Add priority indicator
        if message.priority == MessagePriority.URGENT:
            payload['text'] = f":warning: URGENT :warning:\n{payload['text']}"
        elif message.priority == MessagePriority.HIGH:
            payload['text'] = f":exclamation: HIGH PRIORITY\n{payload['text']}"
        
        response = requests.post(webhook_url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        return {
            'success': True,
            'channel': 'slack',
            'response_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_discord(self, message: Message) -> Dict[str, Any]:
        """Send Discord message"""
        webhook_url = self.credentials.get('discord_webhook')
        if not webhook_url:
            raise ValueError("Discord webhook URL not configured")
        
        payload = {
            'content': message.content,
            'username': 'Agentium Bot'
        }
        
        if message.subject:
            payload['content'] = f"**{message.subject}**\n{message.content}"
        
        # Add priority indicator
        if message.priority == MessagePriority.URGENT:
            payload['content'] = f"🚨 **URGENT** 🚨\n{payload['content']}"
        elif message.priority == MessagePriority.HIGH:
            payload['content'] = f"❗ **HIGH PRIORITY**\n{payload['content']}"
        
        response = requests.post(webhook_url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        return {
            'success': True,
            'channel': 'discord',
            'response_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_teams(self, message: Message) -> Dict[str, Any]:
        """Send Microsoft Teams message"""
        webhook_url = self.credentials.get('teams_webhook')
        if not webhook_url:
            raise ValueError("Teams webhook URL not configured")
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "text": message.content
        }
        
        if message.subject:
            payload["summary"] = message.subject
            payload["title"] = message.subject
        
        # Add priority color
        if message.priority == MessagePriority.URGENT:
            payload["themeColor"] = "FF0000"  # Red
        elif message.priority == MessagePriority.HIGH:
            payload["themeColor"] = "FFA500"  # Orange
        else:
            payload["themeColor"] = "0078D4"  # Blue
        
        response = requests.post(webhook_url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        return {
            'success': True,
            'channel': 'teams',
            'response_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_webhook(self, message: Message, webhook_url: str) -> Dict[str, Any]:
        """Send generic webhook message"""
        if not webhook_url:
            raise ValueError("Webhook URL not specified")
        
        payload = {
            'content': message.content,
            'subject': message.subject,
            'priority': message.priority.value,
            'timestamp': datetime.now().isoformat(),
            'metadata': message.metadata or {}
        }
        
        response = requests.post(webhook_url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        return {
            'success': True,
            'channel': 'webhook',
            'webhook_url': webhook_url,
            'response_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_sms(self, message: Message) -> Dict[str, Any]:
        """Send SMS message (placeholder - requires SMS service integration)"""
        # This would require integration with SMS services like Twilio, AWS SNS, etc.
        self.logger.warning("SMS functionality not implemented - requires SMS service integration")
        
        return {
            'success': False,
            'channel': 'sms',
            'error': 'SMS service not configured',
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_telegram(self, message: Message) -> Dict[str, Any]:
        """Send Telegram message"""
        bot_token = self.credentials.get('telegram_bot_token')
        chat_id = self.credentials.get('telegram_chat_id')
        
        if not bot_token or not chat_id:
            raise ValueError("Telegram bot token and chat ID not configured")
        
        text = message.content
        if message.subject:
            text = f"*{message.subject}*\n{text}"
        
        # Add priority indicator
        if message.priority == MessagePriority.URGENT:
            text = f"🚨 *URGENT* 🚨\n{text}"
        elif message.priority == MessagePriority.HIGH:
            text = f"❗ *HIGH PRIORITY*\n{text}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        return {
            'success': True,
            'channel': 'telegram',
            'chat_id': chat_id,
            'response_status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_console(self, message: Message) -> Dict[str, Any]:
        """Send message to console"""
        output = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        if message.priority != MessagePriority.NORMAL:
            output += f" [{message.priority.value.upper()}]"
        
        if message.subject:
            output += f" {message.subject}:"
        
        output += f" {message.content}"
        
        print(output)
        
        return {
            'success': True,
            'channel': 'console',
            'timestamp': datetime.now().isoformat()
        }
    
    def _send_file(self, message: Message, file_path: str) -> Dict[str, Any]:
        """Send message to file"""
        output = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        if message.priority != MessagePriority.NORMAL:
            output += f" [{message.priority.value.upper()}]"
        
        if message.subject:
            output += f" {message.subject}:"
        
        output += f" {message.content}\n"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(output)
        
        return {
            'success': True,
            'channel': 'file',
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
    
    def _retry_send(self, message: Message, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Retry sending message with exponential backoff"""
        import time
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.info(f"Retry attempt {attempt + 1}/{self.config.retry_attempts}")
                time.sleep(2 ** attempt)  # Exponential backoff
                return self.send(message, **kwargs)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise e
                self.logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
        
        return {'success': False, 'error': 'All retry attempts failed'}
    
    def _log_message(self, message: Message, result: Dict[str, Any], success: bool):
        """Log message delivery"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'channel': message.channel.value,
            'priority': message.priority.value,
            'success': success,
            'result': result,
            'message_length': len(message.content),
            'has_subject': bool(message.subject),
            'has_attachments': bool(message.attachments),
            'recipients_count': len(message.recipients) if message.recipients else 0
        }
        
        self.message_history.append(log_entry)
        
        if self.config.enable_logging:
            if success:
                self.logger.info(f"Message delivered successfully via {message.channel.value}")
            else:
                self.logger.error(f"Message delivery failed via {message.channel.value}: {result.get('error')}")
    
    def send_notification(self, content: str, level: str = "info", **kwargs) -> Dict[str, Any]:
        """Send a notification with predefined formatting"""
        priority_map = {
            'debug': MessagePriority.LOW,
            'info': MessagePriority.NORMAL,
            'warning': MessagePriority.HIGH,
            'error': MessagePriority.URGENT,
            'critical': MessagePriority.URGENT
        }
        
        message = Message(
            content=content,
            subject=f"Agentium {level.title()} Notification",
            priority=priority_map.get(level.lower(), MessagePriority.NORMAL),
            **kwargs
        )
        
        return self.send(message, **kwargs)
    
    def send_bulk(self, messages: List[Union[str, Message]], channel: Optional[ChannelType] = None, **kwargs) -> List[Dict[str, Any]]:
        """Send multiple messages"""
        results = []
        
        for message in messages:
            try:
                result = self.send(message, channel, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get message delivery statistics"""
        if not self.message_history:
            return {'total_messages': 0}
        
        total = len(self.message_history)
        successful = sum(1 for entry in self.message_history if entry['success'])
        failed = total - successful
        
        channels = {}
        priorities = {}
        
        for entry in self.message_history:
            channel = entry['channel']
            priority = entry['priority']
            
            channels[channel] = channels.get(channel, 0) + 1
            priorities[priority] = priorities.get(priority, 0) + 1
        
        return {
            'total_messages': total,
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'channels_used': channels,
            'priority_distribution': priorities,
            'last_message_time': self.message_history[-1]['timestamp'] if self.message_history else None
        }
    
    def clear_history(self):
        """Clear message delivery history"""
        self.message_history.clear()
        self.logger.info("Message history cleared")
    
    def test_channel(self, channel: ChannelType) -> Dict[str, Any]:
        """Test a communication channel"""
        test_message = Message(
            content="This is a test message from Agentium",
            subject="Agentium Test Message",
            priority=MessagePriority.LOW
        )
        
        try:
            result = self.send(test_message, channel)
            return {
                'channel': channel.value,
                'test_result': 'success',
                'details': result
            }
        except Exception as e:
            return {
                'channel': channel.value,
                'test_result': 'failed',
                'error': str(e)
            }