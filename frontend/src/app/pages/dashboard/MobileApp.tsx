import { useState, useEffect } from 'react';
import { Smartphone, Upload, MapPin, Send, Search, CheckCircle, Clock, X, Eye, User, Loader2, AlertCircle } from 'lucide-react';
import { getCases, submitSighting, type Case } from '@/app/services/api';

const API_BASE = 'http://localhost:8000';

export default function MobileApp() {
  const [activeTab, setActiveTab] = useState<'browse' | 'submit' | 'track'>('browse');
  const [sightingPhoto, setSightingPhoto] = useState<string | null>(null);
  const [sightingLocation, setSightingLocation] = useState('');
  const [sightingDescription, setSightingDescription] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [referenceId, setReferenceId] = useState('');
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [mobileNumber, setMobileNumber] = useState('');
  const [trackingId, setTrackingId] = useState('');
  const [trackedSighting, setTrackedSighting] = useState<any>(null);

  // API data
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state for viewing case details
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);

  useEffect(() => {
    async function fetchCases() {
      setIsLoading(true);
      try {
        const data = await getCases();
        setCases(data);
      } catch (err) {
        setError('Failed to load missing persons');
      } finally {
        setIsLoading(false);
      }
    }
    fetchCases();
  }, []);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPhotoFile(file);  // Store the actual file for API upload
      const reader = new FileReader();
      reader.onloadend = () => {
        setSightingPhoto(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmitSighting = async () => {
    if (!photoFile || !sightingLocation) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const formData = new FormData();
      formData.append('photo', photoFile);
      formData.append('location', sightingLocation);
      formData.append('birth_marks', sightingDescription || '');
      formData.append('mobile', mobileNumber || 'Anonymous');
      formData.append('submitted_by', 'Public User');
      formData.append('email', '');

      const result = await submitSighting(formData);
      setReferenceId(result.id);
      setShowSuccess(true);
      setSightingPhoto(null);
      setPhotoFile(null);
      setSightingLocation('');
      setSightingDescription('');
      setMobileNumber('');
    } catch (err) {
      console.error('Sighting submission failed:', err);
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit sighting. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTrackSighting = () => {
    // Mock tracking - would connect to API in full implementation
    setTrackedSighting(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Mobile App Features</h1>
        <p className="text-gray-600">Empowering communities to help find missing persons</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('browse')}
              className={`flex-1 px-6 py-4 font-medium transition-colors border-b-2 ${activeTab === 'browse'
                ? 'border-indigo-900 text-indigo-900'
                : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
            >
              <Eye className="h-5 w-5 inline-block mr-2" />
              Browse Missing People
            </button>
            <button
              onClick={() => setActiveTab('submit')}
              className={`flex-1 px-6 py-4 font-medium transition-colors border-b-2 ${activeTab === 'submit'
                ? 'border-indigo-900 text-indigo-900'
                : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
            >
              <Upload className="h-5 w-5 inline-block mr-2" />
              Submit a Sighting
            </button>
            <button
              onClick={() => setActiveTab('track')}
              className={`flex-1 px-6 py-4 font-medium transition-colors border-b-2 ${activeTab === 'track'
                ? 'border-indigo-900 text-indigo-900'
                : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
            >
              <Search className="h-5 w-5 inline-block mr-2" />
              Track Sighting Status
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Browse Missing People Tab */}
          {activeTab === 'browse' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Browse Missing Persons</h3>
                <p className="text-gray-600">View all registered missing person cases. Click on a card to view full details.</p>
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#1e1b4b' }} />
                </div>
              ) : error ? (
                <div className="text-center py-8 text-red-500">{error}</div>
              ) : cases.length === 0 ? (
                <div className="text-center py-12">
                  <User className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No missing person cases registered yet</p>
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {cases.map((caseItem) => (
                    <div
                      key={caseItem.id}
                      className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => setSelectedCase(caseItem)}
                    >
                      <div className="h-48 overflow-hidden bg-gray-100">
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
                            <User className="h-16 w-16 text-gray-300" />
                          </div>
                        )}
                      </div>
                      <div className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold" style={{ color: '#1e1b4b' }}>{caseItem.name}</h4>
                          {caseItem.status === 'NF' && (
                            <span className="px-2 py-1 rounded-full text-xs font-medium text-white" style={{ backgroundColor: '#ef4444' }}>
                              Missing
                            </span>
                          )}
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <div>{caseItem.age} years old</div>
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            <span className="truncate">{caseItem.last_seen}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>Added: {caseItem.submitted_on ? new Date(caseItem.submitted_on).toLocaleDateString() : 'Recently'}</span>
                          </div>
                        </div>
                        <p className="text-xs text-indigo-600 mt-2">Click to view details →</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Submit Sighting Tab */}
          {activeTab === 'submit' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Submit a Sighting</h3>
                <p className="text-gray-600">Help reunite families by reporting sightings of missing persons</p>
              </div>

              {showSuccess ? (
                <div className="text-center py-8">
                  <div className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center" style={{ backgroundColor: '#10b981' }}>
                    <CheckCircle className="h-12 w-12 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Sighting Submitted Successfully!</h3>
                  <p className="text-gray-600 mb-2">
                    Your submission reference ID is: <span className="font-mono font-bold">{referenceId}</span>
                  </p>
                  <p className="text-gray-600 mb-6">
                    Save this ID to track the status of your sighting. Our AI will analyze the photo for potential matches.
                  </p>
                  <button
                    onClick={() => setShowSuccess(false)}
                    className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Submit Another Sighting
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Photo Upload */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Upload Photo *</label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
                      {sightingPhoto ? (
                        <div className="relative">
                          <img src={sightingPhoto} alt="Sighting" className="max-w-md mx-auto rounded-lg" />
                          <button
                            onClick={() => setSightingPhoto(null)}
                            className="absolute top-2 right-2 p-2 bg-red-500 rounded-full text-white hover:bg-red-600"
                          >
                            <X className="h-5 w-5" />
                          </button>
                        </div>
                      ) : (
                        <label className="flex flex-col items-center cursor-pointer">
                          <Upload className="h-12 w-12 text-gray-400 mb-3" />
                          <span className="text-gray-600 mb-1">Click to upload sighting photo</span>
                          <span className="text-sm text-gray-500">PNG, JPG up to 10MB</span>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handlePhotoUpload}
                            className="hidden"
                          />
                        </label>
                      )}
                    </div>
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <MapPin className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        value={sightingLocation}
                        onChange={(e) => setSightingLocation(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                        placeholder="Where did you see this person? (e.g., Connaught Place, Delhi)"
                      />
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <textarea
                      value={sightingDescription}
                      onChange={(e) => setSightingDescription(e.target.value)}
                      rows={4}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                      style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                      placeholder="Provide any additional details about the sighting..."
                    />
                  </div>

                  {/* Mobile Number */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number (Optional)</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Smartphone className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        type="tel"
                        value={mobileNumber}
                        onChange={(e) => setMobileNumber(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                        placeholder="Your contact number"
                      />
                    </div>
                  </div>

                  {submitError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
                      <AlertCircle className="h-5 w-5" />
                      <p>{submitError}</p>
                    </div>
                  )}

                  <button
                    onClick={handleSubmitSighting}
                    disabled={!sightingPhoto || !sightingLocation || isSubmitting}
                    className="w-full px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-5 w-5" />
                        Submit Sighting
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Track Status Tab */}
          {activeTab === 'track' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Track Sighting Status</h3>
                <p className="text-gray-600">Enter your reference ID to check the status of your submission</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reference ID</label>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={trackingId}
                    onChange={(e) => setTrackingId(e.target.value)}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                    style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                    placeholder="e.g., REF-2026-0001"
                  />
                  <button
                    onClick={handleTrackSighting}
                    className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    <Search className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {trackingId && !trackedSighting && (
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <Search className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No sighting found with this reference ID</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Case Details Modal */}
      {selectedCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[95vh] overflow-y-auto">
            <div className="relative">
              {/* Close button */}
              <button
                onClick={() => setSelectedCase(null)}
                className="absolute top-4 right-4 z-10 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
              >
                <X className="h-6 w-6 text-gray-700" />
              </button>

              {/* Full Image - Larger and fully visible */}
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

              {/* Details */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>{selectedCase.name}</h2>
                    <p className="text-gray-600">{selectedCase.age} years old</p>
                  </div>
                  {selectedCase.status === 'NF' ? (
                    <span className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#ef4444' }}>
                      Missing
                    </span>
                  ) : (
                    <span className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#10b981' }}>
                      Found
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
                      If you have any information about this person, please contact the authorities or use the "Submit a Sighting" feature.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => {
                      setSelectedCase(null);
                      setActiveTab('submit');
                    }}
                    className="flex-1 px-6 py-3 rounded-lg font-medium transition-all hover:shadow-lg border-2"
                    style={{ borderColor: '#1e1b4b', color: '#1e1b4b' }}
                  >
                    Report Sighting
                  </button>
                  <button
                    onClick={() => setSelectedCase(null)}
                    className="flex-1 px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
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
