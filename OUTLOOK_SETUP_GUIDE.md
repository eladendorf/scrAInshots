# Outlook Integration Setup Guide

This guide walks you through setting up Microsoft Outlook integration via Azure AD and Microsoft Graph API.

## Step 1: Register an Application in Azure AD

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your Microsoft work or personal account

2. **Access App Registrations**
   - In the left navigation, select "Azure Active Directory"
   - Select "App registrations" from the menu
   - Click "New registration"

3. **Configure Your App**
   - **Name**: Enter "ScrAInshots Mind Manager" (or any name you prefer)
   - **Supported account types**: Choose based on your needs:
     - "Accounts in this organizational directory only" - for work accounts only
     - "Accounts in any organizational directory" - for any work account
     - "Personal Microsoft accounts only" - for personal accounts
     - "Accounts in any organizational directory and personal accounts" - for both
   - **Redirect URI**: 
     - Platform: "Web"
     - URI: `http://localhost:8000/callback` (for local development)
   - Click "Register"

4. **Save Your Application IDs**
   After registration, you'll see:
   - **Application (client) ID**: Copy this (you'll need it as OUTLOOK_CLIENT_ID)
   - **Directory (tenant) ID**: Copy this (you'll need it as OUTLOOK_TENANT_ID)

## Step 2: Configure Permissions

1. **Navigate to API Permissions**
   - In your app's page, click "API permissions" in the left menu
   - Click "Add a permission"
   - Select "Microsoft Graph"

2. **Choose Permission Type**
   - Select "Delegated permissions" (for user-based access)

3. **Add Required Permissions**
   Search for and add these permissions:
   - `Mail.Read` - Read user mail
   - `Mail.Read.Shared` - Read mail in shared mailboxes
   - `User.Read` - Sign in and read user profile
   - `offline_access` - Maintain access to data

4. **Grant Admin Consent (if needed)**
   - If you're an admin, click "Grant admin consent for [Your Organization]"
   - If not, users will need to consent when they first use the app

## Step 3: Create a Client Secret

1. **Navigate to Certificates & Secrets**
   - In your app's page, click "Certificates & secrets" in the left menu
   - Click "New client secret"

2. **Configure the Secret**
   - Description: "ScrAInshots Mind Manager Secret"
   - Expires: Choose an appropriate expiration (e.g., 24 months)
   - Click "Add"

3. **Save the Secret Value**
   - **IMPORTANT**: Copy the secret value immediately (it won't be shown again)
   - This is your OUTLOOK_CLIENT_SECRET

## Step 4: Configure Authentication

1. **Navigate to Authentication**
   - Click "Authentication" in the left menu
   - Under "Platform configurations", you should see your Web platform

2. **Add Additional Redirect URIs (optional)**
   - Add `http://localhost:3000/auth/callback` for Next.js frontend
   - Add `https://yourdomain.com/auth/callback` for production

3. **Configure Token Settings**
   - Under "Implicit grant and hybrid flows":
     - Check "ID tokens" (if using OpenID Connect)
     - Check "Access tokens" (for API access)

## Step 5: Set Up Your Environment

1. **Create or Update .env File**
   ```bash
   # In your project root
   cp .env.example .env
   ```

2. **Add Your Credentials**
   Edit `.env` and add:
   ```env
   # Microsoft Outlook Configuration
   OUTLOOK_CLIENT_ID=your-application-client-id-here
   OUTLOOK_CLIENT_SECRET=your-client-secret-value-here
   OUTLOOK_TENANT_ID=your-directory-tenant-id-here
   ```

## Step 6: Initial Authentication Flow

Since we're using delegated permissions, you'll need to authenticate as a user. Here's a helper script:

```python
# save as: outlook_auth_helper.py
import webbrowser
from urllib.parse import urlencode

def get_auth_url(client_id, tenant_id, redirect_uri="http://localhost:8000/callback"):
    """Generate the authorization URL"""
    base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': 'Mail.Read Mail.Read.Shared User.Read offline_access',
        'state': '12345'  # Random state for security
    }
    
    auth_url = f"{base_url}?{urlencode(params)}"
    return auth_url

# Usage:
client_id = "your-client-id"
tenant_id = "your-tenant-id"

auth_url = get_auth_url(client_id, tenant_id)
print(f"Open this URL in your browser:\n{auth_url}")
webbrowser.open(auth_url)
```

## Step 7: Test Your Integration

Run the test script:
```bash
python test_mind_manager.py
```

## Common Issues and Solutions

### Issue: "Application not found"
- Ensure you're using the correct tenant ID
- Check that the app registration is in the correct directory

### Issue: "Invalid client secret"
- Client secrets expire - check expiration date
- Ensure you copied the secret value, not the secret ID
- Special characters in secrets may need to be URL-encoded

### Issue: "Insufficient privileges"
- Ensure all required permissions are added
- Admin consent may be required for some permissions
- User must consent to the permissions on first use

### Issue: "Invalid redirect URI"
- Redirect URI must match exactly (including trailing slashes)
- Check both Azure AD config and your code

## Security Best Practices

1. **Never commit credentials to version control**
   - Use .env files (already in .gitignore)
   - Consider using Azure Key Vault for production

2. **Rotate secrets regularly**
   - Set calendar reminders before secret expiration
   - Keep multiple valid secrets during rotation

3. **Use least privilege**
   - Only request permissions you actually need
   - Consider application permissions vs delegated permissions

4. **Monitor access**
   - Review sign-in logs in Azure AD
   - Set up alerts for unusual activity

## Next Steps

Once configured, the Mind Manager will:
- Fetch your Outlook emails within specified date ranges
- Extract sent emails for concept analysis
- Identify Fireflies meeting invitations
- Integrate email data into the unified timeline

For production deployment, consider:
- Using certificate-based authentication instead of secrets
- Implementing proper token caching
- Setting up a proper OAuth flow with a backend service