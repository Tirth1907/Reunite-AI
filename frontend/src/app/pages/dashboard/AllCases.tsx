import { useState, useEffect } from 'react';
import { Search, Filter, MapPin, Clock, User, Calendar, Loader2, X } from 'lucide-react';
import { getCases, deleteCase, type Case } from '@/app/services/api';
import { toast } from 'sonner';

const API_BASE = 'http://localhost:8000';

export default function AllCases() {
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'found' | 'not-found'>('all');
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);

  useEffect(() => {
    async function fetchCases() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getCases({ status: 'All' });
        setCases(data);
      } catch (err) {
        console.error('Failed to fetch cases:', err);
        setError('Failed to load cases. Please check if the backend is running.');
      } finally {
        setIsLoading(false);
      }
    }
    fetchCases();
  }, []);

  const handleDelete = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this case? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteCase(caseId);
      setCases(cases.filter(c => c.id !== caseId));
      if (selectedCase?.id === caseId) {
        setSelectedCase(null);
      }
      toast.success('Case deleted successfully');
    } catch (err) {
      console.error('Failed to delete case:', err);
      toast.error('Failed to delete case');
    }
  };

  // Filter cases based on search and status
  const filteredCases = cases.filter(caseItem => {
    const searchLower = searchQuery.toLowerCase();
    const nameMatch = caseItem.name.toLowerCase().includes(searchLower);
    const lastSeenMatch = caseItem.last_seen ? caseItem.last_seen.toLowerCase().includes(searchLower) : false;

    const matchesSearch = nameMatch || lastSeenMatch;

    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'found' && caseItem.status === 'F') ||
      (statusFilter === 'not-found' && caseItem.status === 'NF');

    return matchesSearch && matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: '#1e1b4b' }} />
          <p className="text-gray-600">Loading cases...</p>
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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>All Missing Person Cases</h1>
        <p className="text-gray-600">Browse and search through all registered cases</p>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                placeholder="Search by name, city, or state..."
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Filter className="h-5 w-5 text-gray-400" />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as 'all' | 'found' | 'not-found')}
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent appearance-none"
                style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
              >
                <option value="all">All Cases</option>
                <option value="not-found">Missing</option>
                <option value="found">Found</option>
              </select>
            </div>
          </div>

          {/* Date Range (simplified) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Date</label>
            <button
              className="w-full px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-left text-gray-700 flex items-center gap-2"
            >
              <Calendar className="h-5 w-5 text-gray-400" />
              <span>All Dates</span>
            </button>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-gray-600">
          Showing <span className="font-bold" style={{ color: '#1e1b4b' }}>{filteredCases.length}</span> of {cases.length} cases
        </p>
      </div>

      {/* Cases Grid */}
      {filteredCases.length === 0 ? (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <Search className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">No cases found</h3>
          <p className="text-gray-600">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCases.map((caseItem) => (
            <div
              key={caseItem.id}
              className="bg-white rounded-xl overflow-hidden shadow-lg border border-gray-200 hover:shadow-xl transition-shadow cursor-pointer"
              onClick={() => setSelectedCase(caseItem)}
            >
              <div className="h-64 overflow-hidden bg-gray-100">
                {caseItem.photo_url ? (
                  <img
                    src={`${API_BASE}${caseItem.photo_url}`}
                    alt={caseItem.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <User className="h-20 w-20 text-gray-300" />
                  </div>
                )}
              </div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-xl font-bold" style={{ color: '#1e1b4b' }}>{caseItem.name}</h3>
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

                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="h-4 w-4 flex-shrink-0" />
                    <span className="truncate">{caseItem.last_seen}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock className="h-4 w-4 flex-shrink-0" />
                    <span>Last seen: {caseItem.submitted_on ? new Date(caseItem.submitted_on).toLocaleDateString() : 'Unknown'}</span>
                  </div>
                </div>

                {caseItem.birth_marks && (
                  <div className="pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-700 line-clamp-2">
                      {caseItem.birth_marks}
                    </p>
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCase(caseItem);
                    }}
                    className="flex-1 px-4 py-2 rounded-lg text-white font-medium transition-all hover:shadow-md"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    View Details
                  </button>
                  <button
                    onClick={(e) => e.stopPropagation()}
                    className="px-4 py-2 border-2 rounded-lg font-medium transition-all hover:shadow-md"
                    style={{ borderColor: '#1e1b4b', color: '#1e1b4b' }}
                  >
                    Share
                  </button>
                  <button
                    onClick={(e) => handleDelete(caseItem.id, e)}
                    className="px-4 py-2 border-2 rounded-lg font-medium transition-all hover:shadow-md hover:bg-red-50 text-red-600 border-red-600"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Case Details Modal */}
      {selectedCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[95vh] overflow-y-auto">
            <div className="relative">
              <button
                onClick={() => setSelectedCase(null)}
                className="absolute top-4 right-4 z-10 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
              >
                <X className="h-6 w-6 text-gray-700" />
              </button>

              <div className="w-full min-h-[300px] max-h-[50vh] bg-gray-100 flex items-center justify-center">
                {selectedCase.photo_url ? (
                  <img
                    src={`${API_BASE}${selectedCase.photo_url}`}
                    alt={selectedCase.name}
                    className="w-full h-full object-contain max-h-[50vh]"
                  />
                ) : (
                  <div className="w-full h-64 flex items-center justify-center">
                    <User className="h-24 w-24 text-gray-300" />
                  </div>
                )}
              </div>

              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>{selectedCase.name}</h2>
                    <p className="text-gray-600">{selectedCase.age} years old</p>
                  </div>
                  {selectedCase.status === 'F' ? (
                    <span className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#10b981' }}>
                      Found
                    </span>
                  ) : (
                    <span className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#ef4444' }}>
                      Missing
                    </span>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <p className="text-sm text-gray-500 mb-1">Last Seen Location</p>
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-gray-600 flex-shrink-0 mt-0.5" />
                        <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.last_seen}</p>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <p className="text-sm text-gray-500 mb-1">Date Added</p>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-600 flex-shrink-0" />
                        <p className="font-medium" style={{ color: '#1e1b4b' }}>
                          {selectedCase.submitted_on ? new Date(selectedCase.submitted_on).toLocaleDateString() : 'Unknown'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedCase.father_name && (
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <p className="text-sm text-gray-500 mb-1">Father/Guardian</p>
                        <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.father_name}</p>
                      </div>
                    )}
                    {selectedCase.address && (
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <p className="text-sm text-gray-500 mb-1">Residential Address</p>
                        <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.address}</p>
                      </div>
                    )}
                  </div>

                  {selectedCase.birth_marks && (
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <p className="text-sm text-gray-500 mb-1">Identification Marks</p>
                      <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.birth_marks}</p>
                    </div>
                  )}

                  {(selectedCase.complainant_name || selectedCase.complainant_mobile) && (
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <p className="text-sm text-gray-500 mb-1">Reporter Contact</p>
                      <div className="flex flex-col gap-1">
                        {selectedCase.complainant_name && <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.complainant_name}</p>}
                        {selectedCase.complainant_mobile && <p className="font-medium" style={{ color: '#1e1b4b' }}>{selectedCase.complainant_mobile}</p>}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-600">
                      If you have any information about this person, please contact the authorities.
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedCase(null)}
                    className="w-full mt-2 px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
