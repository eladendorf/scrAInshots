"use client"

import React, { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Download, CheckCircle, AlertCircle, Brain, Key } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import axios from 'axios'
import IntegrationsConfig from './IntegrationsConfig'

interface LLMModel {
  hf_repo: string
  mlx_repo: string
  size: string
  description: string
}

interface SettingsProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function Settings({ open, onOpenChange }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<'llm' | 'integrations'>('llm')
  const [runtime, setRuntime] = useState<'lmstudio' | 'local'>('lmstudio')
  const [supportedModels, setSupportedModels] = useState<Record<string, LLMModel>>({})
  const [downloadedModels, setDownloadedModels] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState<Record<string, number>>({})
  const [mlxInstalled, setMlxInstalled] = useState(false)
  const [isInstallingMlx, setIsInstallingMlx] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      // Check MLX installation
      const mlxResponse = await axios.get('/api/llm?action=check-mlx')
      setMlxInstalled(mlxResponse.data.installed)

      // Get available models
      const modelsResponse = await axios.get('/api/llm?action=list-models')
      setSupportedModels(modelsResponse.data.supported)
      setDownloadedModels(modelsResponse.data.downloaded)

      // Load saved runtime preference
      const configPath = `${process.env.HOME}/.scrainshots/config.json`
      try {
        const config = await fetch(`file://${configPath}`).then(r => r.json())
        setRuntime(config.runtime || 'lmstudio')
        setSelectedModel(config.local_model || 'gemma-2b')
      } catch (e) {
        // Default settings
      }
    } catch (error) {
      console.error('Error loading settings:', error)
    }
  }

  const installMlx = async () => {
    setIsInstallingMlx(true)
    try {
      const response = await axios.post('/api/llm', { action: 'install-mlx' })
      if (response.data.success) {
        setMlxInstalled(true)
      }
    } catch (error) {
      console.error('Error installing MLX:', error)
    }
    setIsInstallingMlx(false)
  }

  const downloadModel = async (modelName: string) => {
    setIsDownloading(true)
    setDownloadProgress({ ...downloadProgress, [modelName]: 0 })

    try {
      const response = await axios.post('/api/llm', {
        action: 'download-model',
        model: modelName
      })

      if (response.data.success) {
        setDownloadedModels([...downloadedModels, modelName])
        setDownloadProgress({ ...downloadProgress, [modelName]: 100 })
      }
    } catch (error) {
      console.error('Error downloading model:', error)
    }

    setIsDownloading(false)
  }

  const saveSettings = async () => {
    try {
      await axios.post('/api/llm', {
        action: 'set-runtime',
        runtime: runtime,
        model: runtime === 'local' ? selectedModel : undefined
      })
      onOpenChange(false)
    } catch (error) {
      console.error('Error saving settings:', error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Configure AI processing and integrations
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'llm'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              LLM Settings
            </div>
          </button>
          <button
            onClick={() => setActiveTab('integrations')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'integrations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4" />
              Integrations
            </div>
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'llm' ? (
            <div className="space-y-6 p-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">Runtime Selection</h3>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="runtime"
                  value="lmstudio"
                  checked={runtime === 'lmstudio'}
                  onChange={(e) => setRuntime('lmstudio')}
                  className="w-4 h-4"
                />
                <div>
                  <div className="font-medium">LM Studio (Recommended)</div>
                  <div className="text-sm text-gray-600">
                    Use LM Studio running on localhost:1234
                  </div>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="runtime"
                  value="local"
                  checked={runtime === 'local'}
                  onChange={(e) => setRuntime('local')}
                  className="w-4 h-4"
                />
                <div>
                  <div className="font-medium">Local MLX Runtime</div>
                  <div className="text-sm text-gray-600">
                    Run models locally using Apple MLX (Apple Silicon only)
                  </div>
                </div>
              </label>
            </div>
          </div>

          {runtime === 'local' && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Local Model Management</h3>
              
              {!mlxInstalled && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="h-5 w-5 text-yellow-600" />
                    <span className="text-sm">MLX is not installed</span>
                  </div>
                  <Button
                    onClick={installMlx}
                    disabled={isInstallingMlx}
                    size="sm"
                    className="mt-2"
                  >
                    {isInstallingMlx ? 'Installing...' : 'Install MLX'}
                  </Button>
                </div>
              )}

              <div className="space-y-3">
                {Object.entries(supportedModels).map(([name, model]) => {
                  const isDownloaded = downloadedModels.includes(name)
                  const progress = downloadProgress[name] || 0

                  return (
                    <div
                      key={name}
                      className={`border rounded-lg p-4 ${
                        selectedModel === name ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <label className="flex items-center space-x-3 cursor-pointer">
                            <input
                              type="radio"
                              name="model"
                              value={name}
                              checked={selectedModel === name}
                              onChange={(e) => setSelectedModel(name)}
                              disabled={!isDownloaded}
                              className="w-4 h-4"
                            />
                            <div>
                              <div className="font-medium">{name}</div>
                              <div className="text-sm text-gray-600">
                                {model.description} • {model.size}
                              </div>
                            </div>
                          </label>
                        </div>

                        <div className="ml-4">
                          {isDownloaded ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <Button
                              onClick={() => downloadModel(name)}
                              disabled={isDownloading || !mlxInstalled}
                              size="sm"
                              variant="outline"
                            >
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          )}
                        </div>
                      </div>

                      {progress > 0 && progress < 100 && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button onClick={() => onOpenChange(false)} variant="outline">
                  Cancel
                </Button>
                <Button onClick={saveSettings}>
                  Save Settings
                </Button>
              </div>
            </div>
          ) : (
            <div className="p-6">
              <IntegrationsConfig onConfigUpdate={() => {
                // Optionally refresh or notify about config changes
                console.log('Integration config updated')
              }} />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}