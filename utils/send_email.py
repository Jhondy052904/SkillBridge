"""
Email utility module using SendGrid API for SkillBridge
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

def send_email(to_email, subject, content, content_type='html'):
    """
    Send email using SendGrid API
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        content (str): Email content (HTML or plain text)
        content_type (str): Content type ('html' or 'text')
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Get SendGrid API key from environment
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('EMAIL_SENDER')
    
    if not sendgrid_api_key:
        logger.error("SENDGRID_API_KEY not found in environment variables")
        return False
    
    if not from_email:
        logger.error("EMAIL_SENDER not found in environment variables")
        return False
    
    try:
        # Create SendGrid mail object
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject
        )
        
        # Add content
        if content_type.lower() == 'html':
            message.content = Content("text/html", content)
        else:
            message.content = Content("text/plain", content)
        
        # Initialize SendGrid client
        sg = SendGridAPIClient(sendgrid_api_key)
        
        # Send the email
        response = sg.send(message)
        
        # Log success
        logger.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
        return True
        
    except Exception as e:
        # Log error
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_email_template(to_email, subject, template_data):
    """
    Send email using a template
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        template_data (dict): Data to populate the template
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Create email content with template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{subject}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ background-color: #f1f1f1; padding: 10px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SkillBridge</h1>
                <p>Connecting Communities Through Skills</p>
            </div>
            <div class="content">
                {template_data.get('message', 'Hello!')}
                {f"<br><br><strong>Details:</strong><br>{template_data.get('details', '')}" if template_data.get('details') else ""}
            </div>
            <div class="footer">
                <p>This is an automated message from SkillBridge. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content, 'html')

def send_welcome_email(to_email, first_name=""):
    """
    Send welcome email to new users
    
    Args:
        to_email (str): Recipient email address
        first_name (str): User's first name
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    template_data = {
        'message': f"""
        <h2>Welcome to SkillBridge, {first_name}!</h2>
        <p>Thank you for joining SkillBridge. Your account has been created successfully.</p>
        <p>Your account is currently pending approval from a Barangay Official. You will receive another email once your account is approved.</p>
        <p>In the meantime, feel free to explore our platform and learn about available opportunities.</p>
        """,
        'details': f"Email: {to_email}"
    }
    
    return send_email_template(to_email, "Welcome to SkillBridge - Account Created", template_data)

def send_approval_email(to_email, first_name=""):
    """
    Send approval email to users whose accounts have been approved
    
    Args:
        to_email (str): Recipient email address
        first_name (str): User's first name
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    template_data = {
        'message': f"""
        <h2>Account Approved, {first_name}!</h2>
        <p>Great news! Your SkillBridge account has been approved by our Barangay Official.</p>
        <p>You can now log in to your account and start:</p>
        <ul>
            <li>Browsing job opportunities</li>
            <li>Registering for training programs</li>
            <li>Updating your profile and skills</li>
            <li>Connecting with other community members</li>
        </ul>
        <p>Welcome to SkillBridge!</p>
        """,
        'details': f"Email: {to_email}"
    }
    
    return send_email_template(to_email, "SkillBridge Account Approved", template_data)

def send_rejection_email(to_email, first_name=""):
    """
    Send rejection email to users whose accounts have been rejected

    Args:
        to_email (str): Recipient email address
        first_name (str): User's first name

    Returns:
        bool: True if email sent successfully, False otherwise
    """

    template_data = {
        'message': f"""
        <h2>SkillBridge Account Update</h2>
        <p>Hello {first_name},</p>
        <p>Thank you for your interest in SkillBridge. After reviewing your registration, we regret to inform you that your account application was not approved at this time.</p>
        <p>This could be due to several factors, and we encourage you to:</p>
        <ul>
            <li>Ensure all required information is provided accurately</li>
            <li>Provide valid proof of residency if needed</li>
            <li>Contact your Barangay Official for clarification</li>
        </ul>
        <p>If you have any questions or need assistance, please don't hesitate to reach out.</p>
        """,
        'details': f"Email: {to_email}"
    }

    return send_email_template(to_email, "SkillBridge Account Status Update", template_data)

def send_job_notification_email(to_email, job_title, job_description, job_link):
    """
    Send job notification email to residents

    Args:
        to_email (str): Recipient email address
        job_title (str): Job title
        job_description (str): Job description
        job_link (str): Link to job detail

    Returns:
        bool: True if email sent successfully, False otherwise
    """

    template_data = {
        'message': f"""
        <h2>New Job Opportunity Available!</h2>
        <p>A new job opportunity has been posted on SkillBridge:</p>
        <h3>{job_title}</h3>
        <p>{job_description[:200]}{'...' if len(job_description) > 200 else ''}</p>
        <p><a href="{job_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Job Details</a></p>
        """,
        'details': f"Job Link: {job_link}"
    }

    return send_email_template(to_email, f"New Job: {job_title}", template_data)

def send_training_notification_email(to_email, training_name, training_description, training_date, training_link):
    """
    Send training notification email to residents

    Args:
        to_email (str): Recipient email address
        training_name (str): Training name
        training_description (str): Training description
        training_date (str): Training date
        training_link (str): Link to training detail

    Returns:
        bool: True if email sent successfully, False otherwise
    """

    template_data = {
        'message': f"""
        <h2>New Training Opportunity Available!</h2>
        <p>A new training program has been posted on SkillBridge:</p>
        <h3>{training_name}</h3>
        <p><strong>Date:</strong> {training_date}</p>
        <p>{training_description[:200]}{'...' if len(training_description) > 200 else ''}</p>
        <p><a href="{training_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Training Details</a></p>
        """,
        'details': f"Training Link: {training_link}"
    }

    return send_email_template(to_email, f"New Training: {training_name}", template_data)

# Test function
def test_send_email():
    """
    Test function to verify SendGrid configuration
    """
    test_email = os.getenv('TEST_EMAIL', 'khangkong04@gmail.com')  # Default to your email for testing
    
    print(f"Sending test email to: {test_email}")
    
    success = send_email(
        to_email=test_email,
        subject="SkillBridge - SendGrid Test Email",
        content="""
        <h2>SendGrid Integration Test</h2>
        <p>This is a test email to verify that SendGrid is properly configured for SkillBridge.</p>
        <p>If you receive this email, the integration is working correctly!</p>
        <br>
        <p><strong>Configuration Details:</strong></p>
        <ul>
            <li>SendGrid API Key: Configured ✓</li>
            <li>Email Sender: """ + os.getenv('EMAIL_SENDER', 'Not set') + """ ✓</li>
            <li>Email Service: Active ✓</li>
        </ul>
        """,
        content_type='html'
    )
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email. Check logs for details.")
    
    return success

if __name__ == "__main__":
    # Run test if script is executed directly
    test_send_email()