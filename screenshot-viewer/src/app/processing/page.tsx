"use client"

import { useState, useEffect } from 'react'
import { Play, Pause, RefreshCw, CheckCircle, XCircle, FileImage, BarChart3, Clock, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import axios from 'axios'

interface ProcessingStatus {
  is_running: boolean
  job_id: string | null
  progress: number
  total: number
  processed: number
  failed: number
  current_file: string | null
  status: string
  statistics?: {
    total_processed: number
    by_device: Record<string, number>
    by_date: Record<string, number>
    total_size: number
  }
  start_time?: string
}

export default function ProcessingPage() {
  const [status, setStatus] = useState<ProcessingStatus>({
    is_running: false,
    job_id: null,
    progress: 0,
    total: 0,
    processed: 0,
    failed: 0,
    current_file: null,
    status: 'idle',
  })
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [startTime, setStartTime] = useState<Date | null>(null)

  useEffect(() => {
    // Poll for status every second when processing is running
    const interval = setInterval(() => {
      if (status.is_running || status.status === 'idle') {
        fetchStatus()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [status.is_running])

  const fetchStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/processing/status')
      setStatus(response.data)
      
      // Set start time from server if available
      if (response.data.start_time && response.data.is_running) {
        setStartTime(new Date(response.data.start_time))
      } else if (!response.data.is_running) {
        setStartTime(null)
      }
      
      setError(null)
    } catch (err) {
      console.error('Error fetching status:', err)
    }
  }

  const startProcessing = async () => {
    setIsLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/processing/start')
      if (response.data.success) {
        setError(null)
        setStartTime(new Date())
        await fetchStatus()
      } else {
        setError(response.data.error || 'Failed to start processing')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start processing')
    }
    setIsLoading(false)
  }

  const stopProcessing = async () => {
    setIsLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/processing/stop')
      if (response.data.success) {
        setError(null)
        setStartTime(null)
        await fetchStatus()
      } else {
        setError(response.data.error || 'Failed to stop processing')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to stop processing')
    }
    setIsLoading(false)
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const calculateProcessingRate = () => {
    if (!startTime || status.processed === 0) return 0
    const elapsedHours = (new Date().getTime() - startTime.getTime()) / (1000 * 60 * 60)
    return status.processed / elapsedHours
  }

  const calculateTimeRemaining = () => {
    const rate = calculateProcessingRate()
    if (rate === 0) return null
    const remaining = status.total - status.processed - status.failed
    const hoursRemaining = remaining / rate
    return hoursRemaining
  }

  const formatTimeRemaining = (hours: number | null) => {
    if (hours === null) return 'Calculating...'
    if (hours < 1) {
      const minutes = Math.round(hours * 60)
      return `${minutes} minute${minutes !== 1 ? 's' : ''}`
    } else if (hours < 24) {
      const wholeHours = Math.floor(hours)
      const minutes = Math.round((hours - wholeHours) * 60)
      return `${wholeHours}h ${minutes}m`
    } else {
      const days = Math.floor(hours / 24)
      const remainingHours = Math.round(hours % 24)
      return `${days}d ${remainingHours}h`
    }
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'processing':
      case 'starting':
        return 'text-blue-600'
      case 'completed':
        return 'text-green-600'
      case 'stopped':
        return 'text-orange-600'
      case 'idle':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'processing':
      case 'starting':
        return <RefreshCw className="h-5 w-5 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-5 w-5" />
      case 'stopped':
        return <XCircle className="h-5 w-5" />
      default:
        return <FileImage className="h-5 w-5" />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <h1 className="text-4xl font-bold mb-8">Batch Processing</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
                {getStatusIcon()}
                <span className="text-lg font-semibold capitalize">{status.status}</span>
              </div>
              {status.job_id && (
                <span className="text-sm text-gray-500">Job ID: {status.job_id}</span>
              )}
            </div>

            <div className="flex space-x-3">
              {!status.is_running ? (
                <Button
                  onClick={startProcessing}
                  disabled={isLoading}
                  className="flex items-center space-x-2"
                >
                  <Play className="h-4 w-4" />
                  <span>Start Processing</span>
                </Button>
              ) : (
                <Button
                  onClick={stopProcessing}
                  disabled={isLoading}
                  variant="destructive"
                  className="flex items-center space-x-2"
                >
                  <Pause className="h-4 w-4" />
                  <span>Stop Processing</span>
                </Button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          {(status.is_running || status.progress > 0) && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress: {status.processed} / {status.total} screenshots</span>
                <span>{Math.round(status.progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${status.progress}%` }}
                />
              </div>
              {status.current_file && (
                <div className="mt-2 text-sm text-gray-600">
                  Currently processing: {status.current_file}
                </div>
              )}
              
              {/* Processing Rate and Time Estimate */}
              {status.is_running && startTime && status.processed > 0 && (
                <div className="mt-4 grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Processing Rate</p>
                    <p className="text-lg font-semibold text-blue-600">
                      {Math.round(calculateProcessingRate())} images/hour
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Est. Time Remaining</p>
                    <p className="text-lg font-semibold text-blue-600">
                      {formatTimeRemaining(calculateTimeRemaining())}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Processing Stats */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Processed</p>
                  <p className="text-2xl font-bold text-green-600">{status.processed}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600 opacity-50" />
              </div>
            </div>

            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Failed</p>
                  <p className="text-2xl font-bold text-red-600">{status.failed}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-600 opacity-50" />
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Remaining</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {Math.max(0, status.total - status.processed - status.failed)}
                  </p>
                </div>
                <FileImage className="h-8 w-8 text-blue-600 opacity-50" />
              </div>
            </div>
          </div>
        </div>

        {/* Overall Statistics */}
        {status.statistics && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-2 mb-4">
              <BarChart3 className="h-5 w-5 text-gray-600" />
              <h2 className="text-xl font-semibold">Overall Statistics</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Processed</p>
                <p className="text-2xl font-bold">{status.statistics.total_processed}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Total Size</p>
                <p className="text-2xl font-bold">{formatBytes(status.statistics.total_size)}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600">By Device</p>
                <div className="mt-1">
                  {Object.entries(status.statistics.by_device).map(([device, count]) => (
                    <div key={device} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">{device}:</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-600">Recent Days</p>
                <div className="mt-1">
                  {Object.entries(status.statistics.by_date)
                    .slice(-3)
                    .map(([date, count]) => (
                      <div key={date} className="flex justify-between text-sm">
                        <span className="text-gray-600">{date}:</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}