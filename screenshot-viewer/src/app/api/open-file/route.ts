import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import fs from 'fs/promises'

const execAsync = promisify(exec)

export async function POST(request: Request) {
  try {
    const { filePath } = await request.json()
    
    if (!filePath) {
      return NextResponse.json({ error: 'File path is required' }, { status: 400 })
    }
    
    // Check if file exists
    try {
      await fs.access(filePath)
    } catch {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    
    // Open file based on platform
    let command = ''
    if (process.platform === 'darwin') {
      // macOS
      command = `open "${filePath}"`
    } else if (process.platform === 'win32') {
      // Windows
      command = `start "" "${filePath}"`
    } else {
      // Linux
      command = `xdg-open "${filePath}"`
    }
    
    await execAsync(command)
    
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error opening file:', error)
    return NextResponse.json({ error: 'Failed to open file' }, { status: 500 })
  }
}