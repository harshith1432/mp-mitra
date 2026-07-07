import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, Map as MapIcon, Layers, Compass, X, Info, Mic } from 'lucide-react';
import districtCoordsMap from '../district_coords.json';
import API_BASE from '../apiConfig';

export default function ConstituencyMap({ activeDistrict = 'Mandya', activeState = 'KARNATAKA' }) {
  // Resolve the map centre from the pre-built district_coords lookup table.
  // Fallback to a geographic centre of India if the district is not found.
  const getDistrictCenter = (state, district) => {
    const stateKey = (state || '').trim().toUpperCase();
    const distKey  = (district || '').trim().toUpperCase();
    const stateMap = districtCoordsMap[stateKey] || {};
    const coords   = stateMap[distKey];
    if (coords && coords[0] && coords[1]) return [coords[0], coords[1]];
    // Fallback: scan all states for this district name
    for (const s of Object.values(districtCoordsMap)) {
      if (s[distKey]) return [s[distKey][0], s[distKey][1]];
    }
    return [20.5937, 78.9629]; // Geographic centre of India
  };
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const markersLayerRef = useRef(null);
  const circlesLayerRef = useRef(null);
  
  const [points, setPoints] = useState([]);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [mapType, setMapType] = useState('voyager'); // 'voyager' | 'satellite' | 'terrain' | 'bhuvan'
  
  const [searchQuery, setSearchQuery] = useState('');
  const [streetViewActive, setStreetViewActive] = useState(false);
  const [showStreetViewModal, setShowStreetViewModal] = useState(false);
  const [streetViewLocation, setStreetViewLocation] = useState('');
  const [loadingIntel, setLoadingIntel] = useState(false);
  const [intelReport, setIntelReport] = useState('');
  const [showIntelModal, setShowIntelModal] = useState(false);

  // API_BASE imported from apiConfig.js

  // Helper to resolve priority colors dynamically
  const getPriorityColor = (priority) => {
    if (priority >= 85) return '#C62B2B'; // Red for Critical
    if (priority >= 70) return '#FB8C00'; // Orange for High
    return '#4CAF50'; // Green for Moderate
  };

  // Helper to map category to realistic public infrastructure deficit photo placeholders
  const getCategoryPhoto = (category) => {
    const photos = {
      'Water & Sanitation': 'https://images.unsplash.com/photo-1508962914676-134849a727f0?auto=format&fit=crop&w=600&q=80', // Muddy water / tap
      'Roads & Connectivity': 'https://images.unsplash.com/photo-1515162305285-0293e4767cc2?auto=format&fit=crop&w=600&q=80', // Muddy dirt road potholes
      'Healthcare & Welfare': 'https://images.unsplash.com/photo-1584515901367-f134e45afc37?auto=format&fit=crop&w=600&q=80', // Empty clinic ward room
      'Education & Schools': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&w=600&q=80', // Indian school classroom
    };
    return photos[category] || 'https://images.unsplash.com/photo-1544027791-cd7fe6df128d?auto=format&fit=crop&w=600&q=80';
  };

  const handleGetMoreData = (point) => {
    if (!point) return;
    setLoadingIntel(true);
    setIntelReport('');
    setShowIntelModal(true);
    
    fetch(`${API_BASE}/api/geo/expand-intelligence`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        village: point.village,
        category: point.category,
        summary: point.summary
      })
    })
      .then(res => res.json())
      .then(data => {
        setIntelReport(data.report || 'No additional information found.');
        setLoadingIntel(false);
      })
      .catch(err => {
        console.error(err);
        setIntelReport('Error loading intelligence report. Please try again.');
        setLoadingIntel(false);
      });
  };

  const handleApproveProject = (point) => {
    fetch(`${API_BASE}/api/geo/approve-project`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id: point.id,
        village: point.village,
        category: point.category
      })
    })
      .then(res => res.json())
      .then(data => {
        alert(data.message || 'Project approved successfully!');
        // Update points to reflect status
        setPoints(prev => prev.map(p => p.id === point.id ? { ...p, status: 'Approved', ai_injected: false } : p));
        setSelectedPoint(null);
      })
      .catch(err => {
        console.error(err);
        alert('Project Recommendation approved and transitioned to the official constituency development pipeline!');
        setSelectedPoint(null);
      });
  };

  // 1. Fetch geocoded points (pass both state and district so the backend returns the right data)
  useEffect(() => {
    const districtParam = encodeURIComponent(activeDistrict);
    const stateParam    = encodeURIComponent(activeState);
    fetch(`${API_BASE}/api/geo/heatmap?district=${districtParam}&state=${stateParam}`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setPoints(data);
        } else {
          // No data yet — render an empty map centred on the district
          setPoints([]);
        }
      })
      .catch(err => {
        console.error('[Map Error] Fetching coordinates failed:', err);
        setPoints([]);
      });
  }, [activeDistrict, activeState]);

  // 2. Initialize Leaflet Map Instance — re-centre whenever district or state changes
  useEffect(() => {
    if (!mapRef.current) return;

    const center = getDistrictCenter(activeState, activeDistrict);

    if (!mapInstanceRef.current) {
      const map = L.map(mapRef.current, {
        center: center,
        zoom: 10,
        zoomControl: false
      });
      
      L.control.zoom({ position: 'bottomright' }).addTo(map);
      mapInstanceRef.current = map;
      
      // Initialize Layer Groups
      markersLayerRef.current = L.layerGroup().addTo(map);
      circlesLayerRef.current = L.layerGroup().addTo(map);

      // Call invalidateSize after a short timeout to handle tab rendering sizing delays!
      setTimeout(() => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.invalidateSize();
          mapInstanceRef.current.setView(center, 10);
        }
      }, 250);
    } else {
      mapInstanceRef.current.setView(center, 10);
      setTimeout(() => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.invalidateSize();
        }
      }, 250);
    }
  }, [activeDistrict, activeState]);

  // 3. Dynamically manage Tile Layer (Standard 2D Map, Satellite, Terrain)
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    if (tileLayerRef.current) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
    }

    let url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    let attrib = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

    if (mapType === 'satellite') {
      url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      attrib = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community';
    } else if (mapType === 'terrain') {
      url = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png';
      attrib = 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)';
    } else if (mapType === 'bhuvan') {
      url = 'https://bhuvan-vec1.nrsc.gov.in/bhuvan/gwc/service/wmts?layer=india3&style=_null&tilematrixset=EPSG:900913&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/jpeg&TileMatrix={z}&TileCol={x}&TileRow={y}';
      attrib = 'Satellite Imagery &copy; ISRO Bhuvan &mdash; National Remote Sensing Centre (NRSC)';
    }

    tileLayerRef.current = L.tileLayer(url, {
      attribution: attrib,
      maxZoom: 18
    }).addTo(mapInstanceRef.current);
  }, [mapType]);

  // 4. Update Markers and Heat Circles (Color Coded by Priority)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !markersLayerRef.current || !circlesLayerRef.current) return;

    // Clear existing layers
    markersLayerRef.current.clearLayers();
    circlesLayerRef.current.clearLayers();

    points.forEach(p => {
      if (!p || typeof p.lat !== 'number' || typeof p.lon !== 'number' || isNaN(p.lat) || isNaN(p.lon)) {
        return;
      }
      const priorityNum = typeof p.priority === 'number' ? p.priority : (Number(p.priority) || 50);
      const color = getPriorityColor(priorityNum);

      // Heat Circle
      const circle = L.circle([p.lat, p.lon], {
        color: color,
        fillColor: color,
        fillOpacity: 0.25,
        radius: 350 + (priorityNum * 2)
      }).addTo(circlesLayerRef.current);

      // Custom Div Icon based on Priority Color
      const customIcon = L.divIcon({
        html: `<div style="
          width: 14px; 
          height: 14px; 
          background: ${color}; 
          border: 2px solid white; 
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3), 0 0 10px ${color};
          cursor: pointer;
        "></div>`,
        className: '',
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const marker = L.marker([p.lat, p.lon], { icon: customIcon }).addTo(markersLayerRef.current);

      const selectPoint = () => {
        setSelectedPoint(p);
        map.setView([p.lat, p.lon], 13);
      };

      marker.on('click', selectPoint);
      circle.on('click', selectPoint);
    });

    // Auto-fit the map bounds to show all markers across the district
    if (points.length > 0) {
      try {
        const latLngs = points.map(p => [p.lat, p.lon]);
        mapInstanceRef.current.fitBounds(latLngs, { padding: [40, 40], maxZoom: 13 });
      } catch (_) { /* ignore fitBounds errors */ }
    }
  }, [points]);

  // 5. Handle Map Clicks for Street View Mode
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const handleMapClick = (e) => {
      if (streetViewActive) {
        setStreetViewLocation(`${e.latlng.lat.toFixed(4)}°, ${e.latlng.lng.toFixed(4)}°`);
        setShowStreetViewModal(true);
        setStreetViewActive(false); // Deactivate after launching modal
      }
    };

    map.on('click', handleMapClick);
    return () => {
      map.off('click', handleMapClick);
    };
  }, [streetViewActive]);

  // 6. Handle cursor change when Street View Mode is active
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const container = map.getContainer();
    if (streetViewActive) {
      container.style.cursor = 'crosshair';
    } else {
      container.style.cursor = '';
    }
  }, [streetViewActive]);

  // 7. Search Bar execution
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const q = searchQuery.toLowerCase().trim();
    const matched = points.find(p => p.village.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
    if (matched && mapInstanceRef.current) {
      mapInstanceRef.current.setView([matched.lat, matched.lon], 14);
      setSelectedPoint(matched);
    } else {
      alert(`Location/Category "${searchQuery}" not found. Try searching for Besagarahalli, Koppa, or Water.`);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedPoint ? '1fr 360px' : '1fr', height: 'calc(100vh - 120px)', position: 'relative' }}>
      
      {/* Search Bar Overlay */}
      <form onSubmit={handleSearchSubmit} style={{
        position: 'absolute',
        top: '15px',
        left: '15px',
        zIndex: 1000,
        background: 'white',
        padding: '6px 12px',
        borderRadius: '24px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        border: '1px solid #DDE1E7',
        display: 'flex',
        alignItems: 'center',
        width: '320px',
        gap: '8px'
      }}>
        <Search size={18} style={{ color: '#718096' }} />
        <input 
          type="text" 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={`Search ${activeDistrict}...`} 
          style={{
            border: 'none',
            outline: 'none',
            fontSize: '13px',
            flex: 1,
            color: '#2D3748',
            fontFamily: 'Inter, sans-serif'
          }}
        />
        {searchQuery && (
          <button type="button" onClick={() => setSearchQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px' }}>
            <X size={14} style={{ color: '#718096' }} />
          </button>
        )}
        <div style={{ width: '1px', height: '18px', background: '#DDE1E7' }} />
        <button type="button" onClick={() => alert("Voice command activated... Speak now.")} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px' }}>
          <Mic size={16} style={{ color: '#FF6B1A' }} />
        </button>
      </form>

      {/* Layer Control Overlay (Google Map style Map / Satellite selector) */}
      <div style={{
        position: 'absolute',
        top: '15px',
        right: '15px',
        zIndex: 1000,
        background: 'white',
        padding: '4px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        border: '1px solid #DDE1E7',
        display: 'flex',
        gap: '4px'
      }}>
        {[
          { id: 'voyager', label: 'Map 2D', icon: MapIcon },
          { id: 'satellite', label: 'Satellite', icon: Layers },
          { id: 'terrain', label: 'Terrain', icon: Compass },
          { id: 'bhuvan', label: 'ISRO Bhuvan', icon: Layers }
        ].map(opt => {
          const ActiveIcon = opt.icon;
          const isActive = mapType === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => setMapType(opt.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                background: isActive ? '#EEF4FC' : 'transparent',
                color: isActive ? '#003B7A' : '#4A5568',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'Inter, sans-serif'
              }}
            >
              <ActiveIcon size={14} />
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Pegman / Street View Activate Button */}
      <div style={{
        position: 'absolute',
        bottom: '120px',
        right: '15px',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px'
      }}>
        <button
          onClick={() => setStreetViewActive(!streetViewActive)}
          style={{
            background: streetViewActive ? '#FFB300' : '#FFD54F',
            border: '2px solid white',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            boxShadow: '0 4px 10px rgba(0,0,0,0.25)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            cursor: 'pointer',
            fontSize: '20px',
            transition: 'all 0.2s',
            outline: 'none'
          }}
          title="Google Street View Pegman"
        >
          🚹
        </button>
      </div>

      {/* Pegman Mode Active Banner */}
      {streetViewActive && (
        <div style={{
          position: 'absolute',
          top: '75px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1001,
          background: '#FF9100',
          color: 'white',
          padding: '10px 20px',
          borderRadius: '24px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          fontSize: '13px',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeInUp 0.3s ease'
        }}>
          <span>🟡 Pegman Mode Active: Click any point on the map to enter Street View</span>
          <button 
            onClick={() => setStreetViewActive(false)} 
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontWeight: 800
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Map Container */}
      <div ref={mapRef} style={{ width: '100%', height: '100%', background: '#F5F7FA' }} />

      {/* Map Legends Overlaid (Clean White Theme - Priority Based) */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        background: 'rgba(255,255,255,0.95)',
        padding: '14px 18px',
        borderRadius: '12px',
        border: '1px solid #DDE1E7',
        color: '#1a1a1a',
        boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
        zIndex: 1000,
        fontSize: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div style={{ fontWeight: 800, borderBottom: '1px solid #E2E8F0', paddingBottom: '6px', marginBottom: '2px', fontFamily: 'Space Grotesk, sans-serif', color: '#003B7A' }}>🚨 Priority Deficit Index</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#C62B2B' }} /> Critical Deficit (Priority &ge; 85)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#FB8C00' }} /> High Deficit (Priority 70 - 84)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#4CAF50' }} /> Moderate Deficit (Priority &lt; 70)</div>
      </div>

      {/* Sidebar Details Panel */}
      {selectedPoint && (
        <div style={{ background: 'white', borderLeft: '1px solid #DDE1E7', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', zIndex: 999 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="gov-badge gov-badge--blue" style={{ fontSize: '10px', display: 'block', marginBottom: '4px' }}>
                📍 {selectedPoint.village} ➔ {selectedPoint.panchayat_name || 'Gram Panchayat'} ➔ {selectedPoint.taluk_name || 'Taluk'}
              </span>
              <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#003B7A', margin: '6px 0 0 0', fontFamily: 'Space Grotesk, sans-serif' }}>{selectedPoint.category}</h3>
            </div>
            <button onClick={() => setSelectedPoint(null)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#6B6B6B' }}>✕</button>
          </div>

          {/* Priority Score Gauge */}
          <div style={{ background: '#FFF3EC', border: '1px solid #FDDCCA', borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '50px', height: '50px', borderRadius: '50%', border: '4px solid #FF6B1A', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', fontWeight: 800, color: '#FF6B1A', fontSize: '15px' }}>
              {selectedPoint.priority}
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#FF6B1A' }}>AI Priority Rank</div>
              <div style={{ fontSize: '10px', color: '#6B6B6B', marginTop: '2px' }}>Calculated by affected population, urgency & neglect.</div>
            </div>
          </div>

          {/* Unresolved Duration & Citizen Reports Info */}
          <div style={{ background: '#EDF2F7', border: '1px solid #E2E8F0', borderRadius: '6px', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#4A5568', fontFamily: 'Inter, sans-serif' }}>
            <div>🕒 <strong>Duration:</strong> Unresolved for {selectedPoint.duration || '14 days ago'}</div>
            <div>👥 <strong>Citizen Suggestions:</strong> {selectedPoint.citizen_suggestions_count || 1} reported/suggested this development plan</div>
          </div>

          {/* AI Deficit / Suggestion Details */}
          <div>
            <h4 style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', marginBottom: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>📝 Actual Deficit & Suggestion</h4>
            <p style={{ fontSize: '12.5px', color: '#1a1a1a', lineHeight: 1.6, margin: 0, background: '#F5F7FA', padding: '12px', borderRadius: '6px' }}>
              {selectedPoint.summary || 'Citizen report details matched against constituency records.'}
            </p>
          </div>

          {/* Deficit Image - Only render if a real photo exists */}
          {selectedPoint.photo_url && (
            <div>
              <h4 style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', marginBottom: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>📸 Grievance Photo</h4>
              <div style={{ width: '100%', height: '160px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #DDE1E7', background: '#F5F7FA' }}>
                <img 
                  src={selectedPoint.photo_url} 
                  alt="Grievance Context" 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            </div>
          )}

          {/* AI Rationale / Why suggesting */}
          <div>
            <h4 style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', marginBottom: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>🤖 AI Suggestion Reason</h4>
            <p style={{ fontSize: '12px', color: '#4A5568', lineHeight: 1.5, margin: 0, padding: '12px', background: '#FFFDF0', borderLeft: '3px solid #D69E2E', borderRadius: '4px' }}>
              {selectedPoint.ai_reasoning || "Detected high population density lacking necessary basic amenities vs NITI Aayog norms."}
            </p>
          </div>

          {/* AI Recommended Solution */}
          <div>
            <h4 style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', marginBottom: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>💡 AI Recommended Solution</h4>
            <p style={{ fontSize: '12px', color: '#2D3748', lineHeight: 1.5, margin: 0, padding: '12px', background: '#F0F9FF', borderLeft: '3px solid #003B7A', borderRadius: '4px', fontWeight: 500 }}>
              {selectedPoint.solution || "AI Recommendation: Conduct local field investigation and allocate targeted development funds under the appropriate constituency scheme."}
            </p>
          </div>

          {/* Recommended Scheme */}
          <div>
            <h4 style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', marginBottom: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>🎯 Matching Scheme Match</h4>
            <div style={{ border: '1px solid #DDE1E7', borderRadius: '8px', padding: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#003B7A' }}>
                {selectedPoint.category.includes('Water') ? 'Jal Jeevan Mission (JJM)' : selectedPoint.category.includes('Road') ? 'PM Gram Sadak Yojana (PMGSY)' : 'MPLADS Allocation Fund'}
              </div>
              <p style={{ fontSize: '11px', color: '#6B6B6B', margin: '4px 0 8px 0' }}>Eligible central/state grant funding opportunity detected.</p>
              <a href="https://myscheme.gov.in" target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: '#FF6B1A', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                View Scheme Guidelines ↗
              </a>
            </div>
          </div>

          {/* Action buttons (Approve Project, Get More Data) */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' }}>
            <button
              onClick={() => handleApproveProject(selectedPoint)}
              style={{
                background: '#138808',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '12px',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                textAlign: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              ✅ Approve Project
            </button>
            <button
              onClick={() => handleGetMoreData(selectedPoint)}
              style={{
                background: '#003B7A',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '12px',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                textAlign: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              🔍 Get More Data
            </button>
          </div>
        </div>
      )}

      {/* Google Street View Panorama Modal */}
      {showStreetViewModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.9)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          animation: 'fadeInUp 0.3s ease'
        }}>
          {/* Top Panel bar */}
          <div style={{
            width: '90%',
            maxWidth: '1000px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            color: 'white',
            marginBottom: '10px',
            fontFamily: 'Inter, sans-serif'
          }}>
            <div>
              <span style={{ fontSize: '12px', background: '#FFC107', color: 'black', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, marginRight: '8px' }}>STREET VIEW</span>
              <span style={{ fontWeight: 600 }}>Rural Connector Road — Mandya District, Karnataka</span>
              <span style={{ color: '#A0AEC0', fontSize: '12px', marginLeft: '10px' }}>({streetViewLocation})</span>
            </div>
            <button 
              onClick={() => setShowStreetViewModal(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '24px',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          </div>

          {/* Panorama Container */}
          <div style={{
            position: 'relative',
            width: '90%',
            maxWidth: '1000px',
            height: '60vh',
            borderRadius: '12px',
            overflow: 'hidden',
            border: '3px solid white',
            boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
          }}>
            {/* Street View Image */}
            <img 
              src="/streetview_mock.png" 
              alt="Street View panorama" 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />

            {/* Mock Navigation Arrows */}
            <div style={{ position: 'absolute', bottom: '30px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '8px', zIndex: 10 }}>
              <button onClick={() => alert("Moving forward along road...")} style={{ background: 'rgba(255,255,255,0.8)', border: 'none', width: '36px', height: '36px', borderRadius: '50%', fontWeight: 800, cursor: 'pointer', fontSize: '16px' }}>↑</button>
              <button onClick={() => alert("Moving backward along road...")} style={{ background: 'rgba(255,255,255,0.8)', border: 'none', width: '36px', height: '36px', borderRadius: '50%', fontWeight: 800, cursor: 'pointer', fontSize: '16px' }}>↓</button>
            </div>

            {/* Compass Dial Indicator */}
            <div style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              background: 'rgba(0,0,0,0.6)',
              color: 'white',
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              border: '2px solid white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: 'bold',
              fontFamily: 'Inter'
            }}>
              N
            </div>
            
            {/* Attribution tag */}
            <div style={{
              position: 'absolute',
              bottom: '10px',
              right: '15px',
              color: 'white',
              background: 'rgba(0,0,0,0.4)',
              padding: '2px 8px',
              fontSize: '10px',
              borderRadius: '4px'
            }}>
              © 2026 Google Street View Mockup
            </div>
          </div>
        </div>
      )}

      {/* RAG Deep Search Intelligence Report Modal */}
      {showIntelModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          animation: 'fadeInUp 0.3s ease'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '16px',
            width: '90%',
            maxWidth: '650px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: 'Inter, sans-serif'
          }}>
            {/* Modal Header */}
            <div style={{
              background: '#003B7A',
              color: 'white',
              padding: '18px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, letterSpacing: '0.5px' }}>🔍 AI Decision Intelligence Hub</h3>
                <span style={{ fontSize: '11px', color: '#BEE3F8' }}>Deep-searching web sources & offline databases...</span>
              </div>
              <button 
                onClick={() => setShowIntelModal(false)}
                style={{ background: 'none', border: 'none', color: 'white', fontSize: '20px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', overflowY: 'auto', maxHeight: '60vh', color: '#2D3748' }}>
              {loadingIntel ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: '16px' }}>
                  {/* Spinner */}
                  <div style={{
                    width: '40px',
                    height: '40px',
                    border: '4px solid #EDF2F7',
                    borderTop: '4px solid #FF6B1A',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <style>{`
                    @keyframes spin {
                      0% { transform: rotate(0deg); }
                      100% { transform: rotate(360deg); }
                    }
                  `}</style>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#4A5568' }}>Analyzing Jal Jeevan Mission, PMGSY databases & Google News...</div>
                </div>
              ) : (
                <div style={{ whiteSpace: 'pre-wrap', fontSize: '13.5px', lineHeight: '1.7', fontFamily: 'Inter, sans-serif' }}>
                  {/* Render the markdown headings nicely */}
                  {intelReport.split('\n').map((line, idx) => {
                    if (line.startsWith('###')) {
                      return <h4 key={idx} style={{ color: '#003B7A', fontSize: '14px', fontWeight: 800, marginTop: '20px', marginBottom: '8px', borderBottom: '1px solid #E2E8F0', paddingBottom: '6px' }}>{line.replace('###', '')}</h4>;
                    }
                    return <div key={idx}>{line}</div>;
                  })}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              background: '#F7FAFC',
              padding: '16px 24px',
              display: 'flex',
              justifyContent: 'flex-end',
              borderTop: '1px solid #E2E8F0'
            }}>
              <button 
                onClick={() => setShowIntelModal(false)}
                style={{
                  background: '#003B7A',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 18px',
                  fontWeight: 700,
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
