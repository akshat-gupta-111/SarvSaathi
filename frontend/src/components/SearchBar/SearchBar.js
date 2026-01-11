import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiMapPin, FiFilter } from 'react-icons/fi';
import './SearchBar.css';

const SearchBar = ({ onSearch, showFilters = true, placeholder = "Search doctors, hospitals, specialties..." }) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [filters, setFilters] = useState({
    specialty: '',
    availability: '',
    rating: '',
    consultationType: '',
  });

  const specialties = [
    'All Specialties',
    'Cardiology',
    'Dermatology',
    'General Physician',
    'Gynecology',
    'Neurology',
    'Orthopedics',
    'Pediatrics',
    'Psychiatry',
    'Pulmonology',
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    if (onSearch) {
      onSearch({ query: searchQuery, location, ...filters });
    } else {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}&location=${encodeURIComponent(location)}`);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(`${position.coords.latitude}, ${position.coords.longitude}`);
        },
        (error) => {
          console.error('Error getting location:', error);
          setLocation('Location unavailable');
        }
      );
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-inputs">
          {/* Main Search Input */}
          <div className="search-input-wrapper main">
            <FiSearch className="search-icon" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={placeholder}
              className="search-input"
            />
          </div>

          {/* Location Input */}
          <div className="search-input-wrapper location">
            <FiMapPin className="search-icon" />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Location"
              className="search-input"
            />
            <button 
              type="button" 
              className="location-btn"
              onClick={handleCurrentLocation}
              title="Use current location"
            >
              <FiMapPin />
            </button>
          </div>

          {/* Filter Toggle */}
          {showFilters && (
            <button 
              type="button"
              className={`filter-toggle ${showFilterPanel ? 'active' : ''}`}
              onClick={() => setShowFilterPanel(!showFilterPanel)}
            >
              <FiFilter />
              <span>Filters</span>
            </button>
          )}

          {/* Search Button */}
          <button type="submit" className="search-btn">
            <FiSearch />
            <span>Search</span>
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && showFilterPanel && (
          <div className="filter-panel">
            <div className="filter-group">
              <label>Specialty</label>
              <select 
                value={filters.specialty}
                onChange={(e) => handleFilterChange('specialty', e.target.value)}
              >
                {specialties.map(spec => (
                  <option key={spec} value={spec === 'All Specialties' ? '' : spec}>
                    {spec}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Availability</label>
              <select 
                value={filters.availability}
                onChange={(e) => handleFilterChange('availability', e.target.value)}
              >
                <option value="">Any Time</option>
                <option value="today">Available Today</option>
                <option value="tomorrow">Available Tomorrow</option>
                <option value="week">This Week</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Consultation Type</label>
              <select 
                value={filters.consultationType}
                onChange={(e) => handleFilterChange('consultationType', e.target.value)}
              >
                <option value="">All Types</option>
                <option value="online">Online</option>
                <option value="in-clinic">In-Clinic</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Rating</label>
              <select 
                value={filters.rating}
                onChange={(e) => handleFilterChange('rating', e.target.value)}
              >
                <option value="">Any Rating</option>
                <option value="4">4+ Stars</option>
                <option value="3">3+ Stars</option>
              </select>
            </div>
          </div>
        )}
      </form>

      {/* Quick Search Tags */}
      <div className="quick-search-tags">
        <span className="tags-label">Popular:</span>
        {['Cardiologist', 'Dermatologist', 'General Physician', 'Pediatrician'].map(tag => (
          <button 
            key={tag}
            type="button"
            className="quick-tag"
            onClick={() => {
              setSearchQuery(tag);
              if (onSearch) {
                onSearch({ query: tag, location, ...filters });
              }
            }}
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SearchBar;
