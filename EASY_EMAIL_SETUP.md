# Easy Email Setup Guide

Here are much simpler ways to integrate your email without complex OAuth setup:

## Option 1: IMAP Access (Recommended) ✅

Most email providers support IMAP, which only requires your email and password.

### Gmail Setup

1. **Enable 2-Factor Authentication** (if not already enabled)
   - Go to https://myaccount.google.com/security
   - Turn on 2-Step Verification

2. **Generate an App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Add to .env file:**
   ```env
   EMAIL_ADDRESS=your.email@gmail.com
   EMAIL_PASSWORD=your-16-char-app-password
   EMAIL_PROVIDER=gmail
   ```

### Outlook.com / Hotmail

1. **Generate an App Password**
   - Go to https://account.microsoft.com/security
   - Click "Advanced security options"
   - Under "App passwords", create a new password

2. **Add to .env file:**
   ```env
   EMAIL_ADDRESS=your.email@outlook.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_PROVIDER=outlook
   ```

### iCloud Mail

1. **Generate an App-Specific Password**
   - Go to https://appleid.apple.com
   - Sign in and go to "Security"
   - Under "App-Specific Passwords", click "Generate Password"

2. **Add to .env file:**
   ```env
   EMAIL_ADDRESS=your.email@icloud.com
   EMAIL_PASSWORD=your-app-specific-password
   EMAIL_PROVIDER=icloud
   ```

### Yahoo Mail

1. **Generate an App Password**
   - Go to https://login.yahoo.com/account/security
   - Click "Generate app password"

2. **Add to .env file:**
   ```env
   EMAIL_ADDRESS=your.email@yahoo.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_PROVIDER=yahoo
   ```

## Option 2: Export and Import 📧

If you don't want to give the app access to your email:

### Manual Export Method

1. **Export from your email client:**
   - **Outlook**: File → Open & Export → Import/Export → Export to a file
   - **Apple Mail**: Mailbox → Export Mailbox
   - **Thunderbird**: Tools → ImportExportTools NG

2. **Save as .mbox or .eml files**

3. **Process with the Mind Manager:**
   ```python
   from mind_manager import MindManager
   
   manager = MindManager()
   manager.import_email_archive("path/to/emails.mbox")
   ```

## Option 3: Apple Mail Direct Access (Mac Only) 🍎

If you use Apple Mail on Mac, we can access it directly:

```python
# No setup needed! Just run:
from integrations.simple_email_integration import AppleMailIntegration

apple_mail = AppleMailIntegration()
recent_emails = apple_mail.get_recent_emails(days=30)
```

## Option 4: Forward Important Emails 📨

Set up email forwarding rules:

1. **Create a dedicated email** for the Mind Manager
2. **Set up forwarding rules** in your main email:
   - Forward emails from specific senders (like Fireflies)
   - Forward emails with specific keywords
   - Forward emails from certain projects

3. **Access the dedicated email** with simple IMAP

## Quick Test Script

```python
# test_simple_email.py
import os
from integrations.simple_email_integration import SimpleEmailIntegration

# Set your credentials
os.environ['EMAIL_ADDRESS'] = 'your.email@gmail.com'
os.environ['EMAIL_PASSWORD'] = 'your-app-password'

# Initialize
email_client = SimpleEmailIntegration(provider='gmail')
email_client.connect()

# Get recent emails
emails = email_client.get_emails(limit=10)
print(f"Found {len(emails)} recent emails")

# Get Fireflies emails specifically
fireflies_emails = email_client.get_fireflies_emails()
print(f"Found {len(fireflies_emails)} Fireflies emails")

# Search for specific content
search_results = email_client.search_emails("project alpha")
print(f"Found {len(search_results)} emails about 'project alpha'")

email_client.disconnect()
```

## Security Notes

- **App passwords** are safer than your main password
- They can be revoked anytime
- They only give access to email (not your full account)
- Store them in .env file (never commit to git)

## Which Method Should You Choose?

- **IMAP with App Password**: Best for ongoing access and automation
- **Export/Import**: Best for one-time analysis or privacy concerns
- **Apple Mail Direct**: Best if you're on Mac and use Apple Mail
- **Email Forwarding**: Best for selective monitoring

The IMAP method is recommended because:
- ✅ Works with all major email providers
- ✅ No complex OAuth setup
- ✅ Can be set up in 2 minutes
- ✅ Gives read-only access to your emails
- ✅ Can search and filter emails easily