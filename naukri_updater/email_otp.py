"""
Email OTP Reader for Naukri Login
Reads OTP from email using IMAP protocol.
"""

import imaplib
import email
import re
import time
import logging
from email.header import decode_header
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmailOTPReader:
    """Reads OTP from email inbox using IMAP."""
    
    # IMAP servers for common email providers
    IMAP_SERVERS = {
        'gmail.com': 'imap.gmail.com',
        'yahoo.com': 'imap.mail.yahoo.com',
        'outlook.com': 'imap-mail.outlook.com',
        'hotmail.com': 'imap-mail.outlook.com',
    }
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize the email reader.
        
        Args:
            email_address: Your email address
            app_password: App password (NOT your regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.mail = None
        
        # Determine IMAP server from email domain
        domain = email_address.split('@')[-1].lower()
        self.imap_server = self.IMAP_SERVERS.get(domain, f'imap.{domain}')
        
        logger.info(f"Email OTP Reader initialized for {email_address}")
        logger.info(f"Using IMAP server: {self.imap_server}")
    
    def connect(self) -> bool:
        """Connect to the email server."""
        try:
            logger.info(f"Connecting to {self.imap_server}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.app_password)
            logger.info("Successfully connected to email server")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP login failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to email: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the email server."""
        if self.mail:
            try:
                self.mail.logout()
                logger.info("Disconnected from email server")
            except:
                pass
    
    def _decode_email_subject(self, subject) -> str:
        """Decode email subject."""
        if subject is None:
            return ""
        decoded_parts = decode_header(subject)
        subject_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                subject_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                subject_str += part
        return subject_str
    
    def _get_email_body(self, msg) -> str:
        """Extract email body from message."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _extract_otp(self, text: str) -> str:
        """Extract 6-digit OTP from text."""
        # Common OTP patterns
        patterns = [
            r'OTP[:\s]+(\d{6})',           # OTP: 123456
            r'OTP\s+is\s+(\d{6})',          # OTP is 123456
            r'verification\s+code[:\s]+(\d{6})',  # verification code: 123456
            r'code[:\s]+(\d{6})',           # code: 123456
            r'\b(\d{6})\b',                 # Any 6-digit number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                otp = match.group(1)
                logger.info(f"Found OTP: {otp}")
                return otp
        
        return None
    
    def get_latest_otp(self, sender_filter: str = "naukri", max_age_minutes: int = 5) -> str:
        """
        Get the latest OTP from emails.
        
        Args:
            sender_filter: Filter emails by sender (e.g., 'naukri')
            max_age_minutes: Only consider emails from the last N minutes
            
        Returns:
            OTP string or None if not found
        """
        if not self.mail:
            if not self.connect():
                return None
        
        try:
            # Select inbox
            self.mail.select("INBOX")
            
            # Search for recent emails
            # Search by sender containing 'naukri'
            search_criteria = f'(FROM "{sender_filter}")'
            logger.info(f"Searching for emails with criteria: {search_criteria}")
            
            _, message_numbers = self.mail.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.warning(f"No emails found from {sender_filter}")
                return None
            
            # Get the latest emails (last 5)
            email_ids = message_numbers[0].split()[-5:]
            logger.info(f"Found {len(email_ids)} recent email(s) from {sender_filter}")
            
            # Check emails from newest to oldest
            for email_id in reversed(email_ids):
                _, msg_data = self.mail.fetch(email_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Get email date
                        date_str = msg.get("Date", "")
                        subject = self._decode_email_subject(msg.get("Subject", ""))
                        
                        logger.info(f"Checking email: {subject[:50]}...")
                        
                        # Get body and extract OTP
                        body = self._get_email_body(msg)
                        otp = self._extract_otp(body)
                        
                        if otp:
                            logger.info(f"Successfully extracted OTP: {otp}")
                            return otp
            
            logger.warning("No OTP found in recent emails")
            return None
            
        except Exception as e:
            logger.error(f"Error reading emails: {e}")
            return None
    
    def wait_for_otp(self, sender_filter: str = "naukri", 
                     timeout_seconds: int = 120,
                     poll_interval: int = 5) -> str:
        """
        Wait for OTP to arrive in email.
        
        Args:
            sender_filter: Filter emails by sender
            timeout_seconds: Maximum time to wait
            poll_interval: Seconds between checks
            
        Returns:
            OTP string or None if timeout
        """
        logger.info(f"Waiting for OTP email (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            otp = self.get_latest_otp(sender_filter)
            
            if otp:
                return otp
            
            # Wait before next check
            remaining = timeout_seconds - (time.time() - start_time)
            logger.info(f"OTP not found yet. Waiting... ({remaining:.0f}s remaining)")
            time.sleep(poll_interval)
        
        logger.error(f"Timeout waiting for OTP after {timeout_seconds} seconds")
        return None


def get_otp_from_email(email_address: str, app_password: str, 
                       timeout: int = 120) -> str:
    """
    Convenience function to get OTP from email.
    
    Args:
        email_address: Your email address
        app_password: App password for email
        timeout: Max seconds to wait for OTP
        
    Returns:
        OTP string or None
    """
    reader = EmailOTPReader(email_address, app_password)
    try:
        otp = reader.wait_for_otp(timeout_seconds=timeout)
        return otp
    finally:
        reader.disconnect()
