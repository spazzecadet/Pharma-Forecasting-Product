'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  AlertTriangle,
  Activity,
  Brain,
  Shield,
  Zap,
  Upload,
  Settings,
  LogOut
} from 'lucide-react'

interface DashboardStats {
  totalBrands: number
  totalRuns: number
  successfulRuns: number
  avgAccuracy: number
  topPerformingBrand?: string
  recentActivity: Array<{
    run_id: string
    brand: string
    model: string
    status: string
    date: string
  }>
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token) {
      router.push('/login')
      return
    }
    
    if (userData) {
      setUser(JSON.parse(userData))
    }
    
    fetchDashboardData()
  }, [router])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/dashboard/portfolio', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }
      const data = await response.json()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-pharma-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Pharma Forecasting</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-green-500" />
                <span className="text-sm text-gray-600">Secure</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-blue-500" />
                <span className="text-sm text-gray-600">Live</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Welcome, {user?.username}</span>
              </div>
              <button
                onClick={() => router.push('/upload')}
                className="btn-secondary flex items-center"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Data
              </button>
              <button
                onClick={handleLogout}
                className="btn-secondary flex items-center"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-pharma-100 rounded-lg">
                <BarChart3 className="h-6 w-6 text-pharma-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Brands</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.totalBrands || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Forecast Runs</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.totalRuns || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats ? Math.round((stats.successfulRuns / stats.totalRuns) * 100) : 0}%
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats ? Math.round(stats.avgAccuracy) : 0}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Top Performing Brand */}
        {stats?.topPerformingBrand && (
          <div className="card mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Brand</h3>
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Best Accuracy</p>
                <p className="text-xl font-bold text-gray-900">{stats.topPerformingBrand}</p>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {stats?.recentActivity?.length ? (
              stats.recentActivity.map((activity, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-3 ${
                      activity.status === 'completed' ? 'bg-green-500' : 
                      activity.status === 'running' ? 'bg-blue-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {activity.brand} - {activity.model}
                      </p>
                      <p className="text-xs text-gray-500">{activity.date}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    activity.status === 'completed' ? 'bg-green-100 text-green-800' :
                    activity.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {activity.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">No recent activity</p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
