import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function GET() {
  try {
    const projectRoot = path.join(process.cwd(), '..')
    
    const command = `cd "${projectRoot}" && uv run python -c "
from config_manager import ConfigManager
import json

manager = ConfigManager()
config = manager.get_config()

# Don't send passwords in plain text, just indicate if they're set
if config.get('email_password'):
    config['email_password_set'] = True
    config['email_password'] = ''
    
if config.get('fireflies_api_key'):
    config['fireflies_api_key_set'] = True
    # Show last 4 characters for verification
    config['fireflies_api_key_preview'] = '****' + config['fireflies_api_key'][-4:] if len(config['fireflies_api_key']) > 4 else '****'
    config['fireflies_api_key'] = ''

print(json.dumps(config))
"`
    
    const { stdout } = await execAsync(command)
    const config = JSON.parse(stdout)
    
    return NextResponse.json(config)
  } catch (error) {
    console.error('Error getting config:', error)
    return NextResponse.json({ 
      error: 'Failed to get configuration',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const updates = await request.json()
    const projectRoot = path.join(process.cwd(), '..')
    
    // Escape single quotes in the JSON string
    const updatesJson = JSON.stringify(updates).replace(/'/g, "\\'")
    
    const command = `cd "${projectRoot}" && uv run python -c "
from config_manager import ConfigManager
import json

manager = ConfigManager()
current_config = manager.get_config()

# Parse updates
updates = json.loads('${updatesJson}')

# Update config
for key, value in updates.items():
    # Skip preview fields
    if key.endswith('_set') or key.endswith('_preview'):
        continue
    # Only update if value is provided (not empty string for passwords)
    if value or key not in ['email_password', 'fireflies_api_key']:
        current_config[key] = value

# Save config
success = manager.save_config(current_config)

print(json.dumps({'success': success}))
"`
    
    const { stdout } = await execAsync(command)
    const result = JSON.parse(stdout)
    
    if (result.success) {
      return NextResponse.json({ success: true })
    } else {
      return NextResponse.json({ 
        error: 'Failed to save configuration' 
      }, { status: 500 })
    }
  } catch (error) {
    console.error('Error saving config:', error)
    return NextResponse.json({ 
      error: 'Failed to save configuration',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function PUT(request: Request) {
  // Test connection endpoint
  try {
    const { type } = await request.json()
    const projectRoot = path.join(process.cwd(), '..')
    
    let command = ''
    
    switch (type) {
      case 'email':
        command = `cd "${projectRoot}" && uv run python -c "
from config_manager import ConfigManager
import json

manager = ConfigManager()
result = manager.test_email_connection()
print(json.dumps(result))
"`
        break
        
      case 'fireflies':
        command = `cd "${projectRoot}" && uv run python -c "
from config_manager import ConfigManager
import json

manager = ConfigManager()
result = manager.test_fireflies_connection()
print(json.dumps(result))
"`
        break
        
      default:
        return NextResponse.json({ error: 'Invalid test type' }, { status: 400 })
    }
    
    const { stdout } = await execAsync(command)
    const result = JSON.parse(stdout)
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error testing connection:', error)
    return NextResponse.json({ 
      error: 'Failed to test connection',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}