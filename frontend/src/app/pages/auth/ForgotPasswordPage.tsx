import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Mail, Lock, KeyRound, CheckCircle, ArrowLeft } from 'lucide-react';

type Step = 'email' | 'otp' | 'password' | 'success';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('otp');
  };

  const handleOTPSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('password');
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('success');
  };

  const handleOTPChange = (index: number, value: string) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);

      // Auto-focus next input
      if (value && index < 5) {
        const nextInput = document.getElementById(`otp-${index + 1}`);
        nextInput?.focus();
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link to="/" className="flex items-center gap-2">
            <Heart className="h-8 w-8" style={{ color: '#1e1b4b' }} />
            <span className="text-xl font-bold" style={{ color: '#1e1b4b' }}>Reunite AI</span>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Progress Indicator */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <div className={`flex items-center gap-2 ${step === 'email' || step === 'otp' || step === 'password' || step === 'success' ? 'opacity-100' : 'opacity-50'}`}>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: '#1e1b4b' }}>
                    1
                  </div>
                  <span className="text-sm font-medium">Email</span>
                </div>
                <div className={`flex items-center gap-2 ${step === 'otp' || step === 'password' || step === 'success' ? 'opacity-100' : 'opacity-50'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'otp' || step === 'password' || step === 'success' ? 'text-white' : 'text-gray-400 border-2 border-gray-300'}`} style={step === 'otp' || step === 'password' || step === 'success' ? { backgroundColor: '#1e1b4b' } : {}}>
                    2
                  </div>
                  <span className="text-sm font-medium">OTP</span>
                </div>
                <div className={`flex items-center gap-2 ${step === 'password' || step === 'success' ? 'opacity-100' : 'opacity-50'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'password' || step === 'success' ? 'text-white' : 'text-gray-400 border-2 border-gray-300'}`} style={step === 'password' || step === 'success' ? { backgroundColor: '#1e1b4b' } : {}}>
                    3
                  </div>
                  <span className="text-sm font-medium">Reset</span>
                </div>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full transition-all duration-300"
                  style={{ 
                    backgroundColor: '#1e1b4b',
                    width: step === 'email' ? '33%' : step === 'otp' ? '66%' : '100%'
                  }}
                />
              </div>
            </div>

            {/* Step 1: Email */}
            {step === 'email' && (
              <>
                <div className="text-center mb-8">
                  <KeyRound className="h-12 w-12 mx-auto mb-4" style={{ color: '#1e1b4b' }} />
                  <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Forgot Password?</h1>
                  <p className="text-gray-600">Enter your email to receive a verification code</p>
                </div>

                <form onSubmit={handleEmailSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Mail className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                        placeholder="your.email@example.com"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Send Verification Code
                  </button>

                  <Link to="/login" className="flex items-center justify-center gap-2 text-sm hover:underline" style={{ color: '#1e1b4b' }}>
                    <ArrowLeft className="h-4 w-4" />
                    Back to Login
                  </Link>
                </form>
              </>
            )}

            {/* Step 2: OTP */}
            {step === 'otp' && (
              <>
                <div className="text-center mb-8">
                  <Mail className="h-12 w-12 mx-auto mb-4" style={{ color: '#1e1b4b' }} />
                  <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Enter Verification Code</h1>
                  <p className="text-gray-600">We've sent a 6-digit code to {email}</p>
                </div>

                <form onSubmit={handleOTPSubmit} className="space-y-6">
                  <div className="flex gap-2 justify-center">
                    {otp.map((digit, index) => (
                      <input
                        key={index}
                        id={`otp-${index}`}
                        type="text"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOTPChange(index, e.target.value)}
                        className="w-12 h-14 text-center text-xl font-bold border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                      />
                    ))}
                  </div>

                  <div className="text-center">
                    <button type="button" className="text-sm hover:underline" style={{ color: '#1e1b4b' }}>
                      Didn't receive code? Resend
                    </button>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Verify Code
                  </button>
                </form>
              </>
            )}

            {/* Step 3: New Password */}
            {step === 'password' && (
              <>
                <div className="text-center mb-8">
                  <Lock className="h-12 w-12 mx-auto mb-4" style={{ color: '#1e1b4b' }} />
                  <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Create New Password</h1>
                  <p className="text-gray-600">Choose a strong password for your account</p>
                </div>

                <form onSubmit={handlePasswordSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                      New Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Lock className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="newPassword"
                        type="password"
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                        placeholder="Enter new password"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Lock className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="confirmPassword"
                        type="password"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
                        style={{ '--tw-ring-color': '#1e1b4b' } as React.CSSProperties}
                        placeholder="Confirm new password"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Reset Password
                  </button>
                </form>
              </>
            )}

            {/* Step 4: Success */}
            {step === 'success' && (
              <>
                <div className="text-center">
                  <div className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center" style={{ backgroundColor: '#10b981' }}>
                    <CheckCircle className="h-12 w-12 text-white" />
                  </div>
                  <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Password Reset Successfully!</h1>
                  <p className="text-gray-600 mb-8">You can now sign in with your new password</p>

                  <button
                    onClick={() => navigate('/login')}
                    className="w-full py-3 rounded-lg text-white font-medium transition-all hover:shadow-lg"
                    style={{ backgroundColor: '#1e1b4b' }}
                  >
                    Go to Login
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
