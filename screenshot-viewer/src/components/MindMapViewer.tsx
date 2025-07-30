'use client'

import React, { useState, useEffect } from 'react'
import { 
  Brain, 
  Calendar, 
  GitBranch, 
  TrendingUp,
  Users,
  Lightbulb,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import mermaid from 'mermaid'

interface MindMapViewerProps {
  monthData?: any
  onMonthChange?: (month: string) => void
}

export default function MindMapViewer({ monthData, onMonthChange }: MindMapViewerProps) {
  const [currentView, setCurrentView] = useState<'mindmap' | 'gantt' | 'insights'>('mindmap')
  const [isLoading, setIsLoading] = useState(false)
  const [availableMonths, setAvailableMonths] = useState<string[]>([])
  const [currentMonthIndex, setCurrentMonthIndex] = useState(0)

  useEffect(() => {
    // Initialize mermaid
    mermaid.initialize({ 
      startOnLoad: true,
      theme: 'default',
      themeVariables: {
        primaryColor: '#3b82f6',
        primaryTextColor: '#fff',
        primaryBorderColor: '#2563eb',
        lineColor: '#6b7280',
        secondaryColor: '#10b981',
        tertiaryColor: '#f59e0b'
      }
    })
  }, [])

  useEffect(() => {
    // Re-render mermaid diagrams when view changes
    if (currentView === 'mindmap' || currentView === 'gantt') {
      mermaid.contentLoaded()
    }
  }, [currentView, monthData])

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newIndex = direction === 'prev' 
      ? Math.max(0, currentMonthIndex - 1)
      : Math.min(availableMonths.length - 1, currentMonthIndex + 1)
    
    setCurrentMonthIndex(newIndex)
    if (onMonthChange && availableMonths[newIndex]) {
      onMonthChange(availableMonths[newIndex])
    }
  }

  const renderMindMap = () => {
    if (!monthData?.mindmap) {
      return <div className="text-gray-500">No mind map data available</div>
    }

    const { central_theme, branches } = monthData.mindmap

    // Generate Mermaid mindmap syntax
    let mermaidCode = `graph TD\n`
    mermaidCode += `    A[${central_theme}]:::central\n`

    branches?.forEach((branch: any, idx: number) => {
      const branchId = `B${idx}`
      mermaidCode += `    A --> ${branchId}["${branch.status || ''} ${branch.name}"]\n`
      
      branch.sub_branches?.forEach((sub: any, subIdx: number) => {
        const subId = `${branchId}S${subIdx}`
        mermaidCode += `    ${branchId} --> ${subId}[${sub}]\n`
      })

      branch.connections?.forEach((conn: any) => {
        mermaidCode += `    ${branchId} -.-> ${conn}\n`
      })
    })

    mermaidCode += `\n    classDef central fill:#3b82f6,stroke:#2563eb,stroke-width:3px,color:#fff`

    return (
      <div className="w-full h-full flex items-center justify-center">
        <pre className="mermaid">{mermaidCode}</pre>
      </div>
    )
  }

  const renderGantt = () => {
    if (!monthData?.gantt?.tasks) {
      return <div className="text-gray-500">No Gantt chart data available</div>
    }

    const tasks = monthData.gantt.tasks

    // Group tasks by category
    const categories: Record<string, any[]> = {}
    tasks.forEach((task: any) => {
      const cat = task.category || 'Other'
      if (!categories[cat]) categories[cat] = []
      categories[cat].push(task)
    })

    let mermaidCode = `gantt\n`
    mermaidCode += `    title Tasks and Projects\n`
    mermaidCode += `    dateFormat YYYY-MM-DD\n\n`

    Object.entries(categories).forEach(([category, catTasks]) => {
      mermaidCode += `    section ${category}\n`
      catTasks.forEach((task: any) => {
        const status = task.status === 'completed' ? 'done,' : 
                      task.status === 'blocked' ? 'crit,' : 
                      task.status === 'in_progress' ? 'active,' : ''
        
        mermaidCode += `    ${task.name} :${status}${task.id}, ${task.start}, ${task.end}\n`
      })
    })

    return (
      <div className="w-full h-full">
        <pre className="mermaid">{mermaidCode}</pre>
        
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Task Details</h3>
          <div className="space-y-2">
            {tasks.map((task: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {task.status === 'completed' ? '✅' :
                     task.status === 'in_progress' ? '🚧' :
                     task.status === 'blocked' ? '❌' :
                     task.status === 'open' ? '📋' : '💤'}
                  </span>
                  <div>
                    <div className="font-medium">{task.name}</div>
                    <div className="text-sm text-gray-500">
                      {task.people?.join(', ')} • {task.start} to {task.end}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderInsights = () => {
    if (!monthData) {
      return <div className="text-gray-500">No insights available</div>
    }

    return (
      <div className="space-y-6">
        {/* Mental State */}
        {monthData.mental_state && (
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Mental State & Workload
            </h3>
            <div className="space-y-2">
              {Object.entries(monthData.mental_state).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-700">{key}:</span>
                  <span className="font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* People Network */}
        {monthData.people_network && Object.keys(monthData.people_network).length > 0 && (
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Users className="h-5 w-5" />
              People Network
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(monthData.people_network).map(([person, data]: [string, any]) => (
                <div key={person} className="bg-white px-3 py-2 rounded-full shadow-sm">
                  <span className="font-medium">{person}</span>
                  {typeof data === 'object' && data.interactions && (
                    <span className="text-sm text-gray-500 ml-2">
                      ({data.interactions} interactions)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Concepts */}
        {monthData.concepts && Object.keys(monthData.concepts).length > 0 && (
          <div className="bg-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Key Concepts
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(monthData.concepts).map(([concept, data]: [string, any]) => (
                <div key={concept} className="bg-white px-3 py-2 rounded-lg shadow-sm">
                  <span className="font-medium">{concept}</span>
                  {typeof data === 'object' && data.frequency && (
                    <span className="text-sm text-gray-500 ml-2">
                      ({data.frequency}x)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actionable Insights */}
        {monthData.insights && (
          <div className="bg-orange-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Actionable Insights
            </h3>
            <div className="prose prose-sm max-w-none">
              {typeof monthData.insights === 'string' ? (
                <p>{monthData.insights}</p>
              ) : (
                Object.entries(monthData.insights).map(([key, value]) => (
                  <div key={key}>
                    <h4 className="font-medium">{key}</h4>
                    <p>{String(value)}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="h-6 w-6" />
          Mind Evolution
        </h2>
        
        {/* Month Navigation */}
        <div className="flex items-center gap-2">
          <Button
            onClick={() => navigateMonth('prev')}
            disabled={currentMonthIndex === 0}
            variant="outline"
            size="sm"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="px-3 py-1 bg-gray-100 rounded-lg font-medium">
            {monthData?.month || 'No Data'}
          </span>
          
          <Button
            onClick={() => navigateMonth('next')}
            disabled={currentMonthIndex === availableMonths.length - 1}
            variant="outline"
            size="sm"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setCurrentView('mindmap')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            currentView === 'mindmap' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Mind Map
          </div>
        </button>
        
        <button
          onClick={() => setCurrentView('gantt')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            currentView === 'gantt' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Gantt Chart
          </div>
        </button>
        
        <button
          onClick={() => setCurrentView('insights')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            currentView === 'insights' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            Insights
          </div>
        </button>
      </div>

      {/* Content Area */}
      <div className="min-h-[500px]">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <>
            {currentView === 'mindmap' && renderMindMap()}
            {currentView === 'gantt' && renderGantt()}
            {currentView === 'insights' && renderInsights()}
          </>
        )}
      </div>
    </div>
  )
}