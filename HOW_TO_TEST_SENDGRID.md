# How to Test SendGrid Email Functionality

## 🧪 **Method 1: Command Line Test (Simplest)**

Open your terminal/command prompt and run:

```bash
python test_email.py
```

This will send a test email to khangkong04@gmail.com and show you the results.

## 🧪 **Method 2: Django Shell Test**

1. **Start Django shell:**
   ```bash
   python manage.py shell
   ```

2. **Test individual functions:**
   ```python
   # Test basic email
   from utils.send_email import send_email
   send_email("your-email@gmail.com", "Test Subject", "<h2>Hello!</h2>")

   # Test welcome email
   from utils.send_email import send_welcome_email
   send_welcome_email("your-email@gmail.com", "John")

   # Test approval email
   from utils.send_email import send_approval_email
   send_approval_email("your-email@gmail.com", "John")

   # Test rejection email
   from utils.send_email import send_rejection_email
   send_rejection_email("your-email@gmail.com", "John")
   ```

## 🧪 **Method 3: Web Interface Test (Recommended)**

1. **Add this URL to registration/urls.py:**
   ```python
   path('test-email/', views.test_sendgrid_email, name='test_sendgrid_email'),
   ```

2. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

3. **Open browser and go to:**
   ```
   http://localhost:8000/registration/test-email/
   ```

4. **Send test email via web form**

## 🧪 **Method 4: Custom Python Script**

Create a file called `test_specific_email.py`:

```python
import os
import django
from pathlib import Path

# Setup
BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
django.setup()

from dotenv import load_dotenv
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

from utils.send_email import send_email

# Customize this email
test_email = "your-recipient@gmail.com"  # Change to any email
subject = "Custom Test Email"
content = """
<h2>Custom Email Test</h2>
<p>This is a test of your SendGrid integration.</p>
<p><strong>Timestamp:</strong> {}</p>
""".format("December 1, 2025")

# Send email
success = send_email(test_email, subject, content)

if success:
    print(f"✅ SUCCESS: Email sent to {test_email}")
else:
    print(f"❌ FAILED: Email to {test_email}")
```

Run with:
```bash
python test_specific_email.py
```

## 🧪 **Method 5: Test Different Email Types**

Create `test_all_emails.py`:

```python
import os
import django
from pathlib import Path

# Setup
BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
django.setup()

from dotenv import load_dotenv
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

from utils.send_email import (
    send_email, send_welcome_email, 
    send_approval_email, send_rejection_email
)

test_email = "your-email@gmail.com"  # Change this

# Test all email types
emails = [
    ("Basic Email", send_email, test_email, "Test Subject", "<h2>Basic Test</h2>"),
    ("Welcome Email", send_welcome_email, test_email, "John"),
    ("Approval Email", send_approval_email, test_email, "John"),
    ("Rejection Email", send_rejection_email, test_email, "John"),
]

print("Testing all email types...")
for name, func, *args in emails:
    try:
        result = func(*args)
        print(f"✅ {name}: {'SUCCESS' if result else 'FAILED'}")
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")

print("\nEmail testing complete!")
```

## 🔍 **What to Look For**

### ✅ Success Indicators:
- "SUCCESS: Email sent successfully!" message
- Email appears in your inbox (check spam folder too)
- Email has professional SkillBridge styling
- No error messages in console

### ❌ Failure Indicators:
- "FAILED: Email sending failed" message
- HTTP 403 errors (sender not verified)
- HTTP 401 errors (API key issues)
- Connection errors

## 📧 **Where to Check Emails**

1. **Primary inbox** of recipient email
2. **Spam/Junk folder** (emails sometimes go there)
3. **SendGrid Dashboard** (https://app.sendgrid.com) for delivery stats

## 🛠️ **Troubleshooting**

### If emails fail:
1. **Check API key:** Verify SENDGRID_API_KEY is correct in .env
2. **Check sender:** Verify EMAIL_SENDER is verified in SendGrid
3. **Check internet:** Ensure you have internet connection
4. **Check SendGrid dashboard:** Look for error logs

### If emails go to spam:
1. **Check SendGrid reputation**
2. **Verify sender domain**
3. **Add recipient to contacts**

## 🎯 **Quick Test Commands**

```bash
# Test basic functionality
python test_email.py

# Test specific email types
python manage.py shell -c "from utils.send_email import send_welcome_email; print('Welcome test:', send_welcome_email('your-email@gmail.com', 'TestUser'))"

# Check configuration
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', 'FOUND' if os.getenv('SENDGRID_API_KEY') else 'MISSING'); print('Sender:', os.getenv('EMAIL_SENDER'))"
```

Choose the method that works best for you! 🚀