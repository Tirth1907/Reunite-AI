import { useEffect, useState } from 'react';
import { RefreshCw, AlertCircle, CheckCircle, MapPin, Calendar, TrendingUp, Info, AlertTriangle } from 'lucide-react';
import { runMatching, getCase, getPublicSubmission, type Case, type PublicSubmission, confirmMatch, getRecentMatches } from '@/app/services/api';

const API_BASE = 'http://localhost:8000';

interface ExpandedMatch {
  id: string; // Composite ID
  registered: Case;
  sighting: PublicSubmission;
  confidence: number;
  distance: number;
}

export default function MatchCases() {
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState<ExpandedMatch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [processingMatch, setProcessingMatch] = useState<string | null>(null);

  // Fetch stored matches on mount
  useEffect(() => {
    fetchStoredMatches();
  }, []);

  const fetchStoredMatches = async () => {
    setLoading(true);
    try {
      const stored = await getRecentMatches();
      const formatted: ExpandedMatch[] = [];

      for (const m of stored) {
        if (!m.matched_with || !m.id) continue;

        // We have the registered case (m) and the public ID (m.matched_with)
        try {
          const publicSubmission = await getPublicSubmission(m.matched_with);
          formatted.push({
            id: `${m.id}-${m.matched_with}`,
            registered: m,
            sighting: publicSubmission,
            confidence: 90, // Stored matches are always high confidence
            distance: 0.1
          });
        } catch (e) {
          console.error("Failed to load details for match", e);
        }
      }
      setMatches(formatted);
    } catch (err) {
      console.error("Error fetching stored matches", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMatching = async () => {
    setLoading(true);
    setError(null);
    setMatches([]);

    try {
      const matchResult = await runMatching(0.60); // Use 0.60 tolerance

      if (!matchResult.status || !matchResult.result) {
        if (matchResult.message) setError(matchResult.message);
        setLoading(false);
        return;
      }

      const newMatches: ExpandedMatch[] = [];
      const result = matchResult.result;

      // Iterate through registered cases that have matches
      for (const [regId, publicMatches] of Object.entries(result)) {
        try {
          // Fetch registered case details
          const registeredCase = await getCase(regId);

          // For each public match for this case
          for (const match of publicMatches) {
            try {
              const publicSubmission = await getPublicSubmission(match.public_id);

              newMatches.push({
                id: `${regId}-${match.public_id}`,
                registered: registeredCase,
                sighting: publicSubmission,
                confidence: match.confidence,
                distance: match.distance
              });
            } catch (err) {
              console.error(`Failed to fetch public submission ${match.public_id}`, err);
            }
          }
        } catch (err) {
          console.error(`Failed to fetch registered case ${regId}`, err);
        }
      }

      setMatches(newMatches);

      if (newMatches.length === 0) {
        setError("No matches found above the confidence threshold.");
      }

    } catch (err) {
      console.error("Matching failed:", err);
      setError("Failed to run matching algorithm. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmMatch = async (match: ExpandedMatch) => {
    if (!confirm('Are you sure you want to confirm this match? This will mark both cases as FOUND.')) return;

    setProcessingMatch(match.id);
    try {
      await confirmMatch(match.registered.id, match.sighting.id);
      // Remove from list or mark verified
      alert('Match confirmed successfully!');
      setMatches(prev => prev.filter(m => m.id !== match.id));
    } catch (err) {
      alert('Failed to confirm match');
    } finally {
      setProcessingMatch(null);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#10b981'; // green
    if (confidence >= 60) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>AI-Powered Face Matching</h1>
        <p className="text-gray-600">Advanced facial recognition (ArcFace) to match sightings with missing persons</p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex gap-4">
          <Info className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-bold text-blue-900 mb-2">How AI Matching Works</h3>
            <p className="text-blue-800 text-sm leading-relaxed">
              Our system uses <b>DeepFace (ArcFace)</b> to compare facial features.
              It is robust against lighting changes and can recognize faces from a distance.
              A confidence score indicates the similarity found.
            </p>
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold mb-1" style={{ color: '#1e1b4b' }}>
              Run Matching Algorithm
            </h2>
            <p className="text-sm text-gray-600">
              Click to scan recent sightings and find potential matches
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => fetchStoredMatches()}
              className="px-4 py-3 rounded-lg border-2 font-medium hover:bg-gray-50 text-gray-700"
              style={{ borderColor: '#1e1b4b' }}
            >
              Refresh List
            </button>
            <button
              onClick={handleRunMatching}
              disabled={loading}
              className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#1e1b4b' }}
            >
              {loading ? (
                <>
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-5 w-5" />
                  Find Matches
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <p className="text-amber-800">{error}</p>
          </div>
        )}

        {/* Results */}
        {!loading && matches.length > 0 && (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>
                Potential Matches Found: {matches.length}
              </h2>
            </div>

            <div className="space-y-6">
              {matches.map((match) => (
                <div
                  key={match.id}
                  className="bg-white rounded-xl shadow-lg border-2 overflow-hidden hover:shadow-xl transition-shadow"
                  style={{ borderColor: getConfidenceColor(match.confidence) }}
                >
                  <div className="p-6">
                    {/* Match Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-xl font-bold mb-1" style={{ color: '#1e1b4b' }}>
                          Match Found
                        </h3>
                        <p className="text-sm text-gray-600">Reg ID: {match.registered.id} | Sighting ID: {match.sighting.id}</p>
                      </div>
                      <div className="text-right">
                        <div
                          className="text-3xl font-bold mb-1"
                          style={{ color: getConfidenceColor(match.confidence) }}
                        >
                          {match.confidence}%
                        </div>
                        <div
                          className="px-3 py-1 rounded-full text-sm font-medium text-white"
                          style={{ backgroundColor: getConfidenceColor(match.confidence) }}
                        >
                          {getConfidenceLabel(match.confidence)} Confidence
                        </div>
                      </div>
                    </div>

                    {/* Image Comparison */}
                    <div className="grid md:grid-cols-3 gap-6 mb-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Missing Person (Registered)</h4>
                        <div className="relative rounded-lg overflow-hidden aspect-square bg-gray-100">
                          {match.registered.photo_url ? (
                            <img
                              src={`${API_BASE}${match.registered.photo_url}`}
                              alt={match.registered.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">No Image</div>
                          )}
                          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-3">
                            <p className="text-white font-medium">{match.registered.name}</p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-center">
                        <div className="text-center">
                          <TrendingUp
                            className="h-12 w-12 mx-auto mb-2"
                            style={{ color: getConfidenceColor(match.confidence) }}
                          />
                          <p className="text-sm font-medium text-gray-700">Similarity Score</p>
                          <p className="text-xs text-gray-500">{match.distance.toFixed(4)} Distance</p>
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Sighting Photo</h4>
                        <div className="relative rounded-lg overflow-hidden aspect-square bg-gray-100">
                          {match.sighting.photo_url ? (
                            <img
                              src={`${API_BASE}${match.sighting.photo_url}`}
                              alt="Sighting"
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">No Image</div>
                          )}
                          <div className="absolute top-2 right-2">
                            <span className="px-2 py-1 rounded text-xs font-medium bg-white text-gray-900">
                              Public Sighting
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Details Grid */}
                    <div className="grid md:grid-cols-2 gap-6 mb-6 p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h4 className="font-bold mb-3" style={{ color: '#1e1b4b' }}>Missing Person Details</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-700">Last seen: {match.registered.last_seen}</span>
                          </div>
                          <div className="text-gray-700">
                            <span className="font-medium">Age:</span> {match.registered.age}
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-bold mb-3" style={{ color: '#1e1b4b' }}>Sighting Information</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-700">Location: {match.sighting.location}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-700">Submitted: {match.sighting.submitted_on ? new Date(match.sighting.submitted_on).toLocaleDateString() : 'Unknown'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-wrap gap-3">
                      <button
                        onClick={() => handleConfirmMatch(match)}
                        disabled={processingMatch === match.id}
                        className="flex-1 px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-md flex items-center justify-center gap-2"
                        style={{ backgroundColor: '#10b981' }}
                      >
                        {processingMatch === match.id ? (
                          <RefreshCw className="h-5 w-5 animate-spin" />
                        ) : (
                          <CheckCircle className="h-5 w-5" />
                        )}
                        Verify Match
                      </button>
                      <button
                        className="flex-1 px-6 py-3 rounded-lg font-medium transition-all hover:shadow-md border-2"
                        style={{ borderColor: '#1e1b4b', color: '#1e1b4b' }}
                      >
                        Contact Reporter ({match.sighting.mobile})
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {!loading && matches.length === 0 && !error && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">No matches found</h3>
            <p className="text-gray-600">Run the matching algorithm to find potential matches</p>
          </div>
        )}
      </div>
    </div>
  );
}
