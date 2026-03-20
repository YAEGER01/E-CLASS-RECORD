import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications to students and staff"""

    def __init__(self):
        # Email configuration - can be stored in environment variables or config
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sender_name = os.getenv(
            "SENDER_NAME", "E-Class Record System - ISU Cauayan"
        )

    def send_email(
        self, recipient_email: str, subject: str, html_body: str, text_body: str = ""
    ) -> bool:
        """
        Send an email notification

        Args:
            recipient_email: Email address of recipient
            subject: Email subject line
            html_body: HTML formatted email body
            text_body: Plain text version of email body (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            logger.warning(
                "Email credentials not configured. Skipping email notification."
            )
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email

            # Attach both plain text and HTML versions
            if text_body:
                part1 = MIMEText(text_body, "plain")
                message.attach(part1)

            part2 = MIMEText(html_body, "html")
            message.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False

    def send_registration_approval_email(
        self,
        student_email: str,
        student_name: str,
        school_id: str,
        course: str,
        year_level: int,
    ) -> bool:
        """Send email notification when student registration is approved"""
        subject = "✅ Your E-Class Record Account Has Been Approved!"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .success-badge {{ background: #10b981; color: white; padding: 10px 20px; 
                                 border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #667eea; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #667eea; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; 
                          border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 E-Class Record System</h1>
                    <p>Isabela State University - Cauayan Campus | CCSICT</p>
                </div>
                <div class="content">
                    <div class="success-badge">✅ Account Approved</div>
                    
                    <h2>Congratulations, {student_name}!</h2>
                    
                    <p>Your student account registration has been <strong>approved</strong> by the administrator.</p>
                    
                    <div class="info-box">
                        <h3>📋 Account Information</h3>
                        <div class="info-row">
                            <span class="label">School ID:</span> {school_id}
                        </div>
                        <div class="info-row">
                            <span class="label">Name:</span> {student_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Course:</span> {course}
                        </div>
                        <div class="info-row">
                            <span class="label">Year Level:</span> {year_level}
                        </div>
                    </div>
                    
                    <p><strong>You can now log in to your account!</strong></p>
                    
                   
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #666;">
                        If you have any questions or issues, please contact your department administrator.
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated message from E-Class Record System</p>
                    <p>Isabela State University - Cauayan Campus</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        E-Class Record System - Account Approved
        
        Congratulations, {student_name}!
        
        Your student account registration has been approved by the administrator.
        
        Account Information:
        - School ID: {school_id}
        - Name: {student_name}
        - Course: {course}
        - Year Level: {year_level}
        
        You can now log in to your account!
        
        If you have any questions or issues, please contact your department administrator.
        
        ---
        This is an automated message from E-Class Record System
        Isabela State University - Cauayan Campus
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_registration_confirmation_email(
        self,
        student_email: str,
        student_name: str,
        school_id: str,
        course: str,
        year_level: int,
    ) -> bool:
        """Send email confirmation when student submits registration (pending approval)"""
        subject = "📝 Registration Received - Pending Approval"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .pending-badge {{ background: #f59e0b; color: white; padding: 10px 20px; 
                                 border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #f59e0b; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #f59e0b; }}
                .timeline {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .step {{ padding: 10px 0; border-left: 3px solid #d1d5db; padding-left: 15px; margin-left: 10px; }}
                .step.active {{ border-color: #f59e0b; color: #f59e0b; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 E-Class Record System</h1>
                    <p>Isabela State University - Cauayan Campus | CCSICT</p>
                </div>
                <div class="content">
                    <div class="pending-badge">⏳ Registration Received</div>
                    
                    <h2>Thank You for Registering, {student_name}!</h2>
                    
                    <p style="font-size: 15px; color: #374151;">
                        We have successfully received your registration for the E-Class Record System. 
                        Your account is currently <strong>pending approval</strong> from the administrator.
                    </p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #1f2937;">📋 Registration Details</h3>
                        <div class="info-row">
                            <span class="label">School ID:</span> {school_id}
                        </div>
                        <div class="info-row">
                            <span class="label">Name:</span> {student_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Course:</span> {course}
                        </div>
                        <div class="info-row">
                            <span class="label">Year Level:</span> {year_level}
                        </div>
                        <div class="info-row">
                            <span class="label">Email:</span> {student_email}
                        </div>
                    </div>
                    
                    <div class="timeline">
                        <h3 style="margin-top: 0; color: #1f2937;">📍 What Happens Next?</h3>
                        <div class="step" style="border-color: #10b981; color: #10b981;">
                            <strong>✓ Step 1:</strong> Registration Submitted
                        </div>
                        <div class="step active">
                            <strong>⏳ Step 2:</strong> Awaiting Administrator Review (Current Stage)
                        </div>
                        <div class="step">
                            <strong>⏹ Step 3:</strong> Decision & Email Notification
                        </div>
                        <div class="step">
                            <strong>⏹ Step 4:</strong> Login Access (if approved)
                        </div>
                    </div>
                    
                    <div style="background: #dbeafe; border: 1px solid #3b82f6; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <p style="margin: 0; color: #1e40af; font-size: 14px;">
                            <strong>📧 Important:</strong> You will receive another email at this address 
                            (<strong>{student_email}</strong>) once the administrator reviews your registration. 
                            The email will inform you whether your account has been:
                        </p>
                        <ul style="margin: 10px 0 0 20px; color: #1e40af;">
                            <li><strong>✅ Approved</strong> - You can then log in to the system</li>
                            <li><strong>❌ Not Approved</strong> - With information about the decision</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 25px; font-size: 13px; color: #6b7280;">
                        Please be patient as the administrator reviews all registrations. 
                        If you have any urgent concerns, contact the CCSICT office.
                    </p>
                    
                    <p style="margin-top: 15px; font-size: 13px; color: #6b7280;">
                        <strong>Note:</strong> Please do not attempt to log in until you receive the approval notification email.
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated message from E-Class Record System</p>
                    <p>Isabela State University - Cauayan Campus</p>
                    <p style="margin-top: 10px; color: #9ca3af;">
                        If you did not register for this system, please contact the CCSICT office immediately.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        E-Class Record System - Registration Received
        
        Thank You for Registering, {student_name}!
        
        We have successfully received your registration for the E-Class Record System. 
        Your account is currently pending approval from the administrator.
        
        Registration Details:
        - School ID: {school_id}
        - Name: {student_name}
        - Course: {course}
        - Year Level: {year_level}
        - Email: {student_email}
        
        What Happens Next?
        1. ✓ Registration Submitted
        2. ⏳ Awaiting Administrator Review (Current Stage)
        3. Decision & Email Notification
        4. Login Access (if approved)
        
        📧 Important: You will receive another email at {student_email} once the administrator 
        reviews your registration. The email will inform you whether your account has been:
        - ✅ Approved - You can then log in to the system
        - ❌ Not Approved - With information about the decision
        
        Please be patient as the administrator reviews all registrations. 
        If you have any urgent concerns, contact the CCSICT office.
        
        Note: Please do not attempt to log in until you receive the approval notification email.
        
        ---
        This is an automated message from E-Class Record System
        Isabela State University - Cauayan Campus
        
        If you did not register for this system, please contact the CCSICT office immediately.
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_registration_rejection_email(
        self,
        student_email: str,
        student_name: str,
        school_id: str,
        rejection_reason: Optional[str] = None,
    ) -> bool:
        """Send email notification when student registration is rejected"""
        subject = "❌ Your E-Class Record Account Registration Update"

        reason_text = (
            f"<p><strong>Reason:</strong> {rejection_reason}</p>"
            if rejection_reason
            else ""
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .warning-badge {{ background: #ef4444; color: white; padding: 10px 20px; 
                                 border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #ef4444; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 E-Class Record System</h1>
                    <p>Isabela State University - Cauayan Campus | CCSICT</p>
                </div>
                <div class="content">
                    <div class="warning-badge">❌ Registration Not Approved</div>
                    
                    <h2>Dear {student_name},</h2>
                    
                    <p>We regret to inform you that your student account registration (School ID: <strong>{school_id}</strong>) 
                    was not approved by the administrator.</p>
                    
                    {reason_text}
                    
                    <div class="info-box">
                        <h3>📞 Next Steps</h3>
                        <p>Your registration has been removed from our system. You can:</p>
                        <ul>
                            <li>Review the rejection reason above (if provided)</li>
                            <li>Address any issues mentioned</li>
                            <li>Submit a new registration with correct information</li>
                            <li>Contact your department administrator for clarification</li>
                            <li>Email the CCSICT office at: ccsict@isu.edu.ph</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 14px; color: #10b981; font-weight: bold;">
                        ✓ You are welcome to register again after resolving any issues.
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated message from E-Class Record System</p>
                    <p>Isabela State University - Cauayan Campus</p>
                </div>
            </div>
        </body>
        </html>
        """

        reason_plain = f"\nReason: {rejection_reason}\n" if rejection_reason else "\n"

        text_body = f"""
        E-Class Record System - Registration Update
        
        Dear {student_name},
        
        We regret to inform you that your student account registration (School ID: {school_id}) 
        was not approved by the administrator.
        {reason_plain}
        Next Steps:
        Your registration has been removed from our system. You can:
        - Review the rejection reason above (if provided)
        - Address any issues mentioned
        - Submit a new registration with correct information
        - Contact your department administrator for clarification
        - Email the CCSICT office at: ccsict@isu.edu.ph
        
        ✓ You are welcome to register again after resolving any issues.
        
        ---
        This is an automated message from E-Class Record System
        Isabela State University - Cauayan Campus
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_grade_release_email(
        self,
        student_email: str,
        student_name: str,
        subject_name: str,
        course: str,
        section: str,
        final_grade: float,
        equivalent: str,
        instructor_name: str = None,
    ) -> bool:
        """Send email notification when instructor releases grades for a subject"""
        subject = f"📊 Your {subject_name} Grades Have Been Released!"

        # Determine grade status color and icon
        if equivalent in ["1.00", "1.25", "1.50", "1.75", "2.00"]:
            grade_color = "#10b981"  # Green for excellent
            grade_icon = "🌟"
        elif equivalent in ["2.25", "2.50", "2.75", "3.00"]:
            grade_color = "#3b82f6"  # Blue for good
            grade_icon = "✅"
        elif equivalent == "5.00":
            grade_color = "#ef4444"  # Red for failed
            grade_icon = "⚠️"
        else:
            grade_color = "#f59e0b"  # Orange for other
            grade_icon = "📊"

        instructor_text = (
            f"<p style='margin: 10px 0; color: #6b7280;'><strong>Instructor:</strong> {instructor_name}</p>"
            if instructor_name
            else ""
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .grade-badge {{ background: {grade_color}; color: white; padding: 20px; 
                               border-radius: 10px; text-align: center; margin: 20px 0; }}
                .grade-value {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
                .grade-label {{ font-size: 16px; opacity: 0.9; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #667eea; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #667eea; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; 
                          border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
                .icon {{ font-size: 48px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">{grade_icon}</div>
                    <h1 style="margin: 10px 0;">Grades Released</h1>
                    <p style="margin: 5px 0; opacity: 0.9;">Your final grades are now available</p>
                </div>
                <div class="content">
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px;">
                        Dear <strong>{student_name}</strong>,
                    </p>
                    <p style="margin: 0 0 20px 0; color: #555;">
                        Your instructor has released the final grades for <strong>{subject_name}</strong>.
                    </p>
                    
                    <div class="info-box">
                        <h3 style="margin: 0 0 15px 0; color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                            📚 Subject Information
                        </h3>
                        <div class="info-row">
                            <span class="label">Subject:</span> {subject_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Course & Section:</span> {course} - {section}
                        </div>
                        {instructor_text}
                    </div>

                    <div class="grade-badge">
                        <div class="grade-label">YOUR FINAL GRADE</div>
                        <div class="grade-value">{equivalent}</div>
                        <div class="grade-label">Numerical Grade: {final_grade:.2f}</div>
                    </div>

                    <div style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0;">
                        <p style="margin: 0; color: #92400e;">
                            <strong>📝 Note:</strong> This grade is now official and recorded in your class record. 
                            You can view your detailed grade breakdown by logging into the E-Class Record System.
                        </p>
                    </div>

                    

                    <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #e5e7eb;">
                        <p style="margin: 10px 0; color: #6b7280; font-size: 14px;">
                            <strong>💡 What's Next?</strong>
                        </p>
                        <ul style="color: #6b7280; font-size: 14px;">
                            <li>Review your detailed score breakdown in the student portal</li>
                            <li>Contact your instructor if you have any questions about your grade</li>
                            <li>Keep up the good work in your other subjects!</li>
                        </ul>
                    </div>

                    <div class="footer">
                        <p style="margin: 5px 0;">This is an automated notification from E-Class Record System</p>
                        <p style="margin: 5px 0;"><strong>Isabela State University - Cauayan Campus</strong></p>
                        <p style="margin: 5px 0;">College of Computing Studies, Information and Communication Technology</p>
                        <p style="margin: 5px 0;">📧 Email: ccsict@isu.edu.ph</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        E-Class Record System - Grade Release Notification
        
        Dear {student_name},
        
        Your instructor has released the final grades for {subject_name}.
        
        Subject Information:
        - Subject: {subject_name}
        - Course & Section: {course} - {section}
        {f"- Instructor: {instructor_name}" if instructor_name else ""}
        
        YOUR FINAL GRADE: {equivalent}
        Numerical Grade: {final_grade:.2f}
        
        This grade is now official and recorded in your class record.
        
        What's Next:
        - Log in to view your detailed grade breakdown
        - Contact your instructor if you have any questions
        - Keep up the good work in your other subjects!
        
        View your grades at the E-CLASS RECORD SYSTEM.
        
        ---
        This is an automated notification from E-Class Record System
        Isabela State University - Cauayan Campus
        College of Computing Studies, Information and Communication Technology
        Email: ccsict@isu.edu.ph
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_class_join_approval_email(
        self,
        student_email: str,
        student_name: str,
        class_name: str,
        subject_name: str,
        course: str,
        section: str,
        instructor_name: str = None,
    ) -> bool:
        """Send email notification when student's class join request is approved"""
        subject = f"✅ Your Request to Join {subject_name} Has Been Approved!"

        instructor_text = (
            f"<p style='margin: 10px 0; color: #6b7280;'><strong>Instructor:</strong> {instructor_name}</p>"
            if instructor_name
            else ""
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .success-badge {{ background: #10b981; color: white; padding: 15px 25px; 
                                 border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 16px; font-weight: bold; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #10b981; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #10b981; }}
                .button {{ background: #10b981; color: white; padding: 12px 30px; text-decoration: none; 
                          border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
                .icon {{ font-size: 48px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">✅</div>
                    <h1 style="margin: 10px 0;">Class Join Request Approved!</h1>
                    <p style="margin: 5px 0; opacity: 0.9;">Welcome to your new class</p>
                </div>
                <div class="content">
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px;">
                        Dear <strong>{student_name}</strong>,
                    </p>
                    <p style="margin: 0 0 20px 0; color: #555;">
                        Great news! Your request to join <strong>{subject_name}</strong> has been <strong style="color: #10b981;">approved</strong> by your instructor.
                    </p>
                    
                    <div class="success-badge">
                        🎉 You're now enrolled!
                    </div>

                    <div class="info-box">
                        <h3 style="margin: 0 0 15px 0; color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                            📚 Class Information
                        </h3>
                        <div class="info-row">
                            <span class="label">Subject:</span> {subject_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Class:</span> {class_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Course & Section:</span> {course} - {section}
                        </div>
                        {instructor_text}
                    </div>

                    <div style="background: #d1fae5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0;">
                        <p style="margin: 0; color: #065f46;">
                            <strong>🎓 What's Next?</strong> You can now access your class materials, view assignments, 
                            and participate in all class activities through the student portal.
                        </p>
                    </div>

                    

                    <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #e5e7eb;">
                        <p style="margin: 10px 0; color: #6b7280; font-size: 14px;">
                            <strong>💡 Quick Tips:</strong>
                        </p>
                        <ul style="color: #6b7280; font-size: 14px;">
                            <li>Check your class schedule and upcoming assessments</li>
                            <li>Review the class syllabus and requirements</li>
                            <li>Introduce yourself to your classmates and instructor</li>
                        </ul>
                    </div>

                    <div class="footer">
                        <p style="margin: 5px 0;">This is an automated notification from E-Class Record System</p>
                        <p style="margin: 5px 0;"><strong>Isabela State University - Cauayan Campus</strong></p>
                        <p style="margin: 5px 0;">College of Computing Studies, Information and Communication Technology</p>
                        <p style="margin: 5px 0;">📧 Email: ccsict@isu.edu.ph</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        E-Class Record System - Class Join Request Approved
        
        Dear {student_name},
        
        Great news! Your request to join {subject_name} has been approved by your instructor.
        
        🎉 You're now enrolled!
        
        Class Information:
        - Subject: {subject_name}
        - Class: {class_name}
        - Course & Section: {course} - {section}
        {f"- Instructor: {instructor_name}" if instructor_name else ""}
        
        What's Next:
        You can now access your class materials, view assignments, and participate in all class activities.
        
        Quick Tips:
        - Check your class schedule and upcoming assessments
        - Review the class syllabus and requirements
        - Introduce yourself to your classmates and instructor
        
        
        
        ---
        This is an automated notification from E-Class Record System
        Isabela State University - Cauayan Campus
        College of Computing Studies, Information and Communication Technology
        Email: ccsict@isu.edu.ph
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_class_join_rejection_email(
        self,
        student_email: str,
        student_name: str,
        class_name: str,
        subject_name: str,
        course: str,
        section: str,
        rejection_reason: str = None,
        instructor_name: str = None,
    ) -> bool:
        """Send email notification when student's class join request is rejected"""
        subject = f"❌ Your Request to Join {subject_name} Was Not Approved"

        instructor_text = (
            f"<p style='margin: 10px 0; color: #6b7280;'><strong>Instructor:</strong> {instructor_name}</p>"
            if instructor_name
            else ""
        )
        reason_html = (
            f"""
        <div style="background: #fee2e2; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 20px 0;">
            <p style="margin: 0; color: #991b1b;">
                <strong>📝 Reason:</strong> {rejection_reason}
            </p>
        </div>
        """
            if rejection_reason
            else ""
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; 
                            border-left: 4px solid #ef4444; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #ef4444; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; 
                          border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
                .icon {{ font-size: 48px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">❌</div>
                    <h1 style="margin: 10px 0;">Class Join Request Not Approved</h1>
                    <p style="margin: 5px 0; opacity: 0.9;">Your request needs attention</p>
                </div>
                <div class="content">
                    <p style="margin: 0 0 20px 0; color: #333; font-size: 16px;">
                        Dear <strong>{student_name}</strong>,
                    </p>
                    <p style="margin: 0 0 20px 0; color: #555;">
                        We regret to inform you that your request to join <strong>{subject_name}</strong> was not approved at this time.
                    </p>
                    
                    <div class="info-box">
                        <h3 style="margin: 0 0 15px 0; color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                            📚 Class Information
                        </h3>
                        <div class="info-row">
                            <span class="label">Subject:</span> {subject_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Class:</span> {class_name}
                        </div>
                        <div class="info-row">
                            <span class="label">Course & Section:</span> {course} - {section}
                        </div>
                        {instructor_text}
                    </div>

                    {reason_html}

                    <div style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0;">
                        <p style="margin: 0; color: #92400e;">
                            <strong>💡 What You Can Do:</strong>
                        </p>
                        <ul style="color: #92400e; margin: 10px 0; padding-left: 20px;">
                            <li>Contact your instructor for clarification</li>
                            <li>Verify you have the correct class code</li>
                            <li>Check if you meet the class prerequisites</li>
                            <li>You may try joining again if the issue is resolved</li>
                        </ul>
                    </div>

                   

                    <div class="footer">
                        <p style="margin: 5px 0;">This is an automated notification from E-Class Record System</p>
                        <p style="margin: 5px 0;"><strong>Isabela State University - Cauayan Campus</strong></p>
                        <p style="margin: 5px 0;">College of Computing Studies, Information and Communication Technology</p>
                        <p style="margin: 5px 0;">📧 Email: ccsict@isu.edu.ph</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        reason_text = f"\nReason: {rejection_reason}\n" if rejection_reason else "\n"

        text_body = f"""
        E-Class Record System - Class Join Request Not Approved
        
        Dear {student_name},
        
        We regret to inform you that your request to join {subject_name} was not approved at this time.
        
        Class Information:
        - Subject: {subject_name}
        - Class: {class_name}
        - Course & Section: {course} - {section}
        {f"- Instructor: {instructor_name}" if instructor_name else ""}
        {reason_text}
        What You Can Do:
        - Contact your instructor for clarification
        - Verify you have the correct class code
        - Check if you meet the class prerequisites
        - You may try joining again if the issue is resolved
        
        
        
        ---
        This is an automated notification from E-Class Record System
        Isabela State University - Cauayan Campus
        College of Computing Studies, Information and Communication Technology
        Email: ccsict@isu.edu.ph
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_password_reset_email(
        self, recipient_email: str, recipient_name: str, reset_link: str, role: str
    ) -> bool:
        """
        Send password reset email with reset link

        Args:
            recipient_email: Email address of the user
            recipient_name: Full name of the user
            reset_link: The password reset URL with token
            role: User role (student/instructor)

        Returns:
            bool: True if email sent successfully
        """
        subject = "🔐 Password Reset Request - E-Class Record"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">
                                        🔐 Password Reset Request
                                    </h1>
                                    <p style="margin: 10px 0 0 0; color: #f0f0f0; font-size: 14px;">
                                        E-Class Record System
                                    </p>
                                </td>
                            </tr>

                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="margin: 0 0 20px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                        Hello <strong>{recipient_name}</strong>,
                                    </p>
                                    
                                    <p style="margin: 0 0 20px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                        We received a request to reset the password for your <strong>{role}</strong> account in the E-Class Record System.
                                    </p>

                                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 6px; margin: 25px 0;">
                                        <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                            ⚠️ <strong>Important:</strong> This link will expire in <strong>1 hour</strong> for security reasons.
                                        </p>
                                    </div>

                                    <p style="margin: 0 0 25px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                        Click the button below to reset your password:
                                    </p>

                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center" style="padding: 10px 0;">
                                                <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.4);">
                                                    🔓 Reset My Password
                                                </a>
                                            </td>
                                        </tr>
                                    </table>

                                    <p style="margin: 25px 0 15px 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                        Or copy and paste this link into your browser:
                                    </p>
                                    <p style="margin: 0; padding: 12px; background: #f3f4f6; border-radius: 6px; word-break: break-all; font-size: 13px; color: #4b5563;">
                                        {reset_link}
                                    </p>

                                    <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; border-radius: 6px; margin: 25px 0;">
                                        <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px; font-weight: 600;">
                                            ❌ Didn't request this?
                                        </p>
                                        <p style="margin: 0; color: #991b1b; font-size: 14px; line-height: 1.5;">
                                            If you didn't request a password reset, please ignore this email. Your password will remain unchanged. Someone may have entered your email address by mistake.
                                        </p>
                                    </div>

                                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 25px;">
                                        <p style="margin: 0 0 10px 0; color: #374151; font-size: 14px; font-weight: 600;">
                                            🔒 Security Tips:
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #6b7280; font-size: 13px; line-height: 1.6;">
                                            <li>Never share your password with anyone</li>
                                            <li>Use a strong, unique password</li>
                                            <li>Don't use the same password for multiple accounts</li>
                                            <li>Consider using a password manager</li>
                                        </ul>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background: #f9fafb; padding: 25px 30px; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 12px; line-height: 1.5; text-align: center;">
                                        This is an automated email from E-Class Record System
                                    </p>
                                    <p style="margin: 0; color: #6b7280; font-size: 12px; line-height: 1.5; text-align: center;">
                                        <strong>Isabela State University - Cauayan Campus</strong><br>
                                        College of Computing Studies, Information and Communication Technology<br>
                                        Email: ccsict@isu.edu.ph
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        text_body = f"""
        Password Reset Request - E-Class Record System
        
        Hello {recipient_name},
        
        We received a request to reset the password for your {role} account.
        
        IMPORTANT: This link will expire in 1 hour for security reasons.
        
        Click the link below to reset your password:
        {reset_link}
        
        If you didn't request a password reset, please ignore this email.
        Your password will remain unchanged.
        
        Security Tips:
        - Never share your password with anyone
        - Use a strong, unique password
        - Don't use the same password for multiple accounts
        
        ---
        This is an automated notification from E-Class Record System
        Isabela State University - Cauayan Campus
        College of Computing Studies, Information and Communication Technology
        Email: ccsict@isu.edu.ph
        """

        return self.send_email(recipient_email, subject, html_body, text_body)


# Create a singleton instance
email_service = EmailNotificationService()
