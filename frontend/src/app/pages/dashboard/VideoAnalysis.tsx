import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Video, Upload, Search, Clock, MapPin, CheckCircle, AlertCircle,
    Loader2, ChevronRight, Camera, Shield, X
} from 'lucide-react';
import {
    getCases, uploadVideo, getVideoStatus, getVideoResults,
    type Case, type VideoStatus, type Detection, type VideoResults
} from '@/app/services/api';

type Phase = 'upload' | 'processing' | 'results';

export default function VideoAnalysis() {
    // ---- State ----
    const [phase, setPhase] = useState<Phase>('upload');

    // Upload phase
    const [cases, setCases] = useState<Case[]>([]);
    const [loadingCases, setLoadingCases] = useState(true);
    const [selectedCaseId, setSelectedCaseId] = useState('');
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [videoLocation, setVideoLocation] = useState('');
    const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [dragOver, setDragOver] = useState(false);

    // Processing phase
    const [videoId, setVideoId] = useState<string | null>(null);
    const [status, setStatus] = useState<VideoStatus | null>(null);
    const pollRef = useRef<number | null>(null);

    // Results phase
    const [results, setResults] = useState<VideoResults | null>(null);
    const [loadingResults, setLoadingResults] = useState(false);

    // ---- Load cases on mount ----
    useEffect(() => {
        async function loadCases() {
            try {
                const data = await getCases({ status: 'NF' });
                setCases(data);
            } catch (err) {
                console.error('Failed to load cases:', err);
            } finally {
                setLoadingCases(false);
            }
        }
        loadCases();
    }, []);

    // ---- Cleanup polling on unmount ----
    useEffect(() => {
        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
            }
        };
    }, []);

    // ---- Poll for processing status ----
    const startPolling = useCallback((vid: string) => {
        if (pollRef.current) clearInterval(pollRef.current);

        const poll = async () => {
            try {
                const s = await getVideoStatus(vid);
                setStatus(s);

                if (s.status === 'done') {
                    if (pollRef.current) clearInterval(pollRef.current);
                    // Load results
                    setLoadingResults(true);
                    try {
                        const r = await getVideoResults(selectedCaseId || s.video_id);
                        setResults(r);
                        setPhase('results');
                    } catch (err) {
                        console.error('Failed to load results:', err);
                    } finally {
                        setLoadingResults(false);
                    }
                } else if (s.status === 'failed') {
                    if (pollRef.current) clearInterval(pollRef.current);
                }
            } catch (err) {
                console.error('Status poll failed:', err);
            }
        };

        poll(); // Immediately
        pollRef.current = window.setInterval(poll, 3000);
    }, [selectedCaseId]);

    // ---- Handle upload ----
    const handleUpload = async () => {
        if (!videoFile || !selectedCaseId) return;

        setUploading(true);
        setUploadError(null);

        try {
            const formData = new FormData();
            formData.append('video', videoFile);
            formData.append('case_id', selectedCaseId);
            formData.append('video_location', videoLocation);
            formData.append('confidence_threshold', confidenceThreshold.toString());

            const response = await uploadVideo(formData);
            setVideoId(response.video_id);
            setPhase('processing');
            startPolling(response.video_id);
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Upload failed';
            setUploadError(errorMsg);
        } finally {
            setUploading(false);
        }
    };

    // ---- Drag & drop handlers ----
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = () => setDragOver(false);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file && isValidVideoFile(file)) {
            setVideoFile(file);
        }
    };

    const isValidVideoFile = (file: File) => {
        const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/x-matroska', 'video/quicktime', 'video/x-ms-wmv'];
        return validTypes.includes(file.type) || /\.(mp4|avi|mkv|mov|wmv)$/i.test(file.name);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) setVideoFile(file);
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    };

    const selectedCase = cases.find(c => c.id === selectedCaseId);

    const resetToUpload = () => {
        setPhase('upload');
        setVideoFile(null);
        setVideoId(null);
        setStatus(null);
        setResults(null);
        setUploadError(null);
        setVideoLocation('');
        if (pollRef.current) clearInterval(pollRef.current);
    };

    // =======================================================================
    // RENDER
    // =======================================================================
    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold mb-1" style={{ color: '#1e1b4b' }}>
                        CCTV Video Analysis
                    </h1>
                    <p className="text-gray-600">
                        Upload CCTV footage and scan for a missing person using AI
                    </p>
                </div>
                {phase !== 'upload' && (
                    <button
                        onClick={resetToUpload}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-white transition-colors hover:opacity-90"
                        style={{ backgroundColor: '#1e1b4b' }}
                    >
                        <Upload className="h-4 w-4" />
                        New Analysis
                    </button>
                )}
            </div>

            {/* Phase Indicator */}
            <div className="bg-white rounded-xl p-4 shadow-md border border-gray-200">
                <div className="flex items-center justify-between">
                    {[
                        { key: 'upload', label: 'Upload Video', icon: Upload },
                        { key: 'processing', label: 'AI Processing', icon: Search },
                        { key: 'results', label: 'View Results', icon: CheckCircle },
                    ].map((step, idx) => {
                        const Icon = step.icon;
                        const isActive = step.key === phase;
                        const isDone =
                            (step.key === 'upload' && (phase === 'processing' || phase === 'results')) ||
                            (step.key === 'processing' && phase === 'results');
                        return (
                            <div key={step.key} className="flex items-center flex-1">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-10 h-10 rounded-full flex items-center justify-center transition-all"
                                        style={{
                                            backgroundColor: isActive ? '#1e1b4b' : isDone ? '#10b981' : '#e5e7eb',
                                        }}
                                    >
                                        {isDone ? (
                                            <CheckCircle className="h-5 w-5 text-white" />
                                        ) : (
                                            <Icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                                        )}
                                    </div>
                                    <span
                                        className={`text-sm font-medium hidden sm:block ${isActive ? 'text-gray-900' : isDone ? 'text-green-600' : 'text-gray-400'
                                            }`}
                                    >
                                        {step.label}
                                    </span>
                                </div>
                                {idx < 2 && (
                                    <div className="flex-1 mx-4">
                                        <div
                                            className="h-0.5 rounded"
                                            style={{ backgroundColor: isDone ? '#10b981' : '#e5e7eb' }}
                                        />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* ============ UPLOAD PHASE ============ */}
            {phase === 'upload' && (
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left col: Upload form */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Case selector */}
                        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                            <h2 className="text-lg font-bold mb-4" style={{ color: '#1e1b4b' }}>
                                1. Select Missing Person Case
                            </h2>
                            {loadingCases ? (
                                <div className="flex items-center gap-2 text-gray-500">
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                    Loading cases...
                                </div>
                            ) : cases.length === 0 ? (
                                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200 text-yellow-800">
                                    No active missing cases found. Register a case first.
                                </div>
                            ) : (
                                <select
                                    id="case-select"
                                    value={selectedCaseId}
                                    onChange={(e) => setSelectedCaseId(e.target.value)}
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 bg-white"
                                >
                                    <option value="">-- Select a case --</option>
                                    {cases.map((c) => (
                                        <option key={c.id} value={c.id}>
                                            {c.name} — Age: {c.age}, Last seen: {c.last_seen}
                                        </option>
                                    ))}
                                </select>
                            )}

                            {/* Selected case preview */}
                            {selectedCase && (
                                <div className="mt-4 p-4 rounded-lg border border-indigo-200" style={{ backgroundColor: '#f0efff' }}>
                                    <div className="flex items-center gap-4">
                                        <div
                                            className="w-16 h-16 rounded-lg bg-gray-200 flex-shrink-0"
                                            style={{
                                                backgroundImage: selectedCase.photo_url
                                                    ? `url(http://localhost:8000${selectedCase.photo_url})`
                                                    : 'none',
                                                backgroundSize: 'cover',
                                                backgroundPosition: 'center',
                                            }}
                                        />
                                        <div>
                                            <h3 className="font-bold" style={{ color: '#1e1b4b' }}>{selectedCase.name}</h3>
                                            <p className="text-sm text-gray-600">Age: {selectedCase.age} | Last seen: {selectedCase.last_seen}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Video upload */}
                        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                            <h2 className="text-lg font-bold mb-4" style={{ color: '#1e1b4b' }}>
                                2. Upload CCTV Video
                            </h2>

                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${dragOver
                                    ? 'border-indigo-500 bg-indigo-50'
                                    : videoFile
                                        ? 'border-green-400 bg-green-50'
                                        : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
                                    }`}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".mp4,.avi,.mkv,.mov,.wmv"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                    id="video-file-input"
                                />
                                {videoFile ? (
                                    <div className="space-y-2">
                                        <Video className="h-12 w-12 mx-auto text-green-500" />
                                        <p className="font-semibold text-gray-900">{videoFile.name}</p>
                                        <p className="text-sm text-gray-500">{formatFileSize(videoFile.size)}</p>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setVideoFile(null); }}
                                            className="inline-flex items-center gap-1 text-sm text-red-500 hover:text-red-700"
                                        >
                                            <X className="h-4 w-4" /> Remove
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        <Camera className="h-12 w-12 mx-auto text-gray-400" />
                                        <p className="font-medium text-gray-700">Drag & drop video here, or click to browse</p>
                                        <p className="text-sm text-gray-500">Supports: MP4, AVI, MKV, MOV, WMV (Max 2 GB)</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Location & threshold */}
                        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                            <h2 className="text-lg font-bold mb-4" style={{ color: '#1e1b4b' }}>
                                3. Additional Details
                            </h2>
                            <div className="grid sm:grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="video-location" className="block text-sm font-medium text-gray-700 mb-1">
                                        CCTV Camera Location (Optional)
                                    </label>
                                    <input
                                        id="video-location"
                                        type="text"
                                        value={videoLocation}
                                        onChange={(e) => setVideoLocation(e.target.value)}
                                        placeholder="e.g. Rajiv Chowk Station Gate 3"
                                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="confidence-threshold" className="block text-sm font-medium text-gray-700 mb-1">
                                        Distance Threshold: {confidenceThreshold.toFixed(2)} (lower = stricter)
                                    </label>
                                    <input
                                        id="confidence-threshold"
                                        type="range"
                                        min="0.5"
                                        max="1.2"
                                        step="0.05"
                                        value={confidenceThreshold}
                                        onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                                        className="w-full mt-2"
                                    />
                                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                                        <span>Stricter (0.50)</span>
                                        <span>More results (1.20)</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Upload error */}
                        {uploadError && (
                            <div className="p-4 bg-red-50 rounded-xl border border-red-200 flex items-start gap-3">
                                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-red-800">Upload Failed</p>
                                    <p className="text-sm text-red-600">{uploadError}</p>
                                </div>
                            </div>
                        )}

                        {/* Submit button */}
                        <button
                            id="start-analysis-btn"
                            onClick={handleUpload}
                            disabled={!selectedCaseId || !videoFile || uploading}
                            className="w-full py-4 rounded-xl text-white font-bold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                            style={{ backgroundColor: '#1e1b4b' }}
                        >
                            {uploading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                    Uploading...
                                </span>
                            ) : (
                                <span className="flex items-center justify-center gap-2">
                                    <Shield className="h-5 w-5" />
                                    Start AI Analysis
                                </span>
                            )}
                        </button>
                    </div>

                    {/* Right col: Info panel */}
                    <div className="space-y-6">
                        <div className="bg-gradient-to-br from-indigo-950 to-indigo-800 rounded-xl p-6 text-white">
                            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                <Video className="h-5 w-5" />
                                How It Works
                            </h3>
                            <div className="space-y-4 text-sm">
                                {[
                                    'Select a missing person case to search for',
                                    'Upload CCTV footage (up to 15 minutes)',
                                    'AI extracts frames every 2 seconds',
                                    'RetinaFace detects all faces in each frame',
                                    'ArcFace compares against the missing person',
                                    'Matching faces are flagged with timestamps',
                                ].map((step, i) => (
                                    <div key={i} className="flex items-start gap-3">
                                        <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0 text-xs font-bold">
                                            {i + 1}
                                        </span>
                                        <span className="text-indigo-100">{step}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                            <h3 className="text-lg font-bold mb-3" style={{ color: '#1e1b4b' }}>
                                Performance
                            </h3>
                            <div className="space-y-3 text-sm text-gray-600">
                                <div className="flex justify-between">
                                    <span>15-min video</span>
                                    <span className="font-medium text-gray-900">~450 frames</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>GPU processing</span>
                                    <span className="font-medium text-gray-900">~15 min</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>CPU fallback</span>
                                    <span className="font-medium text-gray-900">~45 min</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Workload saved</span>
                                    <span className="font-bold text-green-600">92%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ============ PROCESSING PHASE ============ */}
            {phase === 'processing' && status && (
                <div className="max-w-2xl mx-auto space-y-6">
                    <div className="bg-white rounded-xl p-8 shadow-lg border border-gray-200 text-center">
                        {status.status === 'failed' ? (
                            <>
                                <AlertCircle className="h-16 w-16 mx-auto mb-4 text-red-500" />
                                <h2 className="text-2xl font-bold text-red-600 mb-2">Processing Failed</h2>
                                <p className="text-gray-600 mb-4">{status.error_message || 'An unexpected error occurred'}</p>
                                <button
                                    onClick={resetToUpload}
                                    className="px-6 py-3 rounded-lg text-white font-medium hover:opacity-90"
                                    style={{ backgroundColor: '#1e1b4b' }}
                                >
                                    Try Again
                                </button>
                            </>
                        ) : (
                            <>
                                <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin" style={{ color: '#1e1b4b' }} />
                                <h2 className="text-2xl font-bold mb-2" style={{ color: '#1e1b4b' }}>
                                    {status.status === 'queued' ? 'Preparing Analysis...' : 'Analyzing Video...'}
                                </h2>
                                <p className="text-gray-600 mb-6">
                                    AI is scanning each frame for the selected missing person
                                </p>

                                {/* Progress bar */}
                                <div className="w-full bg-gray-200 rounded-full h-4 mb-4 overflow-hidden">
                                    <div
                                        className="h-4 rounded-full transition-all duration-500 ease-out"
                                        style={{
                                            width: `${Math.max(status.progress_percent, 2)}%`,
                                            background: 'linear-gradient(90deg, #1e1b4b 0%, #4338ca 100%)',
                                        }}
                                    />
                                </div>

                                <div className="grid grid-cols-3 gap-4 text-center">
                                    <div>
                                        <p className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>
                                            {status.progress_percent.toFixed(1)}%
                                        </p>
                                        <p className="text-xs text-gray-500">Progress</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold" style={{ color: '#1e1b4b' }}>
                                            {status.processed_frames}/{status.total_frames || '?'}
                                        </p>
                                        <p className="text-xs text-gray-500">Frames</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold" style={{ color: status.total_detections > 0 ? '#10b981' : '#1e1b4b' }}>
                                            {status.total_detections}
                                        </p>
                                        <p className="text-xs text-gray-500">Detections</p>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Tips while processing */}
                    {status.status !== 'failed' && (
                        <div className="bg-indigo-50 rounded-xl p-6 border border-indigo-200">
                            <h3 className="font-bold text-indigo-900 mb-2">While you wait...</h3>
                            <ul className="text-sm text-indigo-800 space-y-1">
                                <li className="flex items-center gap-2">
                                    <ChevronRight className="h-4 w-4 flex-shrink-0" />
                                    Processing runs in the background — you can navigate away
                                </li>
                                <li className="flex items-center gap-2">
                                    <ChevronRight className="h-4 w-4 flex-shrink-0" />
                                    Each frame is analyzed for faces and compared against the case
                                </li>
                                <li className="flex items-center gap-2">
                                    <ChevronRight className="h-4 w-4 flex-shrink-0" />
                                    Detections above the threshold are saved automatically
                                </li>
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* ============ RESULTS PHASE ============ */}
            {phase === 'results' && (
                <div className="space-y-6">
                    {loadingResults ? (
                        <div className="flex items-center justify-center min-h-[300px]">
                            <Loader2 className="h-10 w-10 animate-spin" style={{ color: '#1e1b4b' }} />
                        </div>
                    ) : results ? (
                        <>
                            {/* Summary card */}
                            <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
                                <div className="grid sm:grid-cols-3 gap-6">
                                    <div className="text-center">
                                        <p className="text-4xl font-bold" style={{ color: '#1e1b4b' }}>
                                            {results.detections.length}
                                        </p>
                                        <p className="text-sm text-gray-600 mt-1">Potential Sightings</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-4xl font-bold" style={{ color: '#10b981' }}>
                                            {results.detections.filter(d => d.confidence >= 30).length}
                                        </p>
                                        <p className="text-sm text-gray-600 mt-1">Higher Confidence (≥30%)</p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-4xl font-bold" style={{ color: '#f59e0b' }}>
                                            {results.total_videos_analyzed}
                                        </p>
                                        <p className="text-sm text-gray-600 mt-1">Videos Analyzed</p>
                                    </div>
                                </div>
                            </div>

                            {/* No detections message */}
                            {results.detections.length === 0 ? (
                                <div className="bg-white rounded-xl p-12 shadow-md border border-gray-200 text-center">
                                    <Search className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                                    <h3 className="text-xl font-bold text-gray-700 mb-2">
                                        No Matches Found
                                    </h3>
                                    <p className="text-gray-500 max-w-md mx-auto">
                                        The AI did not detect the missing person in this video at the given confidence threshold.
                                        Try uploading videos from different camera angles or lowering the threshold.
                                    </p>
                                </div>
                            ) : (
                                /* Detection cards */
                                <div className="space-y-4">
                                    <h2 className="text-xl font-bold" style={{ color: '#1e1b4b' }}>
                                        Detection Timeline
                                        {results.case_name && (
                                            <span className="text-base font-normal text-gray-500 ml-2">
                                                for {results.case_name}
                                            </span>
                                        )}
                                    </h2>

                                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {results.detections.map((det, idx) => (
                                            <div
                                                key={det.id}
                                                className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
                                            >
                                                {/* Cropped face image */}
                                                <div className="relative">
                                                    <img
                                                        src={`http://localhost:8000${det.cropped_face_url}`}
                                                        alt={`Detection ${idx + 1}`}
                                                        className="w-full h-48 object-cover bg-gray-100"
                                                        onError={(e) => {
                                                            (e.target as HTMLImageElement).src = '';
                                                            (e.target as HTMLImageElement).className = 'w-full h-48 bg-gray-200 flex items-center justify-center';
                                                        }}
                                                    />
                                                    {/* Confidence badge */}
                                                    <div
                                                        className="absolute top-3 right-3 px-3 py-1 rounded-full text-sm font-bold text-white"
                                                        style={{
                                                            backgroundColor: det.confidence >= 30 ? '#10b981' : det.confidence >= 15 ? '#f59e0b' : '#ef4444',
                                                        }}
                                                    >
                                                        {det.confidence.toFixed(1)}%
                                                    </div>
                                                    <div className="absolute top-3 left-3 px-2 py-1 rounded-lg bg-black/60 text-white text-xs font-mono">
                                                        #{idx + 1}
                                                    </div>
                                                </div>

                                                <div className="p-4 space-y-2">
                                                    <div className="flex items-center gap-2 text-sm">
                                                        <Clock className="h-4 w-4 text-gray-400" />
                                                        <span className="font-mono font-bold" style={{ color: '#1e1b4b' }}>
                                                            {det.timestamp_display}
                                                        </span>
                                                        <span className="text-gray-400">
                                                            ({det.timestamp_seconds.toFixed(1)}s)
                                                        </span>
                                                    </div>

                                                    {det.video_location && (
                                                        <div className="flex items-center gap-2 text-sm text-gray-600">
                                                            <MapPin className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                                            <span className="truncate">{det.video_location}</span>
                                                        </div>
                                                    )}

                                                    {det.detected_at && (
                                                        <div className="text-xs text-gray-400">
                                                            Detected: {new Date(det.detected_at).toLocaleString()}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="bg-red-50 rounded-xl p-6 border border-red-200 text-center">
                            <p className="text-red-600">Failed to load results. Please try again.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
