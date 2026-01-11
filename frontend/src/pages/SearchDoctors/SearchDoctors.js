import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { doctorAPI } from '../../api';
import SearchBar from '../../components/SearchBar';
import {
  FiSearch, FiFilter, FiMapPin, FiStar, FiClock, FiShield,
  FiHeart, FiChevronDown, FiX, FiGrid, FiList, FiSliders
} from 'react-icons/fi';
import './SearchDoctors.css';

const SearchDoctors = () => {
  const [searchParams] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    specialty: searchParams.get('specialty') || '',
    location: searchParams.get('location') || '',
    rating: '',
    fee: '',
    experience: '',
    availability: ''
  });

  // Sort
  const [sortBy, setSortBy] = useState('relevance');

  // Mock doctors data
  const mockDoctors = [
    {
      id: 1, first_name: 'Priya', last_name: 'Sharma', specialty: 'Cardiology',
      consultation_fee: 500, clinic_address: 'Apollo Hospital, Delhi',
      is_verified: true, rating: 4.8, reviews: 245, experience: 15,
      available_today: true
    },
    {
      id: 2, first_name: 'Rajesh', last_name: 'Patel', specialty: 'Dermatology',
      consultation_fee: 400, clinic_address: 'Max Healthcare, Mumbai',
      is_verified: true, rating: 4.6, reviews: 189, experience: 12,
      available_today: true
    },
    {
      id: 3, first_name: 'Anita', last_name: 'Gupta', specialty: 'Pediatrics',
      consultation_fee: 350, clinic_address: 'Fortis Hospital, Bangalore',
      is_verified: true, rating: 4.9, reviews: 312, experience: 18,
      available_today: false
    },
    {
      id: 4, first_name: 'Vikram', last_name: 'Singh', specialty: 'Orthopedics',
      consultation_fee: 600, clinic_address: 'AIIMS, Delhi',
      is_verified: true, rating: 4.7, reviews: 278, experience: 20,
      available_today: true
    },
    {
      id: 5, first_name: 'Meera', last_name: 'Reddy', specialty: 'Gynecology',
      consultation_fee: 450, clinic_address: 'Rainbow Hospital, Hyderabad',
      is_verified: true, rating: 4.5, reviews: 156, experience: 10,
      available_today: true
    },
    {
      id: 6, first_name: 'Sanjay', last_name: 'Kumar', specialty: 'Neurology',
      consultation_fee: 700, clinic_address: 'Medanta, Gurugram',
      is_verified: true, rating: 4.8, reviews: 198, experience: 22,
      available_today: false
    },
    {
      id: 7, first_name: 'Kavita', last_name: 'Joshi', specialty: 'General Physician',
      consultation_fee: 300, clinic_address: 'City Clinic, Pune',
      is_verified: false, rating: 4.3, reviews: 87, experience: 8,
      available_today: true
    },
    {
      id: 8, first_name: 'Arjun', last_name: 'Nair', specialty: 'Psychiatry',
      consultation_fee: 550, clinic_address: 'NIMHANS, Bangalore',
      is_verified: true, rating: 4.6, reviews: 134, experience: 14,
      available_today: true
    }
  ];

  const specialties = [
    'All Specialties', 'Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics',
    'Gynecology', 'Neurology', 'General Physician', 'Psychiatry', 'ENT',
    'Ophthalmology', 'Dentist'
  ];

  const feeRanges = [
    { label: 'Any', value: '' },
    { label: 'Under ₹300', value: '0-300' },
    { label: '₹300 - ₹500', value: '300-500' },
    { label: '₹500 - ₹700', value: '500-700' },
    { label: 'Above ₹700', value: '700+' }
  ];

  const experienceRanges = [
    { label: 'Any', value: '' },
    { label: '0-5 years', value: '0-5' },
    { label: '5-10 years', value: '5-10' },
    { label: '10-20 years', value: '10-20' },
    { label: '20+ years', value: '20+' }
  ];

  useEffect(() => {
    const fetchDoctors = async () => {
      setLoading(true);
      try {
        const response = await doctorAPI.getVerifiedDoctors();
        setDoctors(response.data || []);
      } catch (error) {
        console.error('Error fetching doctors:', error);
        setDoctors([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDoctors();
  }, []);

  // Filter doctors
  const filteredDoctors = doctors.filter(doc => {
    if (filters.specialty && filters.specialty !== 'All Specialties' && doc.specialty !== filters.specialty) return false;
    if (filters.availability === 'today' && !doc.available_today) return false;
    
    if (filters.fee) {
      const fee = doc.consultation_fee;
      if (filters.fee === '0-300' && fee > 300) return false;
      if (filters.fee === '300-500' && (fee < 300 || fee > 500)) return false;
      if (filters.fee === '500-700' && (fee < 500 || fee > 700)) return false;
      if (filters.fee === '700+' && fee < 700) return false;
    }

    if (filters.experience) {
      const exp = doc.experience || 0;
      if (filters.experience === '0-5' && exp > 5) return false;
      if (filters.experience === '5-10' && (exp < 5 || exp > 10)) return false;
      if (filters.experience === '10-20' && (exp < 10 || exp > 20)) return false;
      if (filters.experience === '20+' && exp < 20) return false;
    }

    if (filters.rating && doc.rating < parseFloat(filters.rating)) return false;

    return true;
  });

  // Sort doctors
  const sortedDoctors = [...filteredDoctors].sort((a, b) => {
    switch (sortBy) {
      case 'rating': return (b.rating || 0) - (a.rating || 0);
      case 'fee-low': return (a.consultation_fee || 0) - (b.consultation_fee || 0);
      case 'fee-high': return (b.consultation_fee || 0) - (a.consultation_fee || 0);
      case 'experience': return (b.experience || 0) - (a.experience || 0);
      default: return 0;
    }
  });

  const clearFilters = () => {
    setFilters({
      specialty: '',
      location: '',
      rating: '',
      fee: '',
      experience: '',
      availability: ''
    });
  };

  const activeFilterCount = Object.values(filters).filter(v => v && v !== 'All Specialties').length;

  return (
    <div className="search-doctors-page">
      {/* Search Header */}
      <div className="search-header">
        <div className="search-header-content">
          <h1>Find Doctors</h1>
          <p>Book appointments with the best doctors near you</p>
          <SearchBar />
        </div>
      </div>

      {/* Main Content */}
      <div className="search-content">
        {/* Filters Sidebar */}
        <aside className={`filters-sidebar ${showFilters ? 'show' : ''}`}>
          <div className="filters-header">
            <h3><FiFilter /> Filters</h3>
            {activeFilterCount > 0 && (
              <button className="clear-btn" onClick={clearFilters}>
                Clear All
              </button>
            )}
            <button className="close-filters" onClick={() => setShowFilters(false)}>
              <FiX />
            </button>
          </div>

          {/* Specialty Filter */}
          <div className="filter-group">
            <h4>Specialty</h4>
            <div className="filter-options">
              {specialties.map(spec => (
                <label key={spec} className="filter-option">
                  <input
                    type="radio"
                    name="specialty"
                    checked={filters.specialty === spec}
                    onChange={() => setFilters({...filters, specialty: spec})}
                  />
                  <span className="checkmark"></span>
                  <span>{spec}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Fee Range Filter */}
          <div className="filter-group">
            <h4>Consultation Fee</h4>
            <div className="filter-options">
              {feeRanges.map(range => (
                <label key={range.value} className="filter-option">
                  <input
                    type="radio"
                    name="fee"
                    checked={filters.fee === range.value}
                    onChange={() => setFilters({...filters, fee: range.value})}
                  />
                  <span className="checkmark"></span>
                  <span>{range.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Experience Filter */}
          <div className="filter-group">
            <h4>Experience</h4>
            <div className="filter-options">
              {experienceRanges.map(range => (
                <label key={range.value} className="filter-option">
                  <input
                    type="radio"
                    name="experience"
                    checked={filters.experience === range.value}
                    onChange={() => setFilters({...filters, experience: range.value})}
                  />
                  <span className="checkmark"></span>
                  <span>{range.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Rating Filter */}
          <div className="filter-group">
            <h4>Rating</h4>
            <div className="rating-options">
              {[4.5, 4, 3.5, 3].map(rating => (
                <button
                  key={rating}
                  className={`rating-btn ${filters.rating === rating.toString() ? 'active' : ''}`}
                  onClick={() => setFilters({...filters, rating: filters.rating === rating.toString() ? '' : rating.toString()})}
                >
                  <FiStar className="star" /> {rating}+
                </button>
              ))}
            </div>
          </div>

          {/* Availability Filter */}
          <div className="filter-group">
            <h4>Availability</h4>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.availability === 'today'}
                onChange={(e) => setFilters({...filters, availability: e.target.checked ? 'today' : ''})}
              />
              <span className="checkbox-mark"></span>
              <span>Available Today</span>
            </label>
          </div>
        </aside>

        {/* Results Section */}
        <div className="results-section">
          {/* Results Header */}
          <div className="results-header">
            <div className="results-info">
              <button className="filter-toggle" onClick={() => setShowFilters(true)}>
                <FiSliders />
                Filters
                {activeFilterCount > 0 && <span className="filter-badge">{activeFilterCount}</span>}
              </button>
              <span className="results-count">
                {sortedDoctors.length} doctors found
              </span>
            </div>

            <div className="results-actions">
              <div className="sort-dropdown">
                <label>Sort by:</label>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                  <option value="relevance">Relevance</option>
                  <option value="rating">Rating</option>
                  <option value="fee-low">Fee: Low to High</option>
                  <option value="fee-high">Fee: High to Low</option>
                  <option value="experience">Experience</option>
                </select>
              </div>

              <div className="view-toggle">
                <button 
                  className={viewMode === 'grid' ? 'active' : ''} 
                  onClick={() => setViewMode('grid')}
                >
                  <FiGrid />
                </button>
                <button 
                  className={viewMode === 'list' ? 'active' : ''} 
                  onClick={() => setViewMode('list')}
                >
                  <FiList />
                </button>
              </div>
            </div>
          </div>

          {/* Active Filters */}
          {activeFilterCount > 0 && (
            <div className="active-filters">
              {filters.specialty && filters.specialty !== 'All Specialties' && (
                <span className="filter-tag">
                  {filters.specialty}
                  <FiX onClick={() => setFilters({...filters, specialty: ''})} />
                </span>
              )}
              {filters.fee && (
                <span className="filter-tag">
                  Fee: {feeRanges.find(r => r.value === filters.fee)?.label}
                  <FiX onClick={() => setFilters({...filters, fee: ''})} />
                </span>
              )}
              {filters.experience && (
                <span className="filter-tag">
                  Exp: {experienceRanges.find(r => r.value === filters.experience)?.label}
                  <FiX onClick={() => setFilters({...filters, experience: ''})} />
                </span>
              )}
              {filters.rating && (
                <span className="filter-tag">
                  Rating: {filters.rating}+
                  <FiX onClick={() => setFilters({...filters, rating: ''})} />
                </span>
              )}
              {filters.availability && (
                <span className="filter-tag">
                  Available Today
                  <FiX onClick={() => setFilters({...filters, availability: ''})} />
                </span>
              )}
            </div>
          )}

          {/* Doctor Cards */}
          {loading ? (
            <div className={`doctors-grid ${viewMode}`}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="doctor-card-skeleton">
                  <div className="skeleton-avatar"></div>
                  <div className="skeleton-content">
                    <div className="skeleton-line"></div>
                    <div className="skeleton-line short"></div>
                    <div className="skeleton-line"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : sortedDoctors.length === 0 ? (
            <div className="no-results">
              <FiSearch className="no-results-icon" />
              <h3>No doctors found</h3>
              <p>Try adjusting your filters or search criteria</p>
              <button className="btn-primary" onClick={clearFilters}>Clear Filters</button>
            </div>
          ) : (
            <div className={`doctors-grid ${viewMode}`}>
              {sortedDoctors.map((doctor) => (
                <Link 
                  key={doctor.id} 
                  to={`/doctor/${doctor.id}`}
                  className={`doctor-card ${viewMode}`}
                >
                  <div className="card-left">
                    <div className="doctor-avatar">
                      {doctor.first_name?.charAt(0)}{doctor.last_name?.charAt(0)}
                    </div>
                    {doctor.is_verified && (
                      <span className="verified-badge"><FiShield /></span>
                    )}
                  </div>

                  <div className="card-middle">
                    <h3>Dr. {doctor.first_name} {doctor.last_name}</h3>
                    <p className="specialty">{doctor.specialty || 'General Physician'}</p>
                    <p className="experience">{doctor.experience || 10}+ years experience</p>
                    
                    <div className="card-meta">
                      <span className="rating">
                        <FiStar className="star-icon" /> {doctor.rating || '4.5'}
                        <span className="reviews">({doctor.reviews || '100'})</span>
                      </span>
                      <span className="location">
                        <FiMapPin /> {doctor.clinic_address?.split(',')[0] || 'Location'}
                      </span>
                    </div>

                    {doctor.available_today && (
                      <span className="available-tag">
                        <FiClock /> Available Today
                      </span>
                    )}
                  </div>

                  <div className="card-right">
                    <button className="favorite-btn">
                      <FiHeart />
                    </button>
                    <div className="fee-info">
                      <span className="fee-amount">₹{doctor.consultation_fee || '500'}</span>
                      <span className="fee-label">Consultation</span>
                    </div>
                    <button className="book-btn">Book Now</button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Mobile Filter Overlay */}
      {showFilters && <div className="filter-overlay" onClick={() => setShowFilters(false)} />}
    </div>
  );
};

export default SearchDoctors;
