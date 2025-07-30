'use client'

import React, { useState, useEffect } from 'react'
import { 
  Key, 
  Mail, 
  Loader2, 
  Check, 
  X, 
  AlertCircle,
  Eye,
  EyeOff,
  HelpCircle,
  ExternalLink
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface IntegrationsConfigProps {
  onConfigUpdate?: () => void
}

export default function IntegrationsConfig({ onConfigUpdate }: IntegrationsConfigProps) {
  const [config, setConfig] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, any>>({})
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  const emailProviders = [
    { value: 'gmail', label: 'Gmail', imap: 'imap.gmail.com' },
    { value: 'outlook', label: 'Outlook/Hotmail', imap: 'outlook.office365.com' },
    { value: 'yahoo', label: 'Yahoo', imap: 'imap.mail.yahoo.com' },
    { value: 'icloud', label: 'iCloud', imap: 'imap.mail.me.com' },
    { value: 'custom', label: 'Custom IMAP', imap: '' }
  ]

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/config')
      const data = await response.json()
      setConfig(data)
    } catch (error) {
      console.error('Error fetching config:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    setErrors({})
    
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      
      if (response.ok) {
        await fetchConfig() // Refresh to get updated preview values
        if (onConfigUpdate) {
          onConfigUpdate()
        }
      } else {
        const error = await response.json()
        setErrors({ save: error.error || 'Failed to save configuration' })
      }
    } catch (error) {
      setErrors({ save: 'Failed to save configuration' })
    } finally {
      setSaving(false)
    }
  }

  const testConnection = async (type: 'email' | 'fireflies') => {
    setTesting(type)
    setTestResults({ ...testResults, [type]: null })
    
    try {
      const response = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      })
      
      const result = await response.json()
      setTestResults({ ...testResults, [type]: result })
    } catch (error) {
      setTestResults({ 
        ...testResults, 
        [type]: { success: false, error: 'Connection test failed' }
      })
    } finally {
      setTesting(null)
    }
  }

  const updateConfig = (key: string, value: any) => {
    setConfig({ ...config, [key]: value })
    // Clear test results when config changes
    if (key.includes('email') || key.includes('imap')) {
      setTestResults({ ...testResults, email: null })
    }
    if (key.includes('fireflies')) {
      setTestResults({ ...testResults, fireflies: null })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Fireflies Configuration */}
      <div className="border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Video className="h-5 w-5" />
            Fireflies.ai Integration
          </h3>
          <a 
            href="https://fireflies.ai/api" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            Get API Key
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">API Key</label>
          <div className="relative">
            <input
              type={showPasswords.fireflies ? 'text' : 'password'}
              className="w-full px-3 py-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={config.fireflies_api_key_set ? `API Key set (${config.fireflies_api_key_preview})` : 'Paste your Fireflies API key'}
              value={config.fireflies_api_key || ''}
              onChange={(e) => updateConfig('fireflies_api_key', e.target.value)}
            />
            <button
              type="button"
              onClick={() => setShowPasswords({ ...showPasswords, fireflies: !showPasswords.fireflies })}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showPasswords.fireflies ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <p className="text-xs text-gray-500">
            Your API key is encrypted and stored securely on your local machine
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => testConnection('fireflies')}
            disabled={!config.fireflies_api_key && !config.fireflies_api_key_set}
            variant="outline"
            size="sm"
          >
            {testing === 'fireflies' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Test Connection'
            )}
          </Button>
          
          {testResults.fireflies && (
            <div className={`flex items-center gap-1 text-sm ${
              testResults.fireflies.success ? 'text-green-600' : 'text-red-600'
            }`}>
              {testResults.fireflies.success ? (
                <>
                  <Check className="h-4 w-4" />
                  {testResults.fireflies.message}
                </>
              ) : (
                <>
                  <X className="h-4 w-4" />
                  {testResults.fireflies.error}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Email Configuration */}
      <div className="border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Integration
          </h3>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.email_enabled || false}
              onChange={(e) => updateConfig('email_enabled', e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Enable</span>
          </label>
        </div>

        {config.email_enabled && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Email Provider</label>
                <select
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={config.email_provider || 'gmail'}
                  onChange={(e) => {
                    updateConfig('email_provider', e.target.value)
                    const provider = emailProviders.find(p => p.value === e.target.value)
                    if (provider && provider.imap) {
                      updateConfig('imap_server', provider.imap)
                    }
                  }}
                >
                  {emailProviders.map(provider => (
                    <option key={provider.value} value={provider.value}>
                      {provider.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Email Address</label>
                <input
                  type="email"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your.email@example.com"
                  value={config.email_address || ''}
                  onChange={(e) => updateConfig('email_address', e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                App Password
                <div className="group relative inline-block">
                  <HelpCircle className="h-4 w-4 text-gray-400" />
                  <div className="invisible group-hover:visible absolute left-0 top-6 w-64 p-2 bg-gray-800 text-white text-xs rounded-lg z-10">
                    Use an app-specific password, not your regular email password. 
                    See the setup guide for instructions on generating app passwords.
                  </div>
                </div>
              </label>
              <div className="relative">
                <input
                  type={showPasswords.email ? 'text' : 'password'}
                  className="w-full px-3 py-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={config.email_password_set ? 'Password is set' : 'App password'}
                  value={config.email_password || ''}
                  onChange={(e) => updateConfig('email_password', e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, email: !showPasswords.email })}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPasswords.email ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {config.email_provider === 'custom' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">IMAP Server</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="imap.example.com"
                    value={config.imap_server || ''}
                    onChange={(e) => updateConfig('imap_server', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">IMAP Port</label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="993"
                    value={config.imap_port || 993}
                    onChange={(e) => updateConfig('imap_port', parseInt(e.target.value))}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <Button
                onClick={() => testConnection('email')}
                disabled={!config.email_address || (!config.email_password && !config.email_password_set)}
                variant="outline"
                size="sm"
              >
                {testing === 'email' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Test Connection'
                )}
              </Button>
              
              {testResults.email && (
                <div className={`flex items-center gap-1 text-sm ${
                  testResults.email.success ? 'text-green-600' : 'text-red-600'
                }`}>
                  {testResults.email.success ? (
                    <>
                      <Check className="h-4 w-4" />
                      {testResults.email.message}
                    </>
                  ) : (
                    <>
                      <X className="h-4 w-4" />
                      {testResults.email.error}
                    </>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* MacOS Notes */}
      <div className="border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            MacOS Notes
          </h3>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.macos_notes_enabled !== false}
              onChange={(e) => updateConfig('macos_notes_enabled', e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Enable</span>
          </label>
        </div>
        <p className="text-sm text-gray-600">
          Automatically syncs with your Notes app on macOS. No configuration needed.
        </p>
      </div>

      {/* Error Display */}
      {errors.save && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{errors.save}</span>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={saveConfig}
          disabled={saving}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Check className="mr-2 h-4 w-4" />
              Save Configuration
            </>
          )}
        </Button>
      </div>

      {/* Help Text */}
      <div className="text-sm text-gray-500 space-y-1">
        <p>• All credentials are encrypted and stored locally on your machine</p>
        <p>• Email passwords should be app-specific passwords, not your main password</p>
        <p>• Configuration changes take effect immediately after saving</p>
      </div>
    </div>
  )
}