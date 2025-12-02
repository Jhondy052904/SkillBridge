#!/usr/bin/env python
"""
Test script for SendGrid email functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
django.setup()

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

# Now import our email utilities
from utils.send_email import send_email

def main():
    """Test SendGrid email functionality"""
    print("=" * 50)
    print("SENDGRID EMAIL TEST")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('SENDGRID_API_KEY')
    sender_email = os.getenv('EMAIL_SENDER')
    
    print(f"SENDGRID_API_KEY: {'FOUND' if api_key else 'NOT FOUND'}")
    print(f"EMAIL_SENDER: {sender_email}")
    print()
    
    if not api_key:
        print("ERROR: SENDGRID_API_KEY not found in environment variables")
        print("Please check your .env file")
        return False
    
    if not sender_email:
        print("ERROR: EMAIL_SENDER not found in environment variables")
        print("Please check your .env file")
        return False
    
    # Test email
    test_email = "khangkong04@gmail.com"
    subject = "SkillBridge SendGrid Integration Test"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SendGrid Test</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SkillBridge</h1>
                <p>SendGrid Integration Test</p>
            </div>
            <div class="content">
                <h2>Email Test Successful!</h2>
                <p>This email confirms that SendGrid is properly configured for SkillBridge.</p>
                <p><strong>Configuration Status:</strong></p>
                <ul>
                    <li>SendGrid API Key: Configured</li>
                    <li>Email Sender: """ + sender_email + """</li>
                    <li>Email Service: Active</li>
                </ul>
                <p>The integration is working correctly!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    print(f"Sending test email to: {test_email}")
    print(f"Subject: {subject}")
    print()
    
    try:
        success = send_email(
            to_email=test_email,
            subject=subject,
            content=html_content,
            content_type='html'
        )
        
        if success:
            print("SUCCESS: Email sent successfully!")
            print(f"Check your inbox at {test_email}")
            return True
        else:
            print("FAILED: Email sending failed")
            print("Check the logs for more details")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)