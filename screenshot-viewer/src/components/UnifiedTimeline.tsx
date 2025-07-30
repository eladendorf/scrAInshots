'use client'

import React, { useState, useMemo } from 'react'
import { format } from 'date-fns'
import { 
  Camera, 
  FileText, 
  Mail, 
  Video,
  Tag,
  Calendar,
  Users,
  Brain,
  TrendingUp
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface TimelineItem {
  id: string
  source_type: string
  title: string
  content: string
  timestamp: string
  metadata: any
  extracted_concepts: string[]
  concept_categories: string[]
  importance_score: number
  summary?: string
  key_topics?: string[]
}

interface ConceptCluster {
  id: string
  name: string
  description: string
  concepts: string[]
  timeline_items: string[]
  importance_score: number
}

interface UnifiedTimelineProps {
  timelineItems: TimelineItem[]
  conceptClusters: ConceptCluster[]
  onItemClick: (item: TimelineItem) => void
  onConceptClick: (concept: string) => void
}

export default function UnifiedTimeline({ 
  timelineItems, 
  conceptClusters,
  onItemClick,
  onConceptClick 
}: UnifiedTimelineProps) {
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showClusters, setShowClusters] = useState(false)

  const sourceIcons = {
    screenshot: Camera,
    macos_note: FileText,
    outlook_email: Mail,
    fireflies_meeting: Video
  }

  const sourceColors = {
    screenshot: 'bg-blue-100 text-blue-800',
    macos_note: 'bg-green-100 text-green-800',
    outlook_email: 'bg-purple-100 text-purple-800',
    fireflies_meeting: 'bg-orange-100 text-orange-800'
  }

  const categoryColors = {
    project: 'bg-indigo-100 text-indigo-800',
    meeting: 'bg-yellow-100 text-yellow-800',
    idea: 'bg-pink-100 text-pink-800',
    task: 'bg-red-100 text-red-800',
    communication: 'bg-purple-100 text-purple-800',
    research: 'bg-teal-100 text-teal-800',
    planning: 'bg-gray-100 text-gray-800',
    review: 'bg-green-100 text-green-800',
    other: 'bg-gray-100 text-gray-600'
  }

  // Filter items based on selection
  const filteredItems = useMemo(() => {
    let items = [...timelineItems]
    
    if (selectedSource) {
      items = items.filter(item => item.source_type === selectedSource)
    }
    
    if (selectedCategory) {
      items = items.filter(item => item.concept_categories.includes(selectedCategory))
    }
    
    return items.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [timelineItems, selectedSource, selectedCategory])

  // Get source counts
  const sourceCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    timelineItems.forEach(item => {
      counts[item.source_type] = (counts[item.source_type] || 0) + 1
    })
    return counts
  }, [timelineItems])

  return (
    <div className="space-y-6">
      {/* Filters and Stats */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Unified Timeline
          </h3>
          <button
            onClick={() => setShowClusters(!showClusters)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showClusters ? 'Show Timeline' : 'Show Concept Clusters'}
          </button>
        </div>

        {/* Source Filters */}
        <div className="flex flex-wrap gap-2 mb-3">
          {Object.entries(sourceCounts).map(([source, count]) => {
            const Icon = sourceIcons[source as keyof typeof sourceIcons]
            const colorClass = sourceColors[source as keyof typeof sourceColors]
            const isSelected = selectedSource === source
            
            return (
              <button
                key={source}
                onClick={() => setSelectedSource(isSelected ? null : source)}
                className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm transition-all ${
                  isSelected 
                    ? colorClass 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{source.replace('_', ' ')}</span>
                <span className="font-semibold">{count}</span>
              </button>
            )
          })}
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          {Object.keys(categoryColors).map(category => {
            const isSelected = selectedCategory === category
            const colorClass = categoryColors[category as keyof typeof categoryColors]
            
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(isSelected ? null : category)}
                className={`px-3 py-1 rounded-full text-xs transition-all ${
                  isSelected 
                    ? colorClass 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            )
          })}
        </div>
      </div>

      {/* Timeline or Clusters View */}
      {showClusters ? (
        <div className="space-y-4">
          {conceptClusters.map(cluster => (
            <div 
              key={cluster.id}
              className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-semibold text-lg">{cluster.name}</h4>
                  <p className="text-sm text-gray-600">{cluster.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium">
                    {Math.round(cluster.importance_score * 100)}%
                  </span>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-3">
                {cluster.concepts.map(concept => (
                  <Badge
                    key={concept}
                    variant="secondary"
                    className="cursor-pointer hover:bg-gray-300"
                    onClick={() => onConceptClick(concept)}
                  >
                    {concept}
                  </Badge>
                ))}
              </div>
              
              <div className="text-sm text-gray-500">
                {cluster.timeline_items.length} related items
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map(item => {
            const Icon = sourceIcons[item.source_type as keyof typeof sourceIcons]
            const sourceColor = sourceColors[item.source_type as keyof typeof sourceColors]
            
            return (
              <div
                key={item.id}
                onClick={() => onItemClick(item)}
                className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-lg ${sourceColor}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900 truncate pr-2">
                        {item.title}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-gray-500 whitespace-nowrap">
                        <Calendar className="h-3 w-3" />
                        {format(new Date(item.timestamp), 'MMM d, h:mm a')}
                      </div>
                    </div>
                    
                    {item.summary && (
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {item.summary}
                      </p>
                    )}
                    
                    <div className="flex flex-wrap gap-2 mb-2">
                      {item.concept_categories.map(category => (
                        <Badge
                          key={category}
                          variant="outline"
                          className={`text-xs ${categoryColors[category as keyof typeof categoryColors]}`}
                        >
                          {category}
                        </Badge>
                      ))}
                    </div>
                    
                    {item.extracted_concepts.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <Tag className="h-3 w-3 text-gray-400 mt-0.5" />
                        {item.extracted_concepts.slice(0, 5).map(concept => (
                          <span
                            key={concept}
                            onClick={(e) => {
                              e.stopPropagation()
                              onConceptClick(concept)
                            }}
                            className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer"
                          >
                            {concept}
                          </span>
                        ))}
                        {item.extracted_concepts.length > 5 && (
                          <span className="text-xs text-gray-400">
                            +{item.extracted_concepts.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* Source-specific metadata */}
                    {item.source_type === 'fireflies_meeting' && item.metadata.participants && (
                      <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                        <Users className="h-3 w-3" />
                        {item.metadata.participants.length} participants
                      </div>
                    )}
                  </div>
                  
                  {/* Importance indicator */}
                  <div className="flex flex-col items-center">
                    <div 
                      className="w-2 h-16 bg-gray-200 rounded-full overflow-hidden"
                      title={`Importance: ${Math.round(item.importance_score * 100)}%`}
                    >
                      <div 
                        className="w-full bg-gradient-to-t from-blue-500 to-blue-300 rounded-full transition-all"
                        style={{ height: `${item.importance_score * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}