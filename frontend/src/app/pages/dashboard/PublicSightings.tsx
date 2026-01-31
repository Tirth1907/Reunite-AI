import { useEffect, useState } from 'react';
import { Trash2, AlertCircle, MapPin, Calendar, Smartphone, Eye } from 'lucide-react';
import { getPublicSubmissions, deletePublicSubmission, type PublicSubmission } from '@/app/services/api';

const API_BASE = 'http://localhost:8000';

export default function PublicSightings() {
    const [sightings, setSightings] = useState<PublicSubmission[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchSightings();
    }, []);

    const fetchSightings = async () => {
        try {
            setLoading(true);
            // We need to update the API service to support 'status' param if not already present
            // Use the updated API service
            const data = await getPublicSubmissions('All');
            setSightings(data);
        } catch (err) {
            setError('Failed to load sightings');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this sighting? This cannot be undone.')) return;

        try {
            await deletePublicSubmission(id);
            setSightings(prev => prev.filter(s => s.id !== id));
        } catch (err) {
            alert('Failed to delete sighting');
            console.error(err);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading sightings...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold mb-2" style={{ color: '#1e1b4b' }}>Public Sightings</h1>
                    <p className="text-gray-600">Manage all sightings submitted by the community</p>
                </div>
                <div className="text-sm font-medium px-4 py-2 bg-gray-100 rounded-full text-gray-700">
                    Total: {sightings.length}
                </div>
            </div>

            {sightings.length === 0 ? (
                <div className="bg-white rounded-xl shadow p-12 text-center">
                    <AlertCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-900 mb-2">No sightings found</h3>
                    <p className="text-gray-600">The database is currently empty.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {sightings.map((sighting) => (
                        <div key={sighting.id} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-all border border-gray-100">
                            <div className="relative aspect-square bg-gray-100">
                                <img
                                    src={`${API_BASE}${sighting.photo_url || `/resources/${sighting.id}.jpg`}`}
                                    alt="Sighting"
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                        (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400?text=No+Image';
                                    }}
                                />
                                <div className="absolute top-2 right-2">
                                    <span className={`px-2 py-1 rounded text-xs font-bold text-white ${sighting.status === 'F' ? 'bg-green-500' : 'bg-red-500'
                                        }`}>
                                        {sighting.status === 'F' ? 'FOUND' : 'MISSING'}
                                    </span>
                                </div>
                            </div>

                            <div className="p-4 space-y-3">
                                <div className="flex items-start gap-2 text-sm text-gray-600">
                                    <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <span className="line-clamp-2">{sighting.location}</span>
                                </div>

                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <Smartphone className="h-4 w-4 flex-shrink-0" />
                                    <span>{sighting.mobile}</span>
                                </div>

                                <div className="flex items-center gap-2 text-sm text-gray-400">
                                    <Calendar className="h-4 w-4 flex-shrink-0" />
                                    <span>{sighting.submitted_on ? new Date(sighting.submitted_on).toLocaleDateString() : 'Unknown'}</span>
                                </div>

                                <div className="pt-2">
                                    <button
                                        onClick={() => handleDelete(sighting.id)}
                                        className="w-full py-2 px-4 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors flex items-center justify-center gap-2 font-medium"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        Delete Sighting
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
