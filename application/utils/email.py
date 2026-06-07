import resend
from application.core.config import settings

from pydantic import EmailStr

from application.utils.logger import collector_logger
from application.utils.time_ist import get_ist_now


class EmailService:
    @staticmethod
    def _send_email(to_email: EmailStr, subject: str, html_content: str):
        try:
            params: resend.Emails.SendParams = {
                "from": f"Pimenta Core <{settings.RESEND_FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            collector_logger.info(f"Email successfully sent to {to_email}. ID: {response.get('id')}")
        except Exception as e:
            collector_logger.error(f"Failed to send email to {to_email}: {e!s}")

    @classmethod
    def send_verification_email(cls, email_to: EmailStr, username: str, verification_url: str):
        """
        Sends a styled HTML verification email to the user using Resend SMTP server.
        """
        subject = "Verify your email address"

        # Premium styled HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background-color: #f4f5f6;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .wrapper {{
                    width: 100%;
                    background-color: #f4f5f6;
                    padding: 40px 0;
                }}
                .container {{
                    max-width: 580px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    padding: 40px 20px;
                    text-align: center;
                    color: #ffffff;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .content {{
                    padding: 40px 30px;
                    color: #374151;
                    line-height: 1.6;
                }}
                .content p {{
                    margin: 0 0 20px;
                    font-size: 16px;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    background-color: #4f46e5;
                    color: #ffffff !important;
                    text-decoration: none;
                    padding: 14px 30px;
                    font-size: 16px;
                    font-weight: 600;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(79, 70, 229, 0.15);
                    transition: background-color 0.2s;
                }}
                .button:hover {{
                    background-color: #4338ca;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 24px 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                }}
                .footer a {{
                    color: #4f46e5;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Auth Service</h1>
                    </div>
                    <div class="content">
                        <p>Hello {username},</p>
                        <p>Thank you for signing up. Please verify your email address to activate your account and gain access to your dashboard.</p>
                        <div class="button-container">
                            <a href="{verification_url}" class="button" target="_blank">Verify Email Address</a>
                        </div>
                        <p>If the button above doesn't work, copy and paste this URL into your browser:</p>
                        <p style="word-break: break-all; font-size: 14px; color: #6b7280;"><a href="{verification_url}">{verification_url}</a></p>
                        <p>This verification link will expire in 24 hours.</p>
                    </div>
                    <div class="footer">
                        <p>If you did not create an account, no further action is required.</p>
                        <p>&copy; {get_ist_now().year} Auth Service. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        cls._send_email(email_to, subject, html_content)

    @classmethod
    def send_password_reset_email(cls, email_to: EmailStr, username: str, reset_token: str):
        """
        Sends a styled HTML password reset email to the user.
        """
        subject = "Reset your password"

        # Premium styled HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background-color: #f4f5f6;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .wrapper {{
                    width: 100%;
                    background-color: #f4f5f6;
                    padding: 40px 0;
                }}
                .container {{
                    max-width: 580px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    padding: 40px 20px;
                    text-align: center;
                    color: #ffffff;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .content {{
                    padding: 40px 30px;
                    color: #374151;
                    line-height: 1.6;
                }}
                .content p {{
                    margin: 0 0 20px;
                    font-size: 16px;
                }}
                .token-box {{
                    background-color: #f3f4f6;
                    border: 1px dashed #d1d5db;
                    padding: 16px;
                    border-radius: 8px;
                    text-align: center;
                    font-family: monospace;
                    font-size: 18px;
                    font-weight: 600;
                    color: #111827;
                    word-break: break-all;
                    margin: 30px 0;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 24px 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #9ca3af;
                    border-top: 1px solid #f3f4f6;
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello {username},</p>
                        <p>We received a request to reset your password. Use the following token to proceed with resetting your password through the API:</p>

                        <div class="token-box">
                            {reset_token}
                        </div>

                        <p>This password reset token will expire in 15 minutes.</p>
                        <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {get_ist_now().year} Auth Service. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        cls._send_email(email_to, subject, html_content)
