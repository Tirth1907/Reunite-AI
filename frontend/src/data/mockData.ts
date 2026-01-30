export interface MissingPerson {
  id: string;
  name: string;
  age: number;
  gender: string;
  fatherName: string;
  photo: string;
  lastSeenDate: string;
  lastSeenLocation: string;
  city: string;
  state: string;
  clothingWorn: string;
  identificationMarks: string;
  medicalConditions: string;
  languagesSpoken: string[];
  additionalNotes: string;
  reporterName: string;
  reporterRelation: string;
  reporterPhone: string;
  reporterAlternatePhone: string;
  reporterAddress: string;
  firDetails: string;
  status: 'found' | 'not-found';
  registeredDate: string;
}

export interface AIMatch {
  id: string;
  caseId: string;
  sightingId: string;
  confidence: number;
  matchedPerson: MissingPerson;
  sightingPhoto: string;
  sightingLocation: string;
  sightingDate: string;
  status: 'pending' | 'verified' | 'rejected';
}

export interface Sighting {
  id: string;
  photo: string;
  location: string;
  description: string;
  submittedDate: string;
  status: 'under-review' | 'matched' | 'closed';
  referenceId: string;
}

// Empty data - ready for backend integration
export const mockMissingPersons: MissingPerson[] = [];

// Empty AI matches - ready for backend integration
export const mockAIMatches: AIMatch[] = [];

// Empty sightings - ready for backend integration
export const mockSightings: Sighting[] = [];

// Statistics - will be fetched from backend
export const statistics = {
  totalRegistered: 0,
  foundCases: 0,
  activeCases: 0,
  aiMatches: 0,
  yearlyMissing: 0,
  unresolvedPercentage: 0,
  childrenAffected: 0,
  elderlyAffected: 0
};
