import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const action = searchParams.get('action')
  const startDate = searchParams.get('startDate')
  const endDate = searchParams.get('endDate')
  
  try {
    const projectRoot = path.join(process.cwd(), '..')
    let command = ''
    
    switch (action) {
      case 'fetch-timeline':
        command = `cd "${projectRoot}" && uv run python -c "
from mind_manager import MindManager
from datetime import datetime
import json

manager = MindManager()
manager.initialize_integrations()

start = datetime.fromisoformat('${startDate}')
end = datetime.fromisoformat('${endDate}')

items = manager.fetch_all_data(start, end)
analysis = manager.analyze_timeline()

result = {
    'timeline_items': manager.get_timeline_for_display(),
    'clusters': manager.get_clusters_for_display(),
    'analysis': analysis
}

print(json.dumps(result))
"`
        break
        
      case 'search':
        const query = searchParams.get('query')
        command = `cd "${projectRoot}" && uv run python -c "
from mind_manager import MindManager
import json

manager = MindManager()
manager.initialize_integrations()

results = manager.search_across_sources('${query}')
items = [item.to_dict() for item in results]

print(json.dumps({'results': items}))
"`
        break
        
      case 'get-concepts':
        command = `cd "${projectRoot}" && uv run python -c "
from mind_manager import MindManager
import json

manager = MindManager()
if manager.timeline_items:
    concepts = manager._get_top_concepts(30)
    print(json.dumps({'concepts': concepts}))
else:
    print(json.dumps({'concepts': []}))
"`
        break
        
      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
    }
    
    const { stdout } = await execAsync(command)
    const result = JSON.parse(stdout)
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Mind Manager API error:', error)
    return NextResponse.json({ 
      error: 'Failed to execute mind manager operation',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}