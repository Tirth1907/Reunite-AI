import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Users, GitCompare, CheckCircle, Clock, MapPin, Plus, Search, Loader2 } from 'lucide-react';
import { getStatistics, getCases, type Statistics, type Case } from '@/app/services/api';

export default function Home() {
  const [stats, setStats] = useState<Statistics>({
    totalRegistered: 0,
    foundCases: 0,
    activeCases: 0,
    aiMatches: 0,
  });
  const [recentCases, setRecentCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      setError(null);

      try {
        const [statsData, casesData] = await Promise.all([
          getStatistics(),
          getCases({ limit: 5 }),
        ]);

        setStats(statsData);
        setRecentCases(casesData);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Failed to load dashboard data. Please check if the backend is running.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: '#1e1b4b' }} />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Welcome to Reunite AI</h1>
        <p className="text-gray-600">Your dashboard for finding and reuniting missing persons</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#1e1b4b' }}>
              <FileText className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-bold" style={{ color: '#1e1b4b' }}>
              {stats.totalRegistered.toLocaleString()}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Total Registered Cases</h3>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#10b981' }}>
              <CheckCircle className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-bold" style={{ color: '#10b981' }}>
              {stats.foundCases.toLocaleString()}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Found Cases</h3>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#ef4444' }}>
              <Users className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-bold" style={{ color: '#ef4444' }}>
              {stats.activeCases.toLocaleString()}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Active Cases</h3>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#f59e0b' }}>
              <GitCompare className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-bold" style={{ color: '#f59e0b' }}>
              {stats.aiMatches.toLocaleString()}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">AI Matches</h3>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Link
          to="/dashboard/register-case"
          className="bg-white rounded-xl p-8 shadow-lg border-2 border-transparent hover:shadow-xl transition-all"
          style={{ borderColor: '#1e1b4b' }}
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#1e1b4b' }}>
              <Plus className="h-7 w-7 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold" style={{ color: '#1e1b4b' }}>Register New Case</h3>
              <p className="text-gray-600">Report a missing person</p>
            </div>
          </div>
          <p className="text-gray-600">
            Register a new missing person case with photo and details to help find them quickly
          </p>
        </Link>

        <Link
          to="/dashboard/match-cases"
          className="bg-white rounded-xl p-8 shadow-lg border-2 border-transparent hover:shadow-xl transition-all"
          style={{ borderColor: '#f59e0b' }}
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#f59e0b' }}>
              <Search className="h-7 w-7 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold" style={{ color: '#f59e0b' }}>Run AI Matching</h3>
              <p className="text-gray-600">Check for potential matches</p>
            </div>
          </div>
          <p className="text-gray-600">
            Use AI-powered facial recognition to match sightings with registered missing persons
          </p>
        </Link>
      </div>

      {/* Recently Added Cases */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>Recently Added Cases</h2>
          <Link
            to="/dashboard/all-cases"
            className="text-sm font-medium hover:underline"
            style={{ color: '#1e1b4b' }}
          >
            View All Cases →
          </Link>
        </div>

        {recentCases.length === 0 ? (
          <div className="bg-white rounded-lg p-8 shadow-md border border-gray-200 text-center">
            <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No cases registered yet</h3>
            <p className="text-gray-600 mb-4">Start by registering your first missing person case</p>
            <Link
              to="/dashboard/register-case"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white"
              style={{ backgroundColor: '#1e1b4b' }}
            >
              <Plus className="h-5 w-5" />
              Register New Case
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {recentCases.map((caseItem) => (
              <div
                key={caseItem.id}
                className="bg-white rounded-lg p-4 shadow-md border border-gray-200 hover:shadow-lg transition-shadow"
              >
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div
                      className="w-24 h-24 rounded-lg bg-gray-200 flex items-center justify-center"
                      style={{
                        backgroundImage: caseItem.photo_url ? `url(http://localhost:8000${caseItem.photo_url})` : 'none',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                      }}
                    >
                      {!caseItem.photo_url && <Users className="h-8 w-8 text-gray-400" />}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-lg" style={{ color: '#1e1b4b' }}>{caseItem.name}</h3>
                        <p className="text-sm text-gray-600">{caseItem.age} years old</p>
                      </div>
                      {caseItem.status === 'F' ? (
                        <span className="px-3 py-1 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#10b981' }}>
                          Found
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#ef4444' }}>
                          Missing
                        </span>
                      )}
                    </div>
                    <div className="space-y-1 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">Last seen: {caseItem.last_seen}</span>
                      </div>
                      {caseItem.submitted_on && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 flex-shrink-0" />
                          <span>Registered on {new Date(caseItem.submitted_on).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
