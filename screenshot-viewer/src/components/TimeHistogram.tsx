'use client'

import React, { useMemo, useState } from 'react'
import { format, startOfDay, eachDayOfInterval, isWithinInterval } from 'date-fns'

interface TimeHistogramProps {
  screenshots: Array<{
    id: string
    created_at: string
    metadata: any
  }>
  onDateRangeSelect?: (start: Date, end: Date) => void
  selectedDateRange?: { start: Date; end: Date } | null
}

export default function TimeHistogram({ 
  screenshots, 
  onDateRangeSelect,
  selectedDateRange 
}: TimeHistogramProps) {
  const [hoveredDate, setHoveredDate] = useState<string | null>(null)
  const [selectionStart, setSelectionStart] = useState<Date | null>(null)
  const [isSelecting, setIsSelecting] = useState(false)

  // Process screenshots into daily counts
  const { dailyCounts, dateRange, maxCount } = useMemo(() => {
    if (!screenshots.length) return { dailyCounts: {}, dateRange: null, maxCount: 0 }

    const counts: Record<string, number> = {}
    let minDate = new Date(screenshots[0].created_at)
    let maxDate = new Date(screenshots[0].created_at)

    screenshots.forEach(screenshot => {
      const date = new Date(screenshot.created_at)
      const dayKey = format(startOfDay(date), 'yyyy-MM-dd')
      counts[dayKey] = (counts[dayKey] || 0) + 1
      
      if (date < minDate) minDate = date
      if (date > maxDate) maxDate = date
    })

    // Fill in missing days with 0 counts
    const days = eachDayOfInterval({ 
      start: startOfDay(minDate), 
      end: startOfDay(maxDate) 
    })
    
    days.forEach(day => {
      const dayKey = format(day, 'yyyy-MM-dd')
      if (!counts[dayKey]) counts[dayKey] = 0
    })

    const max = Math.max(...Object.values(counts))

    return { 
      dailyCounts: counts, 
      dateRange: { start: minDate, end: maxDate },
      maxCount: max
    }
  }, [screenshots])

  if (!screenshots.length || !dateRange) {
    return (
      <div className="w-full h-24 bg-gray-50 rounded-lg flex items-center justify-center text-gray-400">
        No screenshots to display
      </div>
    )
  }

  const days = eachDayOfInterval({ 
    start: startOfDay(dateRange.start), 
    end: startOfDay(dateRange.end) 
  })

  const handleMouseDown = (date: Date) => {
    setSelectionStart(date)
    setIsSelecting(true)
  }

  const handleMouseUp = (date: Date) => {
    if (isSelecting && selectionStart && onDateRangeSelect) {
      const start = selectionStart < date ? selectionStart : date
      const end = selectionStart < date ? date : selectionStart
      onDateRangeSelect(start, end)
    }
    setIsSelecting(false)
    setSelectionStart(null)
  }

  const handleMouseEnter = (date: Date) => {
    setHoveredDate(format(date, 'yyyy-MM-dd'))
  }

  const isDateInSelection = (date: Date) => {
    if (selectedDateRange) {
      return isWithinInterval(date, { 
        start: selectedDateRange.start, 
        end: selectedDateRange.end 
      })
    }
    if (isSelecting && selectionStart) {
      const start = selectionStart < date ? selectionStart : date
      const end = selectionStart < date ? date : selectionStart
      return isWithinInterval(date, { start, end })
    }
    return false
  }

  const barWidth = Math.max(1, Math.min(8, 1000 / days.length))
  const barSpacing = Math.max(0.5, Math.min(2, 500 / days.length))

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-gray-700">Timeline</h3>
        {hoveredDate && dailyCounts[hoveredDate] !== undefined && (
          <span className="text-xs text-gray-500">
            {format(new Date(hoveredDate), 'MMM d, yyyy')}: {dailyCounts[hoveredDate]} screenshots
          </span>
        )}
      </div>
      
      <div className="relative w-full h-16 overflow-x-auto overflow-y-hidden">
        <div 
          className="absolute bottom-0 flex items-end"
          style={{ 
            height: '100%',
            minWidth: `${days.length * (barWidth + barSpacing)}px`
          }}
          onMouseLeave={() => setHoveredDate(null)}
        >
          {days.map((day, index) => {
            const dayKey = format(day, 'yyyy-MM-dd')
            const count = dailyCounts[dayKey] || 0
            const height = maxCount > 0 ? (count / maxCount) * 100 : 0
            const isHovered = hoveredDate === dayKey
            const isSelected = isDateInSelection(day)
            
            return (
              <div
                key={dayKey}
                className="relative group cursor-pointer"
                style={{ 
                  width: `${barWidth}px`,
                  marginRight: `${barSpacing}px`,
                  height: '100%'
                }}
                onMouseDown={() => handleMouseDown(day)}
                onMouseUp={() => handleMouseUp(day)}
                onMouseEnter={() => handleMouseEnter(day)}
              >
                {/* Bar */}
                <div
                  className={`absolute bottom-0 w-full transition-all duration-200 rounded-t ${
                    isSelected 
                      ? 'bg-blue-500' 
                      : isHovered 
                        ? 'bg-gray-700' 
                        : count > 0 
                          ? 'bg-gray-400 hover:bg-gray-600' 
                          : 'bg-gray-200'
                  }`}
                  style={{ height: `${height}%`, minHeight: count > 0 ? '2px' : '1px' }}
                />
                
                {/* Date label - show for every Nth day based on width */}
                {(index % Math.max(1, Math.floor(days.length / 20)) === 0 || isHovered) && (
                  <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 text-xs text-gray-500 whitespace-nowrap">
                    {format(day, days.length > 30 ? 'M/d' : 'MMM d')}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
      
      <div className="mt-6 flex items-center justify-between text-xs text-gray-500">
        <span>{format(dateRange.start, 'MMM d, yyyy')}</span>
        <span className="text-gray-400">
          {screenshots.length} screenshots over {days.length} days
        </span>
        <span>{format(dateRange.end, 'MMM d, yyyy')}</span>
      </div>
      
      {(selectedDateRange || isSelecting) && (
        <div className="mt-2 text-xs text-blue-600 text-center">
          {isSelecting ? 'Drag to select date range' : 'Click and drag to select a new range'}
        </div>
      )}
    </div>
  )
}