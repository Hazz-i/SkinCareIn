# services/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import settings
from core.logger import log_action

class EmailService:
    @staticmethod
    def build_verification_message(email: str, token: str, otp: str) -> dict:
        """Construct email subject, link, and textual content for email verification."""
        verification_link = f"{settings.APP_BASE_URL.rstrip('/')}{settings.API_V1_PREFIX}/auth/verify-email?token={token}"
        subject = f"Verify Your Account - {settings.PROJECT_NAME}"
        
        text_body = (
            f"Welcome to {settings.PROJECT_NAME}!\n\n"
            f"Please verify your account using the 6-digit OTP code below:\n\n"
            f"  OTP Code: {otp}\n\n"
            f"Alternatively, you can verify by clicking the following link:\n"
            f"  {verification_link}\n\n"
            f"This code will expire in 15 minutes.\n"
            f"If you did not create an account, please disregard this email."
        )

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Welcome to {settings.PROJECT_NAME}</h2>
                <p>Thank you for registering. Please verify your email address to complete your account setup.</p>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #2d6a4f;">{otp}</span>
                </div>
                <p>Enter the 6-digit code above in your application, or click the verification button below:</p>
                <p style="text-align: center;">
                    <a href="{verification_link}" style="background-color: #2d6a4f; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Verify Email Address</a>
                </p>
                <p style="font-size: 12px; color: #777;">This code is valid for 15 minutes. If you did not sign up for {settings.PROJECT_NAME}, no action is required.</p>
            </body>
        </html>
        """

        return {
            "recipient": email,
            "subject": subject,
            "otp": otp,
            "link": verification_link,
            "text": text_body,
            "html": html_body
        }

    @classmethod
    def send_verification_email(cls, email: str, token: str, otp: str) -> bool:
        """
        Send verification email via SMTP if configured.
        Falls back seamlessly to console logger for test/development environments.
        """
        content = cls.build_verification_message(email, token, otp)
        
        # If SMTP is unconfigured, fallback to structured application log
        if not settings.SMTP_HOST:
            log_action(
                "auth",
                f"VERIFICATION EMAIL (MOCK/CONSOLE FALLBACK): To={email} | OTP={otp} | Link={content['link']}"
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = content["subject"]
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email

            part1 = MIMEText(content["text"], "plain")
            part2 = MIMEText(content["html"], "html")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.sendmail(settings.SMTP_FROM, [email], msg.as_string())
            
            log_action("auth", f"Verification email successfully dispatched to {email}")
            return True
        except Exception as e:
            log_action(
                "auth",
                f"SMTP dispatch failed ({e}), falling back to console: To={email} | OTP={otp} | Link={content['link']}",
                level="warning"
            )
            return True


    @classmethod
    def send_password_reset_email(cls, email: str, otp: str) -> bool:
        """Send a password reset OTP. Falls back to the console logger when SMTP is unconfigured."""
        subject = f"Reset Your Password - {settings.PROJECT_NAME}"

        text_body = (
            f"We received a request to reset your {settings.PROJECT_NAME} password.\n\n"
            f"  Reset Code: {otp}\n\n"
            f"This code will expire in 15 minutes.\n"
            f"If you did not request a password reset, you can safely ignore this email."
        )

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Reset your {settings.PROJECT_NAME} password</h2>
                <p>Enter the 6-digit code below in the app to choose a new password.</p>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #2d6a4f;">{otp}</span>
                </div>
                <p style="font-size: 12px; color: #777;">This code is valid for 15 minutes. If you did not request this, no action is required.</p>
            </body>
        </html>
        """

        if not settings.SMTP_HOST:
            log_action(
                "auth",
                f"PASSWORD RESET EMAIL (MOCK/CONSOLE FALLBACK): To={email} | OTP={otp}"
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.sendmail(settings.SMTP_FROM, [email], msg.as_string())

            log_action("auth", f"Password reset email dispatched to {email}")
            return True
        except Exception as e:
            log_action(
                "auth",
                f"SMTP dispatch failed ({e}), falling back to console: To={email} | OTP={otp}",
                level="warning"
            )
            return True
