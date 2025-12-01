# Email Migration Guide - Replace Gmail with SendGrid

## 🎯 Quick Migration Steps

Your SendGrid integration is now **fully working**! Here's how to update your existing email calls:

## 📝 Find and Replace Email Calls

Search your codebase for these old Django email calls and replace them:

### 1. Registration/Signup Email (registration/views.py)

**Find this code around line 502:**
```python
email_content = f\"\"\"
<p>Hello!</p>
<p>Thank you for signing up for <strong>SkillBridge</strong>.</p>
<p>Please verify your email address using the confirmation link sent to your inbox.</p>
<p>Once verified, your Barangay Official will review your registration.</p>
<p>You will receive another email once your account is approved.</p>
<br>

email_sent = send_email(
    to_email=email,
    subject="SkillBridge Registration - Awaiting Approval",
    content=email_content
)
```

**Replace with:**
```python
from utils.send_email import send_welcome_email

email_sent = send_welcome_email(email, first_name)
```

### 2. Account Approval Email (registration/views.py)

**Find this code around line 1158:**
```python
send_mail(
    subject="SkillBridge Account Approved",
    message="Your SkillBridge account has been approved! You can now log in and start exploring job opportunities and training programs.",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[resident_email],
    fail_silently=True,
)
```

**Replace with:**
```python
from utils.send_email import send_approval_email

send_approval_email(resident_email, first_name="User")
```

### 3. Account Rejection Email (registration/views.py)

**Find this code around line 1189:**
```python
send_mail(
    subject="SkillBridge Account Verification Result",
    message="Thank you for your interest in SkillBridge. After review, we regret to inform you that your account was not approved at this time.",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[resident_email],
    fail_silently=True,
)
```

**Replace with:**
```python
from utils.send_email import send_rejection_email

send_rejection_email(resident_email, first_name="User")
```

## 🔧 Import Statements

Add these imports at the top of your views.py files that use email functions:

```python
from utils.send_email import (
    send_email,
    send_welcome_email,
    send_approval_email,
    send_rejection_email,
    send_email_template
)
```

## 📧 Available Email Functions

### Basic Email
```python
send_email(
    to_email="user@example.com",
    subject="Subject Line",
    content="<p>HTML content here</p>",
    content_type="html"  # or "text"
)
```

### Welcome Email (for new registrations)
```python
send_welcome_email("user@example.com", "John")
```

### Approval Email (for approved accounts)
```python
send_approval_email("user@example.com", "John")
```

### Rejection Email (for rejected accounts)
```python
send_rejection_email("user@example.com", "John")
```

### Template Email (custom branded emails)
```python
template_data = {
    'message': '<p>Your custom message</p>',
    'details': 'Additional details here'
}
send_email_template("user@example.com", "Subject", template_data)
```

## ✅ Benefits of New Email System

1. **Professional Templates** - Branded HTML emails with SkillBridge styling
2. **Better Deliverability** - SendGrid's professional email service
3. **Tracking** - Click and open tracking enabled
4. **Error Handling** - Comprehensive logging and error handling
5. **Consistency** - Standardized email templates across the application

## 🧪 Testing

After making changes, test with:
```python
python test_email.py
```

Or use the Django test view:
```
POST /registration/test-email/
```

## 🚀 Ready to Deploy!

Your SendGrid integration is production-ready. Simply replace the old email calls with the new functions and you're all set!

---

**Need help?** Check `SENDGRID_INTEGRATION_SUMMARY.md` for detailed documentation.