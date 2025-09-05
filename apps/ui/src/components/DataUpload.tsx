'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Download } from 'lucide-react'

interface UploadResponse {
  success: boolean
  message: string
  records_processed: number
  errors: string[]
}

interface DataUploadProps {
  onUploadComplete?: (response: UploadResponse) => void
}

export default function DataUpload({ onUploadComplete }: DataUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadType, setUploadType] = useState('demand')
  const [brandId, setBrandId] = useState('')
  const [response, setResponse] = useState<UploadResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setResponse(null)

    const formData = new FormData()
    formData.append('file', file)
    
    if (uploadType === 'demand') {
      formData.append('brand_id', brandId)
    }

    try {
      const endpoint = `/api/data/upload/${uploadType}`
      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      const data = await res.json()
      setResponse(data)
      onUploadComplete?.(data)
    } catch (error) {
      setResponse({
        success: false,
        message: 'Upload failed',
        records_processed: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      })
    } finally {
      setUploading(false)
    }
  }

  const downloadTemplate = (dataType: string) => {
    // In a real app, this would download the actual template
    const templates = {
      demand: 'demand_data_template.csv',
      brand: 'brand_data_template.csv',
      geo: 'geo_data_template.csv',
      pricing: 'pricing_data_template.csv'
    }
    
    const filename = templates[dataType as keyof typeof templates]
    const link = document.createElement('a')
    link.href = `/templates/${filename}`
    link.download = filename
    link.click()
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Data Upload</h2>
      
      {/* Upload Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Data Type
        </label>
        <select
          value={uploadType}
          onChange={(e) => setUploadType(e.target.value)}
          className="input"
        >
          <option value="demand">Demand Data</option>
          <option value="brand">Brand Data</option>
          <option value="geo">Geography Data</option>
          <option value="pricing">Pricing Data</option>
        </select>
      </div>

      {/* Brand ID for Demand Data */}
      {uploadType === 'demand' && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Brand ID
          </label>
          <input
            type="text"
            value={brandId}
            onChange={(e) => setBrandId(e.target.value)}
            placeholder="e.g., BRAND_A"
            className="input"
            required
          />
        </div>
      )}

      {/* File Upload */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload File
        </label>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            Click to upload or drag and drop
          </p>
          <p className="text-sm text-gray-500">
            CSV, XLSX, XLS files only
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-primary mt-4"
          >
            {uploading ? 'Uploading...' : 'Choose File'}
          </button>
        </div>
      </div>

      {/* Template Download */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Download Template</h3>
        <button
          onClick={() => downloadTemplate(uploadType)}
          className="btn-secondary flex items-center"
        >
          <Download className="h-4 w-4 mr-2" />
          Download {uploadType} template
        </button>
      </div>

      {/* Upload Response */}
      {response && (
        <div className={`p-4 rounded-lg ${
          response.success 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center mb-2">
            {response.success ? (
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            )}
            <span className={`font-medium ${
              response.success ? 'text-green-800' : 'text-red-800'
            }`}>
              {response.message}
            </span>
          </div>
          
          {response.records_processed > 0 && (
            <p className="text-sm text-gray-600 mb-2">
              Records processed: {response.records_processed}
            </p>
          )}
          
          {response.errors && response.errors.length > 0 && (
            <div className="mt-2">
              <p className="text-sm font-medium text-red-800 mb-1">Errors:</p>
              <ul className="text-sm text-red-700 list-disc list-inside">
                {response.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
