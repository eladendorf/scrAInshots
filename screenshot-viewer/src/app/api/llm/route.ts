import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const action = searchParams.get('action')
  
  try {
    // Get the project root directory (parent of screenshot-viewer)
    const projectRoot = path.join(process.cwd(), '..')
    let command = ''
    
    // Set up the environment to include the project root in PYTHONPATH
    const env = {
      ...process.env,
      PYTHONPATH: projectRoot
    }
    
    switch (action) {
      case 'list-models':
        command = `cd "${projectRoot}" && uv run python -c "from local_llm import LocalLLMManager; m = LocalLLMManager(); import json; print(json.dumps({'supported': m.supported_models, 'downloaded': m.list_downloaded_models()}))"`
        break
      case 'check-mlx':
        command = `cd "${projectRoot}" && uv run python -c "from local_llm import LocalLLMManager; m = LocalLLMManager(); import json; print(json.dumps({'installed': m.check_mlx_installation()}))"`
        break
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
    
    const { stdout } = await execAsync(command, { env })
    const result = JSON.parse(stdout)
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Failed to execute command' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  const { action, ...params } = await request.json()
  
  try {
    // Get the project root directory (parent of screenshot-viewer)
    const projectRoot = path.join(process.cwd(), '..')
    const scriptPath = path.join(projectRoot, 'llm_api.py')
    let command = ''
    
    // Set up the environment to include the project root in PYTHONPATH
    const env = {
      ...process.env,
      PYTHONPATH: projectRoot
    }
    
    switch (action) {
      case 'install-mlx':
        command = `cd "${projectRoot}" && uv run python -c "from local_llm import LocalLLMManager; m = LocalLLMManager(); import json; print(json.dumps({'success': m.install_mlx()}))"`
        break
      case 'download-model':
        command = `cd "${projectRoot}" && uv run python ${scriptPath} download-model "${params.model}"`
        break
      case 'set-runtime':
        // Save runtime preference
        command = `cd "${projectRoot}" && uv run python ${scriptPath} set-runtime "${params.runtime}" "${params.model || ''}"`
        break
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
    
    const { stdout } = await execAsync(command, { env })
    const result = JSON.parse(stdout)
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error processing request:', error)
    return NextResponse.json({ error: 'Failed to process request' }, { status: 500 })
  }
}