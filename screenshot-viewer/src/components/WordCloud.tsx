"use client"

import React, { useMemo, useState } from 'react'
import ReactWordcloud from 'react-wordcloud'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { X, Filter } from 'lucide-react'

interface WordCloudProps {
  text: string
  onWordClick?: (word: string, isShiftClick: boolean) => void
  selectedWords?: string[]
  onClearFilter?: () => void
  onApplyFilter?: () => void
}

export function WordCloud({ 
  text, 
  onWordClick, 
  selectedWords = [], 
  onClearFilter,
  onApplyFilter 
}: WordCloudProps) {
  const words = useMemo(() => {
    const wordCount: Record<string, number> = {}
    const cleanText = text.toLowerCase().replace(/[^\w\s]/g, '')
    const wordArray = cleanText.split(/\s+/)
    
    const stopWords = new Set([
      'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
      'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
      'it', 'from', 'be', 'are', 'been', 'was', 'were', 'being'
    ])
    
    wordArray.forEach(word => {
      if (word.length > 3 && !stopWords.has(word)) {
        wordCount[word] = (wordCount[word] || 0) + 1
      }
    })
    
    return Object.entries(wordCount)
      .map(([text, value]) => ({ text, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 50)
  }, [text])
  
  const options = {
    rotations: 2,
    rotationAngles: [-90, 0] as [number, number],
    fontSizes: [12, 60] as [number, number],
    padding: 2,
    enableTooltip: true,
    deterministic: true,
  }
  
  const callbacks = {
    onWordClick: (word: any, event?: MouseEvent) => {
      if (onWordClick && event) {
        onWordClick(word.text, event.shiftKey)
      }
    },
    getWordColor: (word: any) => {
      return selectedWords.includes(word.text) ? '#3b82f6' : '#6b7280'
    },
    getWordTooltip: (word: any) => 
      `${word.text}: ${word.value} occurrence${word.value > 1 ? 's' : ''}\n${
        selectedWords.includes(word.text) ? '(Selected)' : 'Click to filter, Shift+Click to add'
      }`,
  }
  
  return (
    <div className="space-y-4">
      {selectedWords.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Filtered by:</span>
            {selectedWords.map((word) => (
              <Badge key={word} variant="secondary" className="cursor-pointer">
                {word}
                <X 
                  className="ml-1 h-3 w-3" 
                  onClick={(e) => {
                    e.stopPropagation()
                    if (onWordClick) {
                      onWordClick(word, false)
                    }
                  }}
                />
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={onClearFilter}
            >
              Clear
            </Button>
            <Button
              size="sm"
              onClick={onApplyFilter}
            >
              <Filter className="mr-2 h-4 w-4" />
              Apply Filter
            </Button>
          </div>
        </div>
      )}
      
      <div className="w-full h-96 bg-gray-50 rounded-lg p-4 cursor-pointer">
        <ReactWordcloud 
          words={words} 
          options={options} 
          callbacks={callbacks}
        />
      </div>
      
      <div className="text-sm text-gray-600 text-center">
        Click a word to filter • Shift+Click to add multiple filters
      </div>
    </div>
  )
}