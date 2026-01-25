"""
Email service using Resend API.
Handles sending verification codes, password reset emails, etc.
"""
import os
import resend
from typing import Optional

# Configure Resend API key from environment
resend.api_key = os.getenv("RESEND_API_KEY")


def send_verification_email(to_email: str, verification_code: str, user_name: Optional[str] = None) -> bool:
    """
    Send a verification code email to a user.
    
    Args:
        to_email: Recipient email address
        verification_code: 6-digit verification code
        user_name: Optional user name for personalization
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not resend.api_key:
        print("RESEND_API_KEY not configured")
        return False
    
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">Email Verification</h2>
                <p>{greeting}</p>
                <p>Thank you for signing up! Please use the following verification code to complete your registration:</p>
                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #4F46E5; font-size: 32px; letter-spacing: 8px; margin: 0;">{verification_code}</h1>
                </div>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                <p style="font-size: 12px; color: #6B7280;">This is an automated message, please do not reply.</p>
            </div>
        </body>
    </html>
    """
    
    try:
        params = {
            "from": "VoiceTexta <noreply@voicetexta.com>",
            "to": [to_email],
            "subject": "Verify your email - VoiceTexta",
            "html": html_content,
        }
        
        resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(to_email: str, reset_code: str, user_name: Optional[str] = None) -> bool:
    """
    Send a password reset code email to a user.
    
    Args:
        to_email: Recipient email address
        reset_code: 6-digit reset code
        user_name: Optional user name for personalization
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not resend.api_key:
        print("RESEND_API_KEY not configured")
        return False
    
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">Password Reset</h2>
                <p>{greeting}</p>
                <p>We received a request to reset your password. Use the following code to reset your password:</p>
                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #4F46E5; font-size: 32px; letter-spacing: 8px; margin: 0;">{reset_code}</h1>
                </div>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                <p style="font-size: 12px; color: #6B7280;">This is an automated message, please do not reply.</p>
            </div>
        </body>
    </html>
    """
    
    try:
        params = {
            "from": "VoiceTexta <noreply@voicetexta.com>",
            "to": [to_email],
            "subject": "Reset your password - VoiceTexta",
            "html": html_content,
        }
        
        resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_welcome_email(to_email: str, user_name: str) -> bool:
    """
    Send a welcome email to a newly verified user.
    
    Args:
        to_email: Recipient email address
        user_name: User's name
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not resend.api_key:
        print("RESEND_API_KEY not configured")
        return False
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">Welcome to VoiceTexta! 🎉</h2>
                <p>Hello {user_name},</p>
                <p>Your email has been verified successfully! Welcome to VoiceTexta - your text-to-speech platform.</p>
                <p>You can now start using all our features:</p>
                <ul>
                    <li>Convert text to natural-sounding speech</li>
                    <li>Choose from multiple voice options</li>
                    <li>Download your audio files</li>
                </ul>
                <p>If you have any questions or need help getting started, feel free to reach out to our support team.</p>
                <p>Happy creating!</p>
                <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                <p style="font-size: 12px; color: #6B7280;">The VoiceTexta Team</p>
            </div>
        </body>
    </html>
    """
    
    try:
        params = {
            "from": "VoiceTexta <noreply@voicetexta.com>",
            "to": [to_email],
            "subject": "Welcome to VoiceTexta!",
            "html": html_content,
        }
        
        resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False
