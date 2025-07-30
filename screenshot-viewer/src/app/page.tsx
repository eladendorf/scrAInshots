"use client"

import { useState, useEffect } from 'react'
import { Search, Calendar, RefreshCw, Download, Eye, Sparkles, Settings as SettingsIcon, Activity, X } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import axios from 'axios'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { WordCloud } from '@/components/WordCloud'
import { Settings } from '@/components/Settings'
import TimeHistogram from '@/components/TimeHistogram'

interface Screenshot {
  id: string
  content: string
  metadata: {
    filename: string
    created_time: string
    modified_time: string
    dimensions: string
    device_type: string
    md_path: string
    original_path: string
  }
}

export default function Home() {
  const [screenshots, setScreenshots] = useState<Screenshot[]>([])
  const [filteredScreenshots, setFilteredScreenshots] = useState<Screenshot[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedScreenshot, setSelectedScreenshot] = useState<Screenshot | null>(null)
  const [isRefining, setIsRefining] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showWordCloud, setShowWordCloud] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [wordCloudFilter, setWordCloudFilter] = useState<string[]>([])
  const [pendingWordCloudFilter, setPendingWordCloudFilter] = useState<string[]>([])
  const [selectedDateRange, setSelectedDateRange] = useState<{ start: Date; end: Date } | null>(null)

  useEffect(() => {
    fetchScreenshots()
  }, [])

  useEffect(() => {
    filterScreenshots()
  }, [screenshots, searchQuery, startDate, endDate, wordCloudFilter, selectedDateRange])

  const fetchScreenshots = async () => {
    try {
      const response = await axios.get('/api/screenshots')
      setScreenshots(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch screenshots. Make sure the API server is running.')
      console.error('Error fetching screenshots:', err)
    }
  }

  const filterScreenshots = () => {
    let filtered = [...screenshots]

    if (searchQuery) {
      filtered = filtered.filter(s => 
        s.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.metadata.filename.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedDateRange) {
      filtered = filtered.filter(s => {
        const created = new Date(s.metadata.created_time)
        return created >= selectedDateRange.start && created <= selectedDateRange.end
      })
    } else if (startDate && endDate) {
      filtered = filtered.filter(s => {
        const created = parseISO(s.metadata.created_time)
        const start = parseISO(startDate)
        const end = parseISO(endDate)
        return created >= start && created <= end
      })
    }

    // Apply word cloud filters
    if (wordCloudFilter.length > 0) {
      filtered = filtered.filter(s => {
        const contentLower = s.content.toLowerCase()
        // All selected words must be present in the content
        return wordCloudFilter.every(word => 
          contentLower.includes(word.toLowerCase())
        )
      })
    }

    setFilteredScreenshots(filtered)
  }

  const handleProcessAll = async () => {
    setIsProcessing(true)
    try {
      await axios.post('/api/screenshots', { action: 'process' })
      await fetchScreenshots()
      setError(null)
    } catch (err) {
      setError('Failed to process screenshots')
      console.error('Error processing screenshots:', err)
    }
    setIsProcessing(false)
  }

  const handleRefine = async (screenshot: Screenshot) => {
    setIsRefining(true)
    try {
      const prompt = `This is content extracted from a screenshot on my computer. Help me understand the context: 
      - Is this a company? If so, tell me about the company.
      - Is this a product? If so, tell me about the product.
      - What is the topic? Tell me 200 words about the topic.
      - Do research online to provide additional context.`
      
      await axios.post('/api/screenshots', {
        action: 'refine',
        id: screenshot.id,
        prompt
      })
      
      await fetchScreenshots()
      setError(null)
    } catch (err) {
      setError('Failed to refine content')
      console.error('Error refining content:', err)
    }
    setIsRefining(false)
  }

  const getAllText = () => {
    return screenshots.map(s => s.content).join(' ')
  }

  const handleWordClick = (word: string, isShiftClick: boolean) => {
    if (isShiftClick) {
      // Add to filter if not already present, remove if already present
      setPendingWordCloudFilter(prev => 
        prev.includes(word) 
          ? prev.filter(w => w !== word)
          : [...prev, word]
      )
    } else {
      // Replace entire filter with just this word
      setPendingWordCloudFilter([word])
    }
  }

  const handleApplyWordCloudFilter = () => {
    setWordCloudFilter(pendingWordCloudFilter)
    setShowWordCloud(false)
  }

  const handleClearWordCloudFilter = () => {
    setPendingWordCloudFilter([])
    setWordCloudFilter([])
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8">Screenshot Viewer</h1>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-6 space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search screenshots..."
                  className="w-full pl-10 pr-4 py-2 border rounded-lg"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <input
                type="date"
                className="px-4 py-2 border rounded-lg"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
              <input
                type="date"
                className="px-4 py-2 border rounded-lg"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          {(wordCloudFilter.length > 0 || selectedDateRange) && (
            <div className="flex flex-col gap-2">
              {wordCloudFilter.length > 0 && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Word filters:</span>
                  {wordCloudFilter.map((word) => (
                    <Badge key={word} variant="secondary">
                      {word}
                    </Badge>
                  ))}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setWordCloudFilter([])}
                    className="ml-auto"
                  >
                    <X className="h-4 w-4" />
                    Clear
                  </Button>
                </div>
              )}
              {selectedDateRange && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Date range:</span>
                  <Badge variant="secondary">
                    {format(selectedDateRange.start, 'MMM d, yyyy')} - {format(selectedDateRange.end, 'MMM d, yyyy')}
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedDateRange(null)}
                    className="ml-auto"
                  >
                    <X className="h-4 w-4" />
                    Clear
                  </Button>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-4">
            <Link href="/processing">
              <Button>
                <Activity className="mr-2 h-4 w-4" />
                Batch Processing
              </Button>
            </Link>
            
            <Button onClick={() => setShowWordCloud(true)} variant="outline">
              <Eye className="mr-2 h-4 w-4" />
              Word Cloud
            </Button>
            
            <Button onClick={() => setShowSettings(true)} variant="outline">
              <SettingsIcon className="mr-2 h-4 w-4" />
              Settings
            </Button>
          </div>
        </div>

        {/* Time Histogram */}
        <div className="mb-6">
          <TimeHistogram
            screenshots={screenshots.map(s => ({
              id: s.id,
              created_at: s.metadata.created_time,
              metadata: s.metadata
            }))}
            onDateRangeSelect={(start, end) => {
              setSelectedDateRange({ start, end })
              // Clear the manual date inputs when using histogram
              setStartDate('')
              setEndDate('')
            }}
            selectedDateRange={selectedDateRange}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredScreenshots.map((screenshot) => (
            <div
              key={screenshot.id}
              className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedScreenshot(screenshot)}
            >
              <h3 className="font-semibold text-lg mb-2">{screenshot.metadata.filename}</h3>
              <p className="text-sm text-gray-600 mb-2">
                {format(parseISO(screenshot.metadata.created_time), 'PPP')}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                {screenshot.metadata.dimensions} • {screenshot.metadata.device_type}
              </p>
              <p className="text-sm line-clamp-3">{screenshot.content.substring(0, 200)}...</p>
            </div>
          ))}
        </div>

        <Dialog open={!!selectedScreenshot} onOpenChange={() => setSelectedScreenshot(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedScreenshot?.metadata.filename}</DialogTitle>
              <DialogDescription>
                Created: {selectedScreenshot && format(parseISO(selectedScreenshot.metadata.created_time), 'PPP')}
              </DialogDescription>
            </DialogHeader>
            
            <div className="mt-4">
              <div className="flex gap-2 mb-4">
                <Button
                  onClick={() => selectedScreenshot && handleRefine(selectedScreenshot)}
                  disabled={isRefining}
                  size="sm"
                >
                  <Sparkles className={`mr-2 h-4 w-4 ${isRefining ? 'animate-pulse' : ''}`} />
                  Refine with AI
                </Button>
                
                <Button
                  onClick={async () => {
                    if (selectedScreenshot?.metadata.original_path) {
                      try {
                        const response = await fetch('/api/open-file', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ filePath: selectedScreenshot.metadata.original_path })
                        })
                        if (!response.ok) {
                          console.error('Failed to open file')
                        }
                      } catch (error) {
                        console.error('Error opening file:', error)
                      }
                    }
                  }}
                  variant="outline"
                  size="sm"
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Original
                </Button>
              </div>
              
              <div className="prose max-w-none">
                <ReactMarkdown>{selectedScreenshot?.content || ''}</ReactMarkdown>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={showWordCloud} onOpenChange={(open) => {
          setShowWordCloud(open)
          if (open) {
            // Copy current filter to pending when opening
            setPendingWordCloudFilter(wordCloudFilter)
          }
        }}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Word Cloud</DialogTitle>
              <DialogDescription>
                Most frequent words across all screenshots
              </DialogDescription>
            </DialogHeader>
            
            <WordCloud 
              text={getAllText()} 
              onWordClick={handleWordClick}
              selectedWords={pendingWordCloudFilter}
              onClearFilter={handleClearWordCloudFilter}
              onApplyFilter={handleApplyWordCloudFilter}
            />
          </DialogContent>
        </Dialog>

        <Settings open={showSettings} onOpenChange={setShowSettings} />
      </div>
    </div>
  )
}