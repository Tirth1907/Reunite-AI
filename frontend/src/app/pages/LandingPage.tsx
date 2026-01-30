import { Link } from 'react-router-dom';
import { Heart, Users, Search, Bell, CheckCircle, MapPin, Clock, ArrowRight } from 'lucide-react';
import { mockMissingPersons, statistics } from '@/data/mockData';

export default function LandingPage() {
  const recentStories = mockMissingPersons.slice(0, 3);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Heart className="h-8 w-8" style={{ color: '#1e1b4b' }} />
              <span className="text-xl font-bold" style={{ color: '#1e1b4b' }}>Reunite AI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/login"
                className="px-4 py-2 rounded-lg transition-colors hover:bg-gray-100"
                style={{ color: '#1e1b4b' }}
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="px-6 py-2 rounded-lg text-white transition-all hover:shadow-lg"
                style={{ backgroundColor: '#1e1b4b' }}
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6" style={{ color: '#1e1b4b' }}>
                Finding Hope, Reuniting Families
              </h1>
              <p className="text-lg md:text-xl text-gray-700 mb-8 leading-relaxed">
                Reunite AI uses advanced technology and community power to help find missing persons across India.
                Every second counts. Every face matters. Together, we can bring loved ones home.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/signup"
                  className="px-8 py-4 rounded-lg text-white transition-all hover:shadow-xl flex items-center gap-2"
                  style={{ backgroundColor: '#1e1b4b' }}
                >
                  Register a Missing Person
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/dashboard"
                  className="px-8 py-4 rounded-lg transition-all hover:shadow-lg flex items-center gap-2 bg-white"
                  style={{ color: '#1e1b4b', border: '2px solid #1e1b4b' }}
                >
                  Browse Cases
                </Link>
              </div>
            </div>
            <div className="relative">
              <div className="rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1617080090911-91409e3496ad?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxoZWxwaW5nJTIwaGFuZHMlMjBjb21tdW5pdHl8ZW58MXx8fHwxNzY5MzE4ODY4fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                  alt="Community helping"
                  className="w-full h-96 object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Statistics Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8" style={{ backgroundColor: '#1e1b4b' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              The Reality of Missing Persons in India
            </h2>
            <p className="text-xl text-gray-200 max-w-3xl mx-auto">
              Behind every number is a family waiting, hoping, and searching
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-lg text-center transition-transform hover:scale-105">
              <div className="text-4xl font-bold mb-2" style={{ color: '#ef4444' }}>
                {statistics.yearlyMissing.toLocaleString()}+
              </div>
              <div className="text-gray-600">People go missing annually in India</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg text-center transition-transform hover:scale-105">
              <div className="text-4xl font-bold mb-2" style={{ color: '#f59e0b' }}>
                {statistics.unresolvedPercentage}%
              </div>
              <div className="text-gray-600">Cases remain unresolved</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg text-center transition-transform hover:scale-105">
              <div className="text-4xl font-bold mb-2" style={{ color: '#ef4444' }}>
                {statistics.childrenAffected}%
              </div>
              <div className="text-gray-600">Are children under 18</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg text-center transition-transform hover:scale-105">
              <div className="text-4xl font-bold mb-2" style={{ color: '#f59e0b' }}>
                {statistics.elderlyAffected}%
              </div>
              <div className="text-gray-600">Are elderly with medical conditions</div>
            </div>
          </div>
        </div>
      </section>

      {/* Real Stories Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ color: '#1e1b4b' }}>
              Real Stories, Real Impact
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Every case matters. These are just a few of the families we're helping
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {recentStories.map((story) => (
              <div key={story.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
                <div className="h-64 overflow-hidden">
                  <img src={story.photo} alt={story.name} className="w-full h-full object-cover" />
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold" style={{ color: '#1e1b4b' }}>{story.name}</h3>
                    {story.status === 'found' ? (
                      <span className="px-3 py-1 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#10b981' }}>
                        Found
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-full text-sm font-medium text-white" style={{ backgroundColor: '#ef4444' }}>
                        Missing
                      </span>
                    )}
                  </div>
                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      <span>{story.age} years, {story.gender}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      <span>{story.city}, {story.state}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      <span>Last seen: {new Date(story.lastSeenDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <p className="text-gray-700 line-clamp-2">
                    {story.additionalNotes}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ color: '#1e1b4b' }}>
              How Reunite AI Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Technology meets compassion in our four-step reunification process
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#1e1b4b' }}>
                <Search className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-3" style={{ color: '#1e1b4b' }}>1. Register Case</h3>
              <p className="text-gray-600">
                Family members or NGOs register a missing person with photos and details in our centralized database
              </p>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#f59e0b' }}>
                <Bell className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-3" style={{ color: '#1e1b4b' }}>2. AI Matching</h3>
              <p className="text-gray-600">
                Advanced facial recognition scans sightings and matches them against registered cases automatically
              </p>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#1e1b4b' }}>
                <Users className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-3" style={{ color: '#1e1b4b' }}>3. Community Sightings</h3>
              <p className="text-gray-600">
                Anyone can submit sighting photos via mobile app, creating a nationwide network of eyes
              </p>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#10b981' }}>
                <CheckCircle className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-3" style={{ color: '#1e1b4b' }}>4. Reunification</h3>
              <p className="text-gray-600">
                Families are notified of matches, police verify, and loved ones are reunited safely
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8" style={{ backgroundColor: '#f59e0b' }}>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Every Second Counts. Take Action Today.
          </h2>
          <p className="text-xl text-white mb-8 leading-relaxed">
            Whether you're searching for a loved one or want to help reunite families,
            your action can make a difference. Join thousands who are bringing hope to India.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/signup"
              className="px-8 py-4 rounded-lg font-medium transition-all hover:shadow-xl"
              style={{ backgroundColor: '#1e1b4b', color: 'white' }}
            >
              Register a Missing Person
            </Link>
            <Link
              to="/signup"
              className="px-8 py-4 bg-white rounded-lg font-medium transition-all hover:shadow-xl"
              style={{ color: '#1e1b4b' }}
            >
              Join as Volunteer
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white py-8 px-4 sm:px-6 lg:px-8 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center text-gray-600">
          <p>© 2026 Reunite AI. A civic-tech initiative for missing persons in India.</p>
        </div>
      </footer>
    </div>
  );
}
