import { useState } from 'react';
import { Upload, User, FileText, Phone, CheckCircle, ArrowLeft, ArrowRight, X, Loader2 } from 'lucide-react';
import { registerCase } from '@/app/services/api';
import { useAuth } from '@/app/context/AuthContext';

type Step = 1 | 2 | 3 | 4;

interface CaseFormData {
  photo: string | null;
  fullName: string;
  age: string;
  gender: string;
  fatherName: string;
  identificationMarks: string;
  lastSeenDate: string;
  lastSeenLocation: string;
  city: string;
  state: string;
  clothingWorn: string;
  medicalConditions: string;
  languagesSpoken: string;
  additionalNotes: string;
  reporterName: string;
  reporterRelation: string;
  reporterPhone: string;
  reporterAlternatePhone: string;
  reporterAddress: string;
  firDetails: string;
}

export default function RegisterCase() {
  const { user } = useAuth();
  const [step, setStep] = useState<Step>(1);
  const [showSuccess, setShowSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [registeredCaseId, setRegisteredCaseId] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [formData, setFormData] = useState<CaseFormData>({
    photo: null,
    fullName: '',
    age: '',
    gender: 'male',
    fatherName: '',
    identificationMarks: '',
    lastSeenDate: '',
    lastSeenLocation: '',
    city: '',
    state: '',
    clothingWorn: '',
    medicalConditions: '',
    languagesSpoken: '',
    additionalNotes: '',
    reporterName: '',
    reporterRelation: '',
    reporterPhone: '',
    reporterAlternatePhone: '',
    reporterAddress: '',
    firDetails: ''
  });

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPhotoFile(file);  // Store the actual file for API upload
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, photo: reader.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleNext = () => {
    if (step < 4) setStep((step + 1) as Step);
  };

  const handleBack = () => {
    if (step > 1) setStep((step - 1) as Step);
  };

  const handleSubmit = async () => {
    if (!photoFile) {
      setSubmitError('Please upload a photo');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Create FormData for API submission
      const apiFormData = new FormData();
      apiFormData.append('photo', photoFile);
      apiFormData.append('name', formData.fullName);
      apiFormData.append('age', formData.age);
      apiFormData.append('father_name', formData.fatherName);
      apiFormData.append('last_seen', `${formData.lastSeenLocation}, ${formData.city}, ${formData.state} on ${formData.lastSeenDate}`);
      apiFormData.append('address', formData.reporterAddress);
      apiFormData.append('complainant_name', formData.reporterName);
      apiFormData.append('complainant_mobile', formData.reporterPhone);
      apiFormData.append('birth_marks', formData.identificationMarks);
      apiFormData.append('submitted_by', user?.name || 'Admin');

      const result = await registerCase(apiFormData);
      setRegisteredCaseId(result.id);
      setShowSuccess(true);
    } catch (err) {
      console.error('Failed to register case:', err);
      setSubmitError(err instanceof Error ? err.message : 'Failed to register case');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setShowSuccess(false);
    setStep(1);
    setPhotoFile(null);
    setSubmitError(null);
    setRegisteredCaseId(null);
    setFormData({
      photo: null,
      fullName: '',
      age: '',
      gender: 'male',
      fatherName: '',
      identificationMarks: '',
      lastSeenDate: '',
      lastSeenLocation: '',
      city: '',
      state: '',
      clothingWorn: '',
      medicalConditions: '',
      languagesSpoken: '',
      additionalNotes: '',
      reporterName: '',
      reporterRelation: '',
      reporterPhone: '',
      reporterAlternatePhone: '',
      reporterAddress: '',
      firDetails: ''
    });
  };

  if (showSuccess) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center" style={{ backgroundColor: '#10b981' }}>
            <CheckCircle className="h-12 w-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold mb-4" style={{ color: '#1e1b4b' }}>Case Registered Successfully!</h1>
          <p className="text-gray-600 mb-2">Case ID: <span className="font-mono font-bold text-lg">{registeredCaseId}</span></p>
          <p className="text-gray-600 mb-8">
            The case has been registered and will be processed by our AI matching system.
            You will be notified of any matches or updates.
          </p>
          <button
            onClick={resetForm}
            className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
            style={{ backgroundColor: '#1e1b4b' }}
          >
            Register Another Case
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Register New Missing Person Case</h1>
        <p className="text-gray-600">Please provide accurate and complete information to help locate the missing person</p>
      </div>

      {/* Progress Steps */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((s, idx) => (
            <div key={s} className="flex items-center flex-1">
              <div className="flex items-center gap-2">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-colors ${step >= s ? 'text-white' : 'text-gray-400 border-2 border-gray-300'
                    }`}
                  style={step >= s ? { backgroundColor: '#1e1b4b' } : {}}
                >
                  {s}
                </div>
                <span className={`hidden md:block text-sm font-medium ${step >= s ? 'text-gray-900' : 'text-gray-400'}`}>
                  {s === 1 && 'Photo'}
                  {s === 2 && 'Personal Details'}
                  {s === 3 && 'Reporter Info'}
                  {s === 4 && 'Review'}
                </span>
              </div>
              {idx < 3 && (
                <div className={`flex-1 h-1 mx-2 ${step > s ? 'bg-indigo-900' : 'bg-gray-300'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        {/* Step 1: Photo Upload */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#1e1b4b' }}>Upload Photo</h2>
              <p className="text-gray-600 mb-6">Upload a clear, recent photo of the missing person</p>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
              {formData.photo ? (
                <div className="relative">
                  <img src={formData.photo} alt="Uploaded" className="max-w-md mx-auto rounded-lg" />
                  <button
                    onClick={() => setFormData({ ...formData, photo: null })}
                    className="absolute top-2 right-2 p-2 bg-red-500 rounded-full text-white hover:bg-red-600"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ) : (
                <label className="flex flex-col items-center cursor-pointer">
                  <Upload className="h-16 w-16 text-gray-400 mb-4" />
                  <span className="text-gray-600 mb-2">Click to upload or drag and drop</span>
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
        )}

        {/* Step 2: Personal Details */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#1e1b4b' }}>Personal Details</h2>
              <p className="text-gray-600 mb-6">Provide detailed information about the missing person</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Enter full name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Age *</label>
                <input
                  type="number"
                  required
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Age in years"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Gender *</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Father's/Guardian's Name</label>
                <input
                  type="text"
                  value={formData.fatherName}
                  onChange={(e) => setFormData({ ...formData, fatherName: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Enter name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Last Seen Date *</label>
                <input
                  type="date"
                  required
                  value={formData.lastSeenDate}
                  onChange={(e) => setFormData({ ...formData, lastSeenDate: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Last Seen Location *</label>
                <input
                  type="text"
                  required
                  value={formData.lastSeenLocation}
                  onChange={(e) => setFormData({ ...formData, lastSeenLocation: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Specific location"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
                <input
                  type="text"
                  required
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="City name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">State *</label>
                <input
                  type="text"
                  required
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="State name"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Clothing Worn</label>
                <input
                  type="text"
                  value={formData.clothingWorn}
                  onChange={(e) => setFormData({ ...formData, clothingWorn: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Description of clothing"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Identification Marks</label>
                <input
                  type="text"
                  value={formData.identificationMarks}
                  onChange={(e) => setFormData({ ...formData, identificationMarks: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Scars, birthmarks, tattoos, etc."
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Medical Conditions</label>
                <input
                  type="text"
                  value={formData.medicalConditions}
                  onChange={(e) => setFormData({ ...formData, medicalConditions: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Any medical conditions or medications"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Languages Spoken</label>
                <input
                  type="text"
                  value={formData.languagesSpoken}
                  onChange={(e) => setFormData({ ...formData, languagesSpoken: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="e.g., Hindi, English, Tamil"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
                <textarea
                  value={formData.additionalNotes}
                  onChange={(e) => setFormData({ ...formData, additionalNotes: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Any other relevant information"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Reporter Information */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#1e1b4b' }}>Reporter Information</h2>
              <p className="text-gray-600 mb-6">Contact details of the person reporting this case</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Your Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.reporterName}
                  onChange={(e) => setFormData({ ...formData, reporterName: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Enter your name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Relationship to Missing Person *</label>
                <input
                  type="text"
                  required
                  value={formData.reporterRelation}
                  onChange={(e) => setFormData({ ...formData, reporterRelation: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="e.g., Father, Mother, Spouse"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Primary Phone Number *</label>
                <input
                  type="tel"
                  required
                  value={formData.reporterPhone}
                  onChange={(e) => setFormData({ ...formData, reporterPhone: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Alternate Phone Number</label>
                <input
                  type="tel"
                  value={formData.reporterAlternatePhone}
                  onChange={(e) => setFormData({ ...formData, reporterAlternatePhone: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="+91 98765 43211"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Residential Address *</label>
                <textarea
                  required
                  value={formData.reporterAddress}
                  onChange={(e) => setFormData({ ...formData, reporterAddress: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="Complete address with city and state"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">FIR / Police Complaint Details (Optional)</label>
                <input
                  type="text"
                  value={formData.firDetails}
                  onChange={(e) => setFormData({ ...formData, firDetails: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                  style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                  placeholder="FIR number and police station"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#1e1b4b' }}>Review & Submit</h2>
              <p className="text-gray-600 mb-6">Please review all information before submitting</p>
            </div>

            <div className="space-y-4">
              {formData.photo && (
                <div>
                  <h3 className="font-bold mb-2" style={{ color: '#1e1b4b' }}>Photo</h3>
                  <img src={formData.photo} alt="Missing person" className="max-w-xs rounded-lg border border-gray-200" />
                </div>
              )}

              <div>
                <h3 className="font-bold mb-2" style={{ color: '#1e1b4b' }}>Personal Information</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm bg-gray-100 p-4 rounded-lg border border-gray-200">
                  <div><span className="text-gray-600">Name:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.fullName}</span></div>
                  <div><span className="text-gray-600">Age:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.age} years</span></div>
                  <div><span className="text-gray-600">Gender:</span> <span className="font-medium capitalize block" style={{ color: '#1e1b4b' }}>{formData.gender}</span></div>
                  <div><span className="text-gray-600">Last Seen:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.lastSeenDate}</span></div>
                  <div><span className="text-gray-600">Location:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.lastSeenLocation}</span></div>
                  <div><span className="text-gray-600">City:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.city}, {formData.state}</span></div>
                </div>
              </div>

              <div>
                <h3 className="font-bold mb-2" style={{ color: '#1e1b4b' }}>Reporter Information</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm bg-gray-100 p-4 rounded-lg border border-gray-200">
                  <div><span className="text-gray-600">Name:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.reporterName}</span></div>
                  <div><span className="text-gray-600">Relation:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.reporterRelation}</span></div>
                  <div><span className="text-gray-600">Phone:</span> <span className="font-medium block" style={{ color: '#1e1b4b' }}>{formData.reporterPhone}</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          {step > 1 ? (
            <button
              onClick={handleBack}
              className="px-6 py-3 rounded-lg border-2 font-medium transition-all hover:shadow-md flex items-center gap-2"
              style={{ borderColor: '#1e1b4b', color: '#1e1b4b' }}
            >
              <ArrowLeft className="h-5 w-5" />
              Back
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              onClick={handleNext}
              className="px-6 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg flex items-center gap-2"
              style={{ backgroundColor: '#1e1b4b' }}
            >
              Next
              <ArrowRight className="h-5 w-5" />
            </button>
          ) : (
            <div className="flex flex-col items-end gap-2">
              {submitError && (
                <p className="text-red-500 text-sm">{submitError}</p>
              )}
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-8 py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: '#10b981' }}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-5 w-5" />
                    Submit Case
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
