import { NextResponse } from 'next/server'

const API_BASE_URL = 'http://localhost:8000'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  
  try {
    // Forward the request to Flask API
    const url = new URL('/api/screenshots', API_BASE_URL)
    searchParams.forEach((value, key) => {
      url.searchParams.append(key, value)
    })
    
    const response = await fetch(url.toString())
    const data = await response.json()
    
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching screenshots:', error)
    return NextResponse.json({ error: 'Failed to fetch screenshots' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${API_BASE_URL}/api/screenshots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error processing request:', error)
    return NextResponse.json({ error: 'Failed to process request' }, { status: 500 })
  }
}