import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  auth, db, signOut, onSnapshot, collection, query, where, doc, getDoc
} from './firebase';
import AuthScreen from './components/AuthScreen';
import ConstituencyMap from './components/ConstituencyMap';
import WhatsAppSimulator from './components/WhatsAppSimulator';
import ScraperConsole from './components/ScraperConsole';
import fallbackDistrictsMap from './districts_data.json';
import districtCoordsMap from './district_coords.json';
import L from 'leaflet';
import * as d3 from 'd3';
import confetti from 'canvas-confetti';
import {
  LayoutDashboard, Volume2, Camera, FileText, SlidersHorizontal, Bot,
  Upload, CheckCircle2, XCircle, RefreshCw, ArrowRight, TrendingUp,
  MapPin, HelpCircle, Users, ChevronRight, Briefcase, FileSpreadsheet,
  AlertCircle, Shield, Activity, Calendar, DollarSign, Globe, Clock,
  Sparkles, CheckSquare, ListTodo, Database, Tv, FileDown, ChevronDown,
  Bell, Search, LogOut, Home, Phone, Mail, ExternalLink, Star, Award, Map
} from 'lucide-react';

// Fix Leaflet Default Icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png'
});

const schoolIcon = L.divIcon({
  html: '<div style="width:12px;height:12px;background:#003B7A;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
  className: '', iconSize: [12, 12], iconAnchor: [6, 6]
});
const clinicIcon = L.divIcon({
  html: '<div style="width:12px;height:12px;background:#138808;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
  className: '', iconSize: [12, 12], iconAnchor: [6, 6]
});
const complaintIcon = L.divIcon({
  html: '<div style="width:14px;height:14px;background:#C62B2B;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(198,43,43,0.5)"></div>',
  className: '', iconSize: [14, 14], iconAnchor: [7, 7]
});

// ============================================================
// GOVERNMENT HEADER COMPONENT
// ============================================================
function GovHeader({ portalLabel, portalColor, currentUser, onExit }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const accentColorMap = {
    citizen: '#003B7A',
    official: '#FF6B1A',
    officer: '#138808',
    admin: '#C62B2B',
  };
  const accentColor = accentColorMap[portalColor] || '#003B7A';

  return (
    <header style={{ background: '#003B7A', fontFamily: 'Inter, sans-serif', position: 'relative', zIndex: 100 }}>
      {/* ── DESKTOP HEADER (hidden on mobile via CSS) ── */}
      <div className="gov-header-desktop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 32px', height: '64px' }}>
        {/* Logo + title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <div style={{ width: '38px', height: '38px', background: 'white', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontSize: '18px' }}>🇮🇳</span>
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: 'white', fontWeight: 800, fontSize: '18px', letterSpacing: '-0.3px', lineHeight: 1, whiteSpace: 'nowrap' }}>MP MITRA</div>
            <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: '9px', fontWeight: 500, letterSpacing: '0.07em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>National AI Governance Intelligence Platform</div>
          </div>
        </div>

        {/* Portal label */}
        <div style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '20px', padding: '4px 14px', color: 'white', fontSize: '12px', fontWeight: 600, whiteSpace: 'nowrap', flexShrink: 0 }}>
          {portalLabel}
        </div>

        {/* User + exit */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexShrink: 0 }}>
          {currentUser && (
            <>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'white', fontSize: '12px', fontWeight: 600, lineHeight: 1, maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{currentUser.displayName || currentUser.email}</div>
                <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '10px', textTransform: 'uppercase', fontWeight: 500 }}>{currentUser.role}</div>
              </div>
              <button onClick={onExit} style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '6px', color: 'white', padding: '6px 12px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                <LogOut size={13} /> Exit
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── MOBILE HEADER (hidden on desktop via CSS) ── */}
      <div className="gov-header-mobile" style={{ display: 'none', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', height: '56px' }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '34px', height: '34px', background: 'white', borderRadius: '5px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontSize: '16px' }}>🇮🇳</span>
          </div>
          <div>
            <div style={{ color: 'white', fontWeight: 800, fontSize: '16px', lineHeight: 1 }}>MP MITRA</div>
            <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: '9px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Gov. Intelligence Platform</div>
          </div>
        </div>

        {/* Hamburger button */}
        <button
          onClick={() => setMobileMenuOpen(o => !o)}
          style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.22)', borderRadius: '6px', color: 'white', padding: '8px 10px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center', justifyContent: 'center' }}
          aria-label="Toggle menu"
        >
          <span style={{ display: 'block', width: '18px', height: '2px', background: mobileMenuOpen ? 'transparent' : 'white', transition: 'all 0.2s' }} />
          <span style={{ display: 'block', width: '18px', height: '2px', background: 'white', transform: mobileMenuOpen ? 'rotate(45deg) translate(0, -1px)' : 'none', transition: 'all 0.2s', marginTop: mobileMenuOpen ? '2px' : 0 }} />
          <span style={{ display: 'block', width: '18px', height: '2px', background: 'white', transform: mobileMenuOpen ? 'rotate(-45deg) translate(0, -1px)' : 'none', transition: 'all 0.2s' }} />
        </button>
      </div>

      {/* ── MOBILE DROPDOWN MENU ── */}
      {mobileMenuOpen && (
        <div className="gov-header-mobile-menu" style={{ display: 'none', background: '#002d5c', borderTop: '1px solid rgba(255,255,255,0.12)', padding: '16px', flexDirection: 'column', gap: '12px', animation: 'slideDown 0.2s ease' }}>
          {/* Portal badge */}
          <div style={{ background: `${accentColor}30`, border: `1px solid ${accentColor}60`, borderRadius: '8px', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>{portalColor === 'official' ? '🏛️' : portalColor === 'officer' ? '⚙️' : portalColor === 'admin' ? '🛡️' : '👥'}</span>
            <div>
              <div style={{ color: 'white', fontSize: '13px', fontWeight: 700 }}>{portalLabel}</div>
              <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>Current Portal</div>
            </div>
          </div>

          {/* User info */}
          {currentUser && (
            <div style={{ background: 'rgba(255,255,255,0.07)', borderRadius: '8px', padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ color: 'white', fontSize: '13px', fontWeight: 600 }}>{currentUser.displayName || currentUser.email}</div>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '10px', textTransform: 'uppercase', fontWeight: 600, marginTop: '2px' }}>{currentUser.role}</div>
              </div>
              <button onClick={() => { setMobileMenuOpen(false); onExit(); }} style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'rgba(198,43,43,0.2)', border: '1px solid rgba(198,43,43,0.4)', borderRadius: '6px', color: '#ff8a8a', padding: '7px 12px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                <LogOut size={13} /> Exit
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tricolor accent strip */}
      <div style={{ display: 'flex', height: '3px' }}>
        <div style={{ flex: 1, background: '#FF6B1A' }} />
        <div style={{ flex: 1, background: '#FFFFFF' }} />
        <div style={{ flex: 1, background: '#138808' }} />
      </div>
    </header>
  );
}

// ============================================================
// GOVERNMENT PAGE TITLE BANNER
// ============================================================
function GovPageBanner({ title, subtitle, breadcrumbs }) {
  return (
    <div style={{ background: '#EEF3FA', borderBottom: '1px solid #DDE1E7', padding: '16px 32px' }}>
      {breadcrumbs && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#6B6B6B', marginBottom: '6px' }}>
          <span style={{ color: '#003B7A', cursor: 'pointer' }}>Home</span>
          {breadcrumbs.map((b, i) => (
            <React.Fragment key={i}>
              <ChevronRight size={12} />
              <span style={{ color: i === breadcrumbs.length - 1 ? '#1a1a1a' : '#003B7A', fontWeight: i === breadcrumbs.length - 1 ? 600 : 400 }}>{b}</span>
            </React.Fragment>
          ))}
        </div>
      )}
      <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>{title}</h1>
      {subtitle && <p style={{ fontSize: '13px', color: '#6B6B6B', margin: '4px 0 0', lineHeight: 1.5 }}>{subtitle}</p>}
    </div>
  );
}

// ============================================================
// STAT CARD COMPONENT
// ============================================================
function StatCard({ label, value, color = '#003B7A', icon: Icon, sub, onClick, active }) {
  const isClickable = !!onClick;
  return (
    <div 
      onClick={onClick}
      style={{ 
        background: active ? '#F0F7FF' : 'white', 
        border: active ? `2px solid ${color}` : '1.5px solid #DDE1E7', 
        borderRadius: '10px', 
        padding: '20px', 
        borderTop: active ? `6px solid ${color}` : `3.5px solid ${color}`, 
        boxShadow: active ? '0 4px 12px rgba(0,0,0,0.1)' : '0 1px 4px rgba(0,0,0,0.06)',
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'all 0.2s',
        position: 'relative',
        transform: active ? 'scale(1.02)' : 'none',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6B6B6B' }}>{label}</span>
        {Icon && <div style={{ width: '32px', height: '32px', background: `${color}15`, borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color }}><Icon size={16} /></div>}
      </div>
      <div style={{ fontSize: '28px', fontWeight: 800, color: '#1a1a1a', lineHeight: 1, fontFamily: 'Space Grotesk, sans-serif' }}>{value}</div>
      {sub && <div style={{ fontSize: '11px', color: '#6B6B6B', marginTop: '6px' }}>{sub}</div>}
      {isClickable && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px', fontSize: '9px', fontWeight: 700, color: color, textTransform: 'uppercase', gap: '4px', alignItems: 'center' }}>
          <span>{active ? '🟢 Showing Details' : '🔍 Click to drill down'}</span>
        </div>
      )}
    </div>
  );
}

// ============================================================
// SECTION HEADER COMPONENT
// ============================================================
function SectionHeader({ title, subtitle, accent = '#FF6B1A' }) {
  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '4px', height: '22px', background: accent, borderRadius: '2px', flexShrink: 0 }} />
        <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>{title}</h2>
      </div>
      {subtitle && <p style={{ fontSize: '12px', color: '#6B6B6B', margin: '4px 0 0 14px' }}>{subtitle}</p>}
    </div>
  );
}

// using imported fallbackDistrictsMap from ./districts_data.json

function generateMockConstituencyData(state, district) {
  const sUpper = (state || 'GOA').toUpperCase();
  const dUpper = (district || 'NORTH GOA').toUpperCase();
  
  // Resolve base lat/lng from our coordinates database
  let baseLat = 19.0;
  let baseLng = 78.5;
  if (districtCoordsMap[sUpper] && districtCoordsMap[sUpper][dUpper]) {
    baseLat = districtCoordsMap[sUpper][dUpper][0];
    baseLng = districtCoordsMap[sUpper][dUpper][1];
  }

  // Use a simple hash code of state + district to get deterministic mock values
  const str = sUpper + dUpper;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  const absHash = Math.abs(hash);

  const health_score = 72 + (absHash % 18);
  const pop = 120000 + (absHash % 80000);
  const sc_st = 12 + (absHash % 15);
  
  // Schools
  const schoolsCount = 35 + (absHash % 30);
  const teachers = 120 + (absHash % 80);
  const students = Math.floor(teachers * (22 + (absHash % 12)));
  const avg_ptr = parseFloat((students / teachers).toFixed(1));
  
  // Healthcare
  const clinics = 6 + (absHash % 10);
  const chc = Math.floor(clinics * 0.15) || 1;
  const phc = Math.floor(clinics * 0.35) || 2;
  const subcentre = clinics - chc - phc;
  
  // Roads
  const roads = 25 + (absHash % 35);
  const completed = Math.floor(roads * (0.55 + (absHash % 30) / 100));
  const total_cost = 320 + (absHash % 900); // In Lakhs
  const avg_cost = 14.2 + (absHash % 10);
  
  // Water
  const habs = 40 + (absHash % 45);
  const fully_covered = Math.floor(habs * (0.6 + (absHash % 25) / 100));
  const quality_records = 2 + (absHash % 6);
  
  const map_points = {
    schools: Array.from({ length: 5 }, (_, i) => ({
      code: `SCH-${absHash % 1000}-${i}`,
      name: `${dUpper} Government School #${i + 1}`,
      category: i % 2 === 0 ? "Primary only" : "Upper Primary with Secondary",
      type: "Co-educational",
      teachers: 4 + (i % 4),
      students: 90 + (i * 25),
      lat: baseLat + Math.sin(i + absHash) * 0.05,
      lng: baseLng + Math.cos(i + absHash) * 0.05
    })),
    clinics: Array.from({ length: 4 }, (_, i) => ({
      id: absHash % 100 + i,
      name: `${dUpper} PHC Clinic #${i + 1}`,
      type: i === 0 ? "CHC" : i === 1 ? "PHC" : "Subcentre",
      lat: baseLat + Math.cos(i + absHash + 2) * 0.05,
      lng: baseLng + Math.sin(i + absHash + 2) * 0.05,
      location_type: "Rural"
    })),
    complaints: [
      { id: "c1", text: "Regular load shedding affecting drinking water filtration plants", category: "Water Supply", urgency: "High", lat: baseLat + 0.015, lng: baseLng - 0.01, status: "Pending", date: "2026-07-05", village: "Centroid Sector" },
      { id: "c2", text: "Poor PTR ratio and lack of mathematics teachers in Government High School", category: "Education", urgency: "Medium", lat: baseLat - 0.02, lng: baseLng + 0.025, status: "Verified", date: "2026-07-04", village: "West Habitation" },
      { id: "c3", text: "Road connectivity cut off due to waterlogging and potholes", category: "Roads", urgency: "High", lat: baseLat - 0.01, lng: baseLng - 0.03, status: "In Progress", date: "2026-07-03", village: "South Palli" }
    ]
  };

  return {
    constituency: `${dUpper}, ${sUpper}`,
    health_score,
    metrics: {
      population: pop,
      sc_st_percentage: sc_st,
      schools: { count: schoolsCount, students, teachers, avg_ptr },
      healthcare: { count: clinics, chc, phc, subcentre },
      roads: { count: roads, completed, total_cost_cr: parseFloat((total_cost/100).toFixed(2)), avg_cost_per_km_lakh: avg_cost },
      water: { total_habitations: habs, fully_covered, quality_records, contaminants: { "Fluoride": 2, "Iron": 1, "Salinity": 1 } }
    },
    map_points
  };
}

// ============================================================
// FUNCTION LEVEL DASHBOARD COMPONENT
// ============================================================
function FunctionLevelDashboard({ selectedState, selectedDistrict, constituencyData, firestoreComplaints }) {
  const [selectedDept, setSelectedDept] = useState('water');
  
  // Interactive KPI drill-down states
  const [activeCardId, setActiveCardId] = useState(null);
  const [detailData, setDetailData] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // Safe extraction of metrics
  const metrics = constituencyData?.metrics || {
    population: 150000,
    schools: { count: 48, students: 3840, teachers: 120, avg_ptr: 32.0 },
    healthcare: { count: 12, chc: 2, phc: 4, subcentre: 6 },
    roads: { count: 45, completed: 28, total_cost_cr: 5.2, avg_cost_per_km_lakh: 16.5 },
    water: { total_habitations: 64, fully_covered: 38, quality_records: 4, contaminants: { "Fluoride": 2, "Iron": 1, "Salinity": 1 } }
  };

  const departments = [
    { id: 'water', label: 'Water Supply', sub: 'Jal Jeevan Mission', icon: '💧', color: '#003B7A', bg: '#EEF3FA' },
    { id: 'education', label: 'Primary Education', sub: 'Samagra Shiksha', icon: '📚', color: '#FF6B1A', bg: '#FFF3EC' },
    { id: 'health', label: 'Primary Healthcare', sub: 'National Health Mission', icon: '🏥', color: '#138808', bg: '#EAF6EA' },
    { id: 'roads', label: 'Road Connectivity', sub: 'PMGSY Phase III', icon: '🛣️', color: '#C62B2B', bg: '#FDECEA' },
    { id: 'digital', label: 'Digital Connectivity', sub: 'BharatNet Program', icon: '🌐', color: '#6A0DAD', bg: '#F3E8FF' }
  ];

  const currentDept = departments.find(d => d.id === selectedDept);

  // Reset drill-down details when department changes
  useEffect(() => {
    setActiveCardId(null);
    setDetailData([]);
  }, [selectedDept]);

  // Fetch detailed card data
  useEffect(() => {
    if (!activeCardId) return;
    
    // Backend queries for large tables (water, roads, education, health)
    setDetailLoading(true);
    let url = '';
    
    if (selectedDept === 'education') {
      if (activeCardId === 'all_schools' || activeCardId === 'teaching_staff') {
        url = `/api/constituency/school-list?state=${selectedState}&district=${selectedDistrict}`;
      } else if (activeCardId === 'ptr_deficit') {
        url = `/api/constituency/school-list?state=${selectedState}&district=${selectedDistrict}&status=ptr_deficit`;
      }
    } else if (selectedDept === 'health') {
      if (activeCardId === 'all_clinics') {
        url = `/api/constituency/clinic-list?state=${selectedState}&district=${selectedDistrict}`;
      } else if (activeCardId === 'clinics_10k') {
        url = `/api/constituency/clinic-list?state=${selectedState}&district=${selectedDistrict}&type=chc_phc`;
      } else if (activeCardId === 'subcentres') {
        url = `/api/constituency/clinic-list?state=${selectedState}&district=${selectedDistrict}&type=subcentre`;
      }
    } else if (selectedDept === 'water') {
      if (activeCardId === 'fully_covered') {
        url = `/api/constituency/habitation-list?state=${selectedState}&district=${selectedDistrict}&status=fully_covered`;
      } else if (activeCardId === 'quality_incidents') {
        url = `/api/constituency/water-quality-list?state=${selectedState}&district=${selectedDistrict}`;
      } else if (activeCardId === 'habitations_deficit') {
        url = `/api/constituency/habitation-list?state=${selectedState}&district=${selectedDistrict}&status=partially_covered`;
      }
    } else if (selectedDept === 'roads') {
      if (activeCardId === 'all_roads') {
        url = `/api/constituency/road-list?state=${selectedState}&district=${selectedDistrict}`;
      } else if (activeCardId === 'completion_rate') {
        url = `/api/constituency/road-list?state=${selectedState}&district=${selectedDistrict}&status=completed`;
      } else if (activeCardId === 'capital_outlay') {
        url = `/api/constituency/road-list?state=${selectedState}&district=${selectedDistrict}&status=pending`;
      }
    } else if (selectedDept === 'digital') {
      // Mock digital details for GP connections
      setDetailData([
        { gp: 'Katteri GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Koppa GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Maddur GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Besagarahalli GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Huliyurdurga GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Malavalli GP', status: 'Pending Link', speed: '0 Mbps', type: 'RF link' },
        { gp: 'Pandavapura GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
        { gp: 'Srirangapatna GP', status: 'Connected', speed: '100 Mbps', type: 'FTTH' },
      ]);
      setDetailLoading(false);
      return;
    }

    if (url) {
      fetch(url)
        .then(r => r.json())
        .then(data => {
          setDetailData(data.records || []);
          setDetailLoading(false);
        })
        .catch(err => {
          console.error(err);
          setDetailLoading(false);
        });
    }
  }, [activeCardId, selectedState, selectedDistrict, selectedDept, constituencyData]);

  // Filter complaints based on department keywords
  const getFilteredComplaints = () => {
    const list = firestoreComplaints && firestoreComplaints.length > 0 ? firestoreComplaints : constituencyData?.map_points?.complaints || [];
    return list.filter(c => {
      const cat = (c.category || '').toLowerCase();
      const txt = (c.text || '').toLowerCase();
      if (selectedDept === 'water') return cat.includes('water') || txt.includes('water') || txt.includes('pipe') || txt.includes('leakage') || cat.includes('sanitation');
      if (selectedDept === 'education') return cat.includes('school') || cat.includes('education') || txt.includes('school') || txt.includes('teacher') || txt.includes('education');
      if (selectedDept === 'health') return cat.includes('health') || cat.includes('clinic') || txt.includes('health') || txt.includes('hospital') || txt.includes('doctor') || cat.includes('medical');
      if (selectedDept === 'roads') return cat.includes('road') || txt.includes('road') || txt.includes('pothole') || txt.includes('bridge') || cat.includes('infrastructure');
      if (selectedDept === 'digital') return cat.includes('digital') || txt.includes('internet') || txt.includes('broadband') || txt.includes('wi-fi') || txt.includes('bharatnet') || txt.includes('mobile') || txt.includes('network');
      return false;
    });
  };

  const deptComplaints = getFilteredComplaints();

  // Department-specific mock recommendations
  const getDeptRecommendations = () => {
    const dName = selectedDistrict ? (selectedDistrict.charAt(0).toUpperCase() + selectedDistrict.slice(1).toLowerCase()) : 'Mandya';
    if (selectedDept === 'water') return [
      { action: `Repair Main Pipeline Leakage in ${dName} Rural Sector 2`, cost: '₹12 Lakhs', impact: '3,200 Citizens', score: '94/100' },
      { action: `Establish Community Water Purification Plant in ${dName} East`, cost: '₹24 Lakhs', impact: '1,800 Citizens', score: '88/100' }
    ];
    if (selectedDept === 'education') return [
      { action: `Deploy 3 Mathematics & Science Teachers to ${dName} Centroid High School`, cost: 'N/A (Re-allocation)', impact: '480 Students', score: '91/100' },
      { action: 'Construct Girls Sanitary Blocks in 4 Rural Primary Schools', cost: '₹15 Lakhs', impact: '900 Girls', score: '86/100' }
    ];
    if (selectedDept === 'health') return [
      { action: `Upgrade ${dName} Rural Primary Health Centre to Community Health Centre (CHC)`, cost: '₹1.8 Crores', impact: '12,500 Citizens', score: '97/100' },
      { action: `Procure Diagnostic Lab Equipment for ${dName} South PHC Centroid`, cost: '₹35 Lakhs', impact: '6,000 Citizens', score: '84/100' }
    ];
    if (selectedDept === 'roads') return [
      { action: `Lay All-weather Bituminous PMGSY Road connecting ${dName} Rural to Highway`, cost: '₹1.4 Crores', impact: '5,000 Citizens', score: '92/100' },
      { action: `Reconstruct Damaged Culvert Bridge near ${dName} West Habitation`, cost: '₹28 Lakhs', impact: '2,400 Citizens', score: '85/100' }
    ];
    return [
      { action: 'Extend Fiber Drop cables to connect 8 remaining Gram Panchayats', cost: '₹42 Lakhs', impact: '9,500 Citizens', score: '89/100' },
      { action: 'Deploy Public Wi-Fi Hotspots at Gram Panchayat libraries', cost: '₹8 Lakhs', impact: '3,000 Students', score: '82/100' }
    ];
  };

  const deptRecs = getDeptRecommendations();

  // Render department metrics
  const renderDeptMetrics = () => {
    switch (selectedDept) {
      case 'water':
        const wCov = metrics.water.total_habitations > 0 
          ? ((metrics.water.fully_covered / metrics.water.total_habitations) * 100).toFixed(1) 
          : '58.0';
        return (
          <>
            <StatCard label="Fully Covered Habitations" value={`${metrics.water.fully_covered} / ${metrics.water.total_habitations}`} color="#003B7A" sub={`Coverage rate: ${wCov}%`} onClick={() => setActiveCardId(activeCardId === 'fully_covered' ? null : 'fully_covered')} active={activeCardId === 'fully_covered'} />
            <StatCard label="Water Quality Incidents" value={metrics.water.quality_records} color="#FF6B1A" sub="Fluoride and Salinity reports" onClick={() => setActiveCardId(activeCardId === 'quality_incidents' ? null : 'quality_incidents')} active={activeCardId === 'quality_incidents'} />
            <StatCard label="Habitations Deficit" value={metrics.water.total_habitations - metrics.water.fully_covered} color="#C62B2B" sub="Habitations under partial cover" onClick={() => setActiveCardId(activeCardId === 'habitations_deficit' ? null : 'habitations_deficit')} active={activeCardId === 'habitations_deficit'} />
          </>
        );
      case 'education':
        return (
          <>
            <StatCard label="Total Schools Supported" value={metrics.schools.count} color="#003B7A" sub={`Total Students: ${metrics.schools.students}`} onClick={() => setActiveCardId(activeCardId === 'all_schools' ? null : 'all_schools')} active={activeCardId === 'all_schools'} />
            <StatCard label="Pupil-Teacher Ratio (PTR)" value={`${metrics.schools.avg_ptr} : 1`} color={metrics.schools.avg_ptr > 30 ? '#C62B2B' : '#138808'} sub={`NITI Standard target: 30.0:1`} onClick={() => setActiveCardId(activeCardId === 'ptr_deficit' ? null : 'ptr_deficit')} active={activeCardId === 'ptr_deficit'} />
            <StatCard label="Total Teaching Staff" value={metrics.schools.teachers} color="#138808" sub="Full-time registered teachers" onClick={() => setActiveCardId(activeCardId === 'teaching_staff' ? null : 'teaching_staff')} active={activeCardId === 'teaching_staff'} />
          </>
        );
      case 'health':
        const hCov = metrics.healthcare.count > 0 
          ? ((metrics.healthcare.count / (metrics.population / 10000))).toFixed(2) 
          : '1.2';
        return (
          <>
            <StatCard label="Total Health Facilities" value={metrics.healthcare.count} color="#003B7A" sub={`CHCs: ${metrics.healthcare.chc} | PHCs: ${metrics.healthcare.phc}`} onClick={() => setActiveCardId(activeCardId === 'all_clinics' ? null : 'all_clinics')} active={activeCardId === 'all_clinics'} />
            <StatCard label="Clinics per 10k Population" value={hCov} color={parseFloat(hCov) < 2.0 ? '#FF6B1A' : '#138808'} sub="WHO Minimum Target: 2.0" onClick={() => setActiveCardId(activeCardId === 'clinics_10k' ? null : 'clinics_10k')} active={activeCardId === 'clinics_10k'} />
            <StatCard label="Subcentres Active" value={metrics.healthcare.subcentre} color="#138808" sub="Rural community outreach posts" onClick={() => setActiveCardId(activeCardId === 'subcentres' ? null : 'subcentres')} active={activeCardId === 'subcentres'} />
          </>
        );
      case 'roads':
        const rComp = metrics.roads.count > 0 
          ? ((metrics.roads.completed / metrics.roads.count) * 100).toFixed(1) 
          : '64.5';
        return (
          <>
            <StatCard label="Road Construction Projects" value={metrics.roads.count} color="#003B7A" sub={`Completed: ${metrics.roads.completed}`} onClick={() => setActiveCardId(activeCardId === 'all_roads' ? null : 'all_roads')} active={activeCardId === 'all_roads'} />
            <StatCard label="Project Completion Rate" value={`${rComp}%`} color={parseFloat(rComp) < 70 ? '#FF6B1A' : '#138808'} sub="Active PMGSY portfolio status" onClick={() => setActiveCardId(activeCardId === 'completion_rate' ? null : 'completion_rate')} active={activeCardId === 'completion_rate'} />
            <StatCard label="Total Capital Outlay" value={`₹${metrics.roads.total_cost_cr} Cr`} color="#138808" sub={`Avg cost: ₹${metrics.roads.avg_cost_per_km_lakh} Lakhs/km`} onClick={() => setActiveCardId(activeCardId === 'capital_outlay' ? null : 'capital_outlay')} active={activeCardId === 'capital_outlay'} />
          </>
        );
      case 'digital':
        const hash = (selectedState + selectedDistrict).length;
        const gpConnected = 70 + (hash % 25);
        return (
          <>
            <StatCard label="Gram Panchayat Connected" value={`${gpConnected}%`} color="#6A0DAD" sub="Fiber backhaul complete" onClick={() => setActiveCardId(activeCardId === 'gp_connected' ? null : 'gp_connected')} active={activeCardId === 'gp_connected'} />
            <StatCard label="Public Hotspots Deployed" value={14 + (hash % 12)} color="#138808" sub="Active high-speed nodes" onClick={() => setActiveCardId(activeCardId === 'hotspots' ? null : 'hotspots')} active={activeCardId === 'hotspots'} />
            <StatCard label="Fiber Laid Length" value={`${120 + (hash % 80)} km`} color="#003B7A" sub="Under BharatNet Phase II" onClick={() => setActiveCardId(activeCardId === 'fiber_laid' ? null : 'fiber_laid')} active={activeCardId === 'fiber_laid'} />
          </>
        );
      default:
        return null;
    }
  };

  const getDeptHealthScore = () => {
    if (selectedDept === 'water') {
      const wCov = metrics.water.total_habitations > 0 ? (metrics.water.fully_covered / metrics.water.total_habitations) : 0.6;
      // Fix: bound and scale penalty to prevent negative scores
      const score = Math.round(50 + wCov * 45 - Math.min(25, metrics.water.quality_records * 0.1));
      return Math.max(0, Math.min(100, score));
    }
    if (selectedDept === 'education') {
      const ptrDiff = metrics.schools.avg_ptr > 30 ? (metrics.schools.avg_ptr - 30) : 0;
      return Math.max(0, Math.min(100, Math.round(92 - ptrDiff * 3)));
    }
    if (selectedDept === 'health') {
      const hCov = metrics.healthcare.count > 0 ? (metrics.healthcare.count / (metrics.population / 10000)) : 1.5;
      return Math.max(0, Math.min(100, Math.round(60 + Math.min(35, hCov * 15))));
    }
    if (selectedDept === 'roads') {
      const rComp = metrics.roads.count > 0 ? (metrics.roads.completed / metrics.roads.count) : 0.65;
      return Math.max(0, Math.min(100, Math.round(55 + rComp * 40)));
    }
    const hash = (selectedState + selectedDistrict).length;
    return Math.max(0, Math.min(100, 75 + (hash % 20)));
  };

  const deptHealthScore = getDeptHealthScore();
  const healthColor = deptHealthScore > 85 ? '#138808' : deptHealthScore > 70 ? '#FF6B1A' : '#C62B2B';
  const healthBg = deptHealthScore > 85 ? '#EAF6EA' : deptHealthScore > 70 ? '#FFF3EC' : '#FDECEA';

  return (
    <>
      <GovPageBanner 
        title="Function-Level Performance Dashboard" 
        subtitle={`Detailed department intelligence analysis for ${selectedDistrict}, ${selectedState}`} 
        breadcrumbs={['MP Dashboard', 'Function Level']} 
      />

      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Department Selector Tabs */}
        <div className="gov-card" style={{ padding: '14px', background: 'white' }}>
          <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
            {departments.map(dept => {
              const active = selectedDept === dept.id;
              return (
                <button
                  key={dept.id}
                  onClick={() => setSelectedDept(dept.id)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: '12px 16px',
                    background: active ? dept.bg : '#F5F7FA',
                    border: '1.5px solid',
                    borderColor: active ? dept.color : '#DDE1E7',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    minWidth: '150px'
                  }}
                >
                  <span style={{ fontSize: '22px', marginBottom: '6px' }}>{dept.icon}</span>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: active ? dept.color : '#1a1a1a' }}>{dept.label}</span>
                  <span style={{ fontSize: '10px', color: '#6B6B6B', marginTop: '2px' }}>{dept.sub}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Top KPIs Row */}
        <div className="gov-grid-split" style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '20px' }}>
          {/* Functional Health Card */}
          <div className="gov-card" style={{ padding: '24px', borderTop: `4px solid ${currentDept.color}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', background: healthBg }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#6B6B6B', letterSpacing: '0.05em' }}>Functional Health</span>
            <div style={{ fontSize: '48px', fontWeight: 800, color: healthColor, margin: '14px 0', fontFamily: 'Space Grotesk, sans-serif' }}>
              {deptHealthScore}<span style={{ fontSize: '20px', fontWeight: 500, color: '#6B6B6B' }}>/100</span>
            </div>
            <span className="gov-badge" style={{ background: healthColor + '20', color: healthColor, fontWeight: 700 }}>
              {deptHealthScore > 85 ? '🟢 High Compliance' : deptHealthScore > 70 ? '🟡 Moderate Gaps' : '🔴 Critical Deficit'}
            </span>
          </div>

          {/* Department Specific KPIs */}
          <div className="gov-grid-3col" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
            {renderDeptMetrics()}
          </div>
        </div>

        {/* Drill-down Detail Panel */}
        {activeCardId && (
          <div className="gov-card" style={{ padding: '24px', borderLeft: `4px solid ${currentDept.color}`, background: '#FCFDFE', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1.5px solid #DDE1E7', paddingBottom: '10px' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>{currentDept.icon}</span> {activeCardId.replace(/_/g, ' ')} Drill-Down Directory
                </h3>
                <span style={{ fontSize: '11px', color: '#6B6B6B' }}>
                  Showing real-time records from {selectedDistrict.toUpperCase()} district database
                </span>
              </div>
              <button 
                onClick={() => setActiveCardId(null)}
                style={{ background: '#FFF3EC', border: '1px solid #FF6B1A', borderRadius: '6px', padding: '6px 12px', fontSize: '11px', fontWeight: 700, color: '#FF6B1A', cursor: 'pointer', transition: 'all 0.15s' }}
              >
                ✕ Close Drill-down
              </button>
            </div>
            
            {detailLoading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6B6B6B', fontSize: '13px', fontWeight: 600 }}>⏳ Querying live databases...</div>
            ) : detailData.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6B6B6B', fontSize: '13px' }}>📭 No records found matching this filter in database.</div>
            ) : (
              <div style={{ overflowX: 'auto', maxHeight: '350px' }}>
                <table className="gov-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: '#F0F4F8', textAlign: 'left' }}>
                      <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>#</th>
                      {selectedDept === 'water' && activeCardId === 'quality_incidents' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Block</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Panchayat</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Village</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Habitation</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Contaminant Parameter</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Year</th>
                        </>
                      )}
                      {selectedDept === 'water' && activeCardId !== 'quality_incidents' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Block</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Panchayat</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Village</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Habitation</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>SC Pop</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>ST Pop</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Gen Pop</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Coverage Status</th>
                        </>
                      )}
                      {selectedDept === 'education' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>School Name</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Category</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Type</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Students</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Teachers</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>PTR</th>
                        </>
                      )}
                      {selectedDept === 'health' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Facility Name</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Facility Type</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Location Type</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Latitude</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Longitude</th>
                        </>
                      )}
                      {selectedDept === 'roads' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Road Name</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Length (km)</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Outlay Cost</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Physical Status</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Stage Progress</th>
                        </>
                      )}
                      {selectedDept === 'digital' && (
                        <>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Gram Panchayat Name</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Connectivity Status</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Port Speed</th>
                          <th style={{ padding: '10px', fontWeight: 700, color: '#FFFFFF', borderBottom: '2.5px solid rgba(255,255,255,0.2)' }}>Backhaul Link Type</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {detailData.map((row, index) => {
                      const trStyle = { background: index % 2 === 0 ? 'white' : '#F9FBFD', borderBottom: '1px solid #E2E8F0' };
                      return (
                        <tr key={row.id || index} style={trStyle}>
                          <td style={{ padding: '10px', fontWeight: 600 }}>{index + 1}</td>
                          {selectedDept === 'water' && activeCardId === 'quality_incidents' && (
                            <>
                              <td style={{ padding: '10px' }}>{row.block}</td>
                              <td style={{ padding: '10px' }}>{row.panchayat}</td>
                              <td style={{ padding: '10px' }}>{row.village}</td>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.habitation}</td>
                              <td style={{ padding: '10px', color: '#C62B2B', fontWeight: 700 }}>⚠️ {row.parameter}</td>
                              <td style={{ padding: '10px' }}>{row.year}</td>
                            </>
                          )}
                          {selectedDept === 'water' && activeCardId !== 'quality_incidents' && (
                            <>
                              <td style={{ padding: '10px' }}>{row.block}</td>
                              <td style={{ padding: '10px' }}>{row.panchayat}</td>
                              <td style={{ padding: '10px' }}>{row.village}</td>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.habitation}</td>
                              <td style={{ padding: '10px' }}>{row.sc_pop}</td>
                              <td style={{ padding: '10px' }}>{row.st_pop}</td>
                              <td style={{ padding: '10px' }}>{row.gen_pop}</td>
                              <td style={{ padding: '10px' }}>
                                <span className={`gov-badge ${row.status?.toLowerCase().includes('fully') ? 'gov-badge--green' : 'gov-badge--blue'}`}>
                                  {row.status}
                                </span>
                              </td>
                            </>
                          )}
                          {selectedDept === 'education' && (
                            <>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.name}</td>
                              <td style={{ padding: '10px' }}>{row.category}</td>
                              <td style={{ padding: '10px' }}>{row.type}</td>
                              <td style={{ padding: '10px' }}>{row.students}</td>
                              <td style={{ padding: '10px' }}>{row.teachers}</td>
                              <td style={{ padding: '10px', fontWeight: 700, color: (row.students / (row.teachers || 1)) > 30 ? '#C62B2B' : '#138808' }}>
                                {(row.students / (row.teachers || 1)).toFixed(1)}:1
                              </td>
                            </>
                          )}
                          {selectedDept === 'health' && (
                            <>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.name}</td>
                              <td style={{ padding: '10px' }}>
                                <span className="gov-badge gov-badge--blue">{row.type}</span>
                              </td>
                              <td style={{ padding: '10px' }}>{row.location_type}</td>
                              <td style={{ padding: '10px', color: '#6B6B6B' }}>{row.lat.toFixed(4)}</td>
                              <td style={{ padding: '10px', color: '#6B6B6B' }}>{row.lng.toFixed(4)}</td>
                            </>
                          )}
                          {selectedDept === 'roads' && (
                            <>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.road_name}</td>
                              <td style={{ padding: '10px' }}>{row.length} km</td>
                              <td style={{ padding: '10px', fontWeight: 700, color: '#003B7A' }}>₹{(row.total_cost / 100000).toFixed(2)} Lakhs</td>
                              <td style={{ padding: '10px' }}>
                                <span className={`gov-badge ${row.physical_status?.toLowerCase() === 'completed' ? 'gov-badge--green' : 'gov-badge--saffron'}`}>
                                  {row.physical_status}
                                </span>
                              </td>
                              <td style={{ padding: '10px' }}>{row.stage_complete || 'N/A'}</td>
                            </>
                          )}
                          {selectedDept === 'digital' && (
                            <>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.gp}</td>
                              <td style={{ padding: '10px' }}>
                                <span className={`gov-badge ${row.status === 'Connected' ? 'gov-badge--green' : 'gov-badge--red'}`}>
                                  {row.status}
                                </span>
                              </td>
                              <td style={{ padding: '10px', fontWeight: 700 }}>{row.speed}</td>
                              <td style={{ padding: '10px', color: '#6B6B6B' }}>{row.type}</td>
                            </>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Charts & Interactive Section */}
        <div className="gov-grid-split" style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '20px' }}>
          {/* Main Visualizer */}
          <div className="gov-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '360px' }}>
            <SectionHeader title="Functional Gap Analysis & Village Priorities" subtitle="Target standard guidelines versus village aggregates" accent={currentDept.color} />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '20px' }}>
              
              {selectedDept === 'water' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', fontWeight: 600 }}>
                      <span>Jal Jeevan Mission Habitation Water Coverage</span>
                      <span>{((metrics.water.fully_covered / metrics.water.total_habitations) * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ height: '24px', background: '#EEF3FA', borderRadius: '12px', overflow: 'hidden', border: '1px solid #DDE1E7' }}>
                      <div style={{ width: `${(metrics.water.fully_covered / metrics.water.total_habitations) * 100}%`, background: '#003B7A', height: '100%', borderRadius: '12px', transition: 'width 0.5s' }} />
                    </div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', fontWeight: 600 }}>
                      <span>Water Quality Contaminant Severity Index</span>
                      <span style={{ color: '#FF6B1A' }}>Moderate</span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                      {Object.entries(metrics.water.contaminants || {}).map(([c, count], i) => (
                        <div key={i} style={{ flex: 1, padding: '10px', background: '#FFF3EC', border: '1px solid #FDDCCA', borderRadius: '6px', textAlign: 'center' }}>
                          <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600 }}>{c}</div>
                          <div style={{ fontSize: '16px', fontWeight: 800, color: '#FF6B1A' }}>{count} Areas</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {selectedDept === 'education' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '180px', borderBottom: '2px solid #DDE1E7', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '22%' }}>
                      <div style={{ height: '120px', width: '32px', background: '#EEF3FA', border: '1.5px dashed #003B7A', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <div style={{ height: '90px', width: '100%', background: '#003B7A' }} />
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#003B7A', marginTop: '6px', textAlign: 'center' }}>NITI Target (30:1)</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '22%' }}>
                      <div style={{ height: '120px', width: '32px', background: '#F5F7FA', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <div style={{ height: `${(metrics.schools.avg_ptr / 40) * 120}px`, width: '100%', background: metrics.schools.avg_ptr > 30 ? '#C62B2B' : '#138808' }} />
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#1a1a1a', marginTop: '6px', textAlign: 'center' }}>Constituency ({metrics.schools.avg_ptr}:1)</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '22%' }}>
                      <div style={{ height: '120px', width: '32px', background: '#F5F7FA', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <div style={{ height: '108px', width: '100%', background: '#C62B2B' }} />
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#C62B2B', marginTop: '6px', textAlign: 'center' }}>{selectedDistrict ? selectedDistrict.toUpperCase() : 'MANDYA'} Rural (36:1)</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '22%' }}>
                      <div style={{ height: '120px', width: '32px', background: '#F5F7FA', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <div style={{ height: '72px', width: '100%', background: '#138808' }} />
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#138808', marginTop: '6px', textAlign: 'center' }}>{selectedDistrict ? selectedDistrict.toUpperCase() : 'MANDYA'} Urban (24:1)</span>
                    </div>
                  </div>
                  <p style={{ fontSize: '11px', color: '#6B6B6B', margin: 0, textAlign: 'center', fontWeight: 500 }}>
                    ⚠️ Pupil-Teacher Ratio shows critical disparities. Rural habitations exceed the NITI Aayog standard by 20%.
                  </p>
                </div>
              )}

              {selectedDept === 'health' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                    <div style={{ padding: '16px', background: '#EAF6EA', border: '1px solid #C3E6C3', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', marginBottom: '4px' }}>🏥</div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#138808' }}>{metrics.healthcare.chc}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, textTransform: 'uppercase' }}>Community Centres (CHC)</div>
                    </div>
                    <div style={{ padding: '16px', background: '#EEF3FA', border: '1px solid #BEE3F8', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', marginBottom: '4px' }}>⚕️</div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#003B7A' }}>{metrics.healthcare.phc}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, textTransform: 'uppercase' }}>Primary Health (PHC)</div>
                    </div>
                    <div style={{ padding: '16px', background: '#F5F7FA', border: '1px solid #E2E8F0', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '24px', marginBottom: '4px' }}>🏠</div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#3A3A3A' }}>{metrics.healthcare.subcentre}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, textTransform: 'uppercase' }}>Sub-Centres</div>
                    </div>
                  </div>
                  <div style={{ padding: '10px 14px', background: '#FFF3EC', border: '1px solid #FDDCCA', borderRadius: '6px', fontSize: '11px', color: '#FF6B1A', lineHeight: 1.5, fontWeight: 500 }}>
                    💡 NITI guideline: 1 PHC per 30,000 population in plains, 1 per 20,000 in hilly/tribal areas.
                  </div>
                </div>
              )}

              {selectedDept === 'roads' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', fontWeight: 600 }}>
                      <span>PMGSY Connectivity Progress (Completed/Targeted)</span>
                      <span>{((metrics.roads.completed / metrics.roads.count) * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ height: '20px', background: '#FDECEA', borderRadius: '10px', overflow: 'hidden', border: '1px solid #DDE1E7' }}>
                      <div style={{ width: `${(metrics.roads.completed / metrics.roads.count) * 100}%`, background: '#C62B2B', height: '100%', borderRadius: '10px', transition: 'width 0.5s' }} />
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div style={{ padding: '12px', background: '#F5F7FA', borderRadius: '6px', border: '1.5px solid #DDE1E7' }}>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600 }}>AVERAGE COST PER KILOMETRE</div>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#1a1a1a', fontFamily: 'Space Grotesk' }}>₹{metrics.roads.avg_cost_per_km_lakh} Lakhs</div>
                    </div>
                    <div style={{ padding: '12px', background: '#F5F7FA', borderRadius: '6px', border: '1.5px solid #DDE1E7' }}>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600 }}>TOTAL EXPENDITURE APPROVED</div>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#1a1a1a', fontFamily: 'Space Grotesk' }}>₹{metrics.roads.total_cost_cr} Crores</div>
                    </div>
                  </div>
                </div>
              )}

              {selectedDept === 'digital' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', border: '6px solid #F3E8FF', borderTopColor: '#6A0DAD', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span style={{ fontSize: '15px', fontWeight: 800, color: '#6A0DAD' }}>
                        {70 + ((selectedState + selectedDistrict).length % 25)}%
                      </span>
                    </div>
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#1a1a1a', margin: '0 0 4px' }}>BharatNet Optical Fiber Ingestion</h4>
                      <p style={{ fontSize: '11px', color: '#6B6B6B', margin: 0, lineHeight: 1.5 }}>
                        High-speed broadband ring network connection is active for the Gram Panchayats in this district centroid. Ongoing works targeting remaining sectors.
                      </p>
                    </div>
                  </div>
                  <div style={{ padding: '10px', background: '#EEF3FA', borderRadius: '6px', border: '1px solid #DDE1E7', fontSize: '11px', color: '#003B7A', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
                    <span>📡 Public Wi-Fi Hotspots Status: ACTIVE</span>
                    <span>🔗 Fiber Ring Redundancy: 99.8%</span>
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* AI Advisor Recommendations */}
          <div className="gov-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '360px', overflowY: 'auto' }}>
            <SectionHeader title="AI Priority Directives" subtitle="Strategic interventions identified by deficit severity" accent={currentDept.color} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {deptRecs.map((rec, i) => (
                <div key={i} style={{ padding: '12px', background: '#F5F7FA', border: '1px solid #DDE1E7', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <span className="gov-badge" style={{ background: currentDept.color + '15', color: currentDept.color, fontSize: '10px', fontWeight: 700 }}>
                      Priority: {rec.score}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#3A3A3A' }}>{rec.cost}</span>
                  </div>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#1a1a1a', lineHeight: 1.4, marginBottom: '6px' }}>{rec.action}</div>
                  <div style={{ fontSize: '10px', color: '#6B6B6B' }}>Target Impact: <strong>{rec.impact}</strong></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Citizen Suggestions Feed */}
        <div className="gov-card" style={{ padding: '24px' }}>
          <SectionHeader title="Citizen Suggestions Feed" subtitle={`Active grievances filed under ${currentDept.label}`} accent={currentDept.color} />
          
          {deptComplaints.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', background: '#F5F7FA', borderRadius: '8px', border: '1.5px dashed #DDE1E7' }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>📋</div>
              <p style={{ fontSize: '13px', color: '#6B6B6B', margin: 0 }}>No active suggestions or grievances found for this department in {selectedDistrict}.</p>
            </div>
          ) : (
            <div className="gov-grid-2col" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
              {deptComplaints.map(c => (
                <div key={c.id} style={{ padding: '16px', background: '#F5F7FA', border: '1.5px solid #DDE1E7', borderRadius: '8px', position: 'relative' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span className={`gov-badge ${c.urgency === 'High' ? 'gov-badge--red' : 'gov-badge--blue'}`} style={{ fontSize: '10px' }}>
                      {c.urgency} Urgency
                    </span>
                    <span style={{ fontSize: '11px', color: '#999', fontWeight: 500 }}>{c.date}</span>
                  </div>
                  <p style={{ fontSize: '12px', color: '#1a1a1a', lineHeight: 1.6, margin: '0 0 10px', minHeight: '36px' }}>"{c.text}"</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #EBEBEB', paddingTop: '8px', fontSize: '11px', color: '#6B6B6B' }}>
                    <span>📍 Habitation: <strong>{c.village || 'General Area'}</strong></span>
                    <span style={{ color: c.status === 'Pending' ? '#FF6B1A' : '#138808', fontWeight: 700 }}>
                      ● {c.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </>
  );
}

// ============================================================

// ============================================================
// AI RECOMMENDATIONS PANEL — REAL-TIME PRIORITY SYSTEM
// ============================================================
function RecommendationsPanel({ sName, dName }) {
  const [activeFilter, setActiveFilter] = React.useState('ALL');
  const [activeCat, setActiveCat]       = React.useState('ALL');
  const [data, setData]                 = React.useState(null);
  const [loading, setLoading]           = React.useState(false);
  const [error, setError]               = React.useState(null);
  const [expandedId, setExpandedId]     = React.useState(null);
  const [lastFetch, setLastFetch]       = React.useState(null);

  const PRIORITY_COLORS = { HIGH: '#C62B2B', MID: '#D97706', LOW: '#138808' };
  const PRIORITY_BG     = { HIGH: '#FEF2F2', MID: '#FFFBEB', LOW: '#F0FDF4' };
  const PRIORITY_ICONS  = { HIGH: '🔴', MID: '🟡', LOW: '🟢' };
  const CAT_ICONS = {
    Healthcare: '🏥', 'Water Supply': '💧', Education: '📚',
    Roads: '🛣️', Electricity: '⚡', Connectivity: '📡', Sanitation: '🚰'
  };

  const fetchData = React.useCallback(async (priority, cat) => {
    const pf = priority !== undefined ? priority : activeFilter;
    const cf = cat !== undefined ? cat : activeCat;
    if (!sName || !dName) { setError('Please select a state and district.'); return; }
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams({ state: sName, district: dName, limit: 60 });
      if (pf !== 'ALL') params.append('priority', pf);
      if (cf !== 'ALL') params.append('category', cf);
      const res = await fetch(`/api/recommendations/priorities?${params}`);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const json = await res.json();
      if (json.status === 'error') throw new Error(json.error || 'Failed to load');
      setData(json);
      setLastFetch(new Date().toLocaleTimeString());
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }, [sName, dName, activeFilter, activeCat]);

  React.useEffect(() => { fetchData('ALL', 'ALL'); }, [sName, dName]);

  const handleFilter = (p) => { setActiveFilter(p); fetchData(p, activeCat); };
  const handleCat    = (c) => { setActiveCat(c);    fetchData(activeFilter, c); };

  const summary = data?.summary || { HIGH: 0, MID: 0, LOW: 0, total: 0 };
  const recs    = data?.recommendations || [];
  const allCats = ['ALL', ...new Set(recs.map(r => r.category))];

  return (
    <>
      <GovPageBanner
        title="AI Priority Recommendations"
        subtitle={`Real-time infrastructure deficit analysis — ${dName || 'Select District'}, ${sName || ''}`}
        breadcrumbs={['MP Dashboard','AI Recommendations']}
      />
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>

        {/* Priority Summary Cards — clickable filters */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '14px' }}>
          {[
            { label: 'HIGH Priority', key: 'HIGH', count: summary.HIGH, color: '#C62B2B', bg: '#FEF2F2', icon: '🔴', desc: 'Urgent — immediate action' },
            { label: 'MID Priority',  key: 'MID',  count: summary.MID,  color: '#D97706', bg: '#FFFBEB', icon: '🟡', desc: 'Plan within 6 months' },
            { label: 'LOW Priority',  key: 'LOW',  count: summary.LOW,  color: '#138808', bg: '#F0FDF4', icon: '🟢', desc: 'Include in next year plan' },
            { label: 'Total Issues',  key: 'ALL',  count: summary.total || (summary.HIGH+summary.MID+summary.LOW), color: '#003B7A', bg: '#EFF6FF', icon: '📋', desc: 'All infrastructure sectors' },
          ].map((s) => (
            <div key={s.key}
              onClick={() => handleFilter(s.key)}
              style={{
                background: activeFilter === s.key ? s.color : s.bg,
                borderRadius: '12px', padding: '16px',
                border: `2px solid ${activeFilter === s.key ? s.color : s.color + '30'}`,
                cursor: 'pointer', transition: 'all 0.18s',
                boxShadow: activeFilter === s.key ? `0 4px 14px ${s.color}50` : '0 1px 4px rgba(0,0,0,0.05)',
                color: activeFilter === s.key ? 'white' : 'inherit'
              }}>
              <div style={{ fontSize: '22px', marginBottom: '6px' }}>{s.icon}</div>
              <div style={{ fontSize: '26px', fontWeight: 800, color: activeFilter === s.key ? 'white' : s.color }}>
                {loading ? '…' : (s.count || 0)}
              </div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: activeFilter === s.key ? 'white' : '#1a1a1a', marginTop: '2px' }}>{s.label}</div>
              <div style={{ fontSize: '10.5px', color: activeFilter === s.key ? 'rgba(255,255,255,0.8)' : '#6B7280', marginTop: '3px' }}>{s.desc}</div>
            </div>
          ))}
        </div>

        {/* Filter + Category bar */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', background: 'white', padding: '12px 16px', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Category:</span>
          {allCats.map(c => (
            <button key={c} onClick={() => handleCat(c)} style={{
              padding: '5px 12px', borderRadius: '16px', border: '1.5px solid',
              borderColor: activeCat === c ? '#003B7A' : '#DDE1E7',
              background: activeCat === c ? '#003B7A' : 'white',
              color: activeCat === c ? 'white' : '#4A5568',
              fontWeight: 600, fontSize: '11.5px', cursor: 'pointer', transition: 'all 0.15s'
            }}>
              {CAT_ICONS[c] || ''} {c}
            </button>
          ))}
          <div style={{ marginLeft: 'auto' }}>
            <button onClick={() => { setActiveFilter('ALL'); setActiveCat('ALL'); fetchData('ALL','ALL'); }}
              disabled={loading} style={{
              padding: '6px 14px', borderRadius: '8px', border: '1px solid #DDE1E7',
              background: 'white', cursor: 'pointer', fontSize: '12px', fontWeight: 600, color: '#374151'
            }}>
              {loading ? '⏳ Loading…' : '🔄 Refresh'}
            </button>
          </div>
        </div>

        {/* Status bar */}
        {lastFetch && !loading && (
          <div style={{ fontSize: '11px', color: '#6B7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#22C55E', fontWeight: 700 }}>●</span>
            Live data from database · Last fetched {lastFetch} · {recs.length} records shown for {dName}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '36px', marginBottom: '14px' }}>⏳</div>
            <div style={{ fontSize: '14px', color: '#6B7280', fontWeight: 600 }}>Scanning infrastructure database for {dName}…</div>
            <div style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '6px' }}>Schools · Roads · Health Centres · Water Records · Citizen Complaints</div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div style={{ padding: '18px', background: '#FEF2F2', borderRadius: '10px', border: '1px solid #FECACA', color: '#991B1B', fontSize: '13px' }}>
            ⚠️ {error}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && recs.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#6B7280' }}>
            <div style={{ fontSize: '36px', marginBottom: '12px' }}>📭</div>
            <div style={{ fontWeight: 600, fontSize: '14px' }}>No {activeFilter !== 'ALL' ? activeFilter + ' priority ' : ''} issues found for {dName || 'selected district'}</div>
            <div style={{ fontSize: '12px', marginTop: '6px' }}>Database may not have records for this district yet.</div>
            <button onClick={() => { setActiveFilter('ALL'); setActiveCat('ALL'); fetchData('ALL','ALL'); }}
              style={{ marginTop: '14px', padding: '8px 20px', borderRadius: '8px', background: '#003B7A', color: 'white', border: 'none', cursor: 'pointer', fontSize: '13px' }}>
              Show All
            </button>
          </div>
        )}

        {/* Recommendation Cards Grid */}
        {!loading && !error && recs.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {recs.map(rec => {
              const expanded = expandedId === rec.id;
              const pc = rec.priority_color || PRIORITY_COLORS[rec.priority] || '#6B7280';
              const bg = PRIORITY_BG[rec.priority] || '#F8F9FA';
              return (
                <div key={rec.id} style={{
                  background: 'white', borderRadius: '12px',
                  border: '1px solid #E2E8F0', borderLeft: `4px solid ${pc}`,
                  boxShadow: '0 1px 5px rgba(0,0,0,0.06)', overflow: 'hidden'
                }}>
                  {/* Header */}
                  <div style={{ padding: '16px 18px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '8px' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '6px' }}>
                          <span style={{ background: bg, color: pc, padding: '3px 9px', borderRadius: '10px', fontSize: '10.5px', fontWeight: 800, border: `1px solid ${pc}30` }}>
                            {PRIORITY_ICONS[rec.priority] || '📌'} {rec.priority} PRIORITY
                          </span>
                          <span style={{ background: '#EFF6FF', color: '#1D4ED8', padding: '3px 9px', borderRadius: '10px', fontSize: '10.5px', fontWeight: 700 }}>
                            {CAT_ICONS[rec.category] || '📌'} {rec.category}
                          </span>
                        </div>
                        <h3 style={{ fontSize: '13.5px', fontWeight: 700, color: '#111827', margin: '0 0 4px', lineHeight: 1.35 }}>{rec.title}</h3>
                        <div style={{ fontSize: '11px', color: '#6B7280' }}>📍 {rec.location}</div>
                      </div>
                      {/* Score ring */}
                      <div style={{ textAlign: 'center', flexShrink: 0 }}>
                        <div style={{
                          width: '42px', height: '42px', borderRadius: '50%',
                          background: `conic-gradient(${pc} ${rec.score}%, #F3F4F6 0%)`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '11px', fontWeight: 800, color: pc,
                          boxShadow: `inset 0 0 0 5px white`
                        }}>{rec.score}</div>
                        <div style={{ fontSize: '9px', color: '#9CA3AF', fontWeight: 700, marginTop: '2px' }}>SCORE</div>
                      </div>
                    </div>

                    <p style={{ fontSize: '11.5px', color: '#374151', lineHeight: 1.55, margin: '0 0 8px',
                      display: '-webkit-box', WebkitLineClamp: expanded ? 999 : 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
                    }}>❓ {rec.problem}</p>

                    {/* Citizen voice */}
                    {rec.citizen_complaints > 0 && (
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px',
                        background: '#FFF7ED', border: '1px solid #FED7AA',
                        padding: '4px 10px', borderRadius: '8px', fontSize: '11px', color: '#92400E'
                      }}>
                        🗣️ <strong>{rec.citizen_complaints.toLocaleString('en-IN')}</strong> citizen complaints from {dName}
                      </div>
                    )}
                  </div>

                  {/* Toggle */}
                  <button onClick={() => setExpandedId(expanded ? null : rec.id)} style={{
                    width: '100%', padding: '7px 18px', background: '#F8FAFC',
                    border: 'none', borderTop: '1px solid #F0F2F5', cursor: 'pointer',
                    fontSize: '11px', color: '#5A6474', fontWeight: 600,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px'
                  }}>
                    {expanded ? '▲ Hide Details' : '▼ Full Analysis + Cost + Scheme'}
                  </button>

                  {/* Expanded */}
                  {expanded && (
                    <div style={{ padding: '14px 18px', background: '#FAFBFC', borderTop: '1px solid #F0F2F5' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px', color: '#374151', lineHeight: 1.6 }}>
                        <div style={{ padding: '10px 12px', background: 'white', borderRadius: '8px', border: '1px solid #E8EDF2' }}>
                          <div style={{ fontWeight: 700, color: '#003B7A', marginBottom: '3px' }}>🎯 Why Chosen (Evidence)</div>
                          <div>{rec.why_chosen}</div>
                        </div>
                        <div style={{ padding: '10px 12px', background: 'white', borderRadius: '8px', border: '1px solid #E8EDF2' }}>
                          <div style={{ fontWeight: 700, color: '#138808', marginBottom: '3px' }}>🛠️ Recommended Action</div>
                          <div>{rec.how_to_fix}</div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                          <div style={{ padding: '8px', background: 'white', borderRadius: '8px', border: '1px solid #E8EDF2', textAlign: 'center' }}>
                            <div style={{ fontSize: '9.5px', color: '#9CA3AF', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>Est. Cost</div>
                            <div style={{ fontSize: '13px', fontWeight: 800, color: '#1a1a1a' }}>
                              {rec.estimated_cost_lakh >= 100
                                ? `₹${(rec.estimated_cost_lakh/100).toFixed(1)} Cr`
                                : `₹${rec.estimated_cost_lakh} L`}
                            </div>
                          </div>
                          <div style={{ padding: '8px', background: 'white', borderRadius: '8px', border: '1px solid #E8EDF2', textAlign: 'center' }}>
                            <div style={{ fontSize: '9.5px', color: '#9CA3AF', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>Beneficiaries</div>
                            <div style={{ fontSize: '13px', fontWeight: 800, color: '#003B7A' }}>
                              {rec.beneficiaries ? (rec.beneficiaries).toLocaleString('en-IN') : '—'}
                            </div>
                          </div>
                          <div style={{ padding: '8px', background: 'white', borderRadius: '8px', border: '1px solid #E8EDF2', textAlign: 'center' }}>
                            <div style={{ fontSize: '9.5px', color: '#9CA3AF', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>Scheme</div>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#003B7A', lineHeight: 1.3 }}>{rec.scheme}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}

// VILLAGE PROJECT & HABITATION SEARCH COMPONENT
// ============================================================
function VillageProjectSearch({ selectedState, selectedDistrict }) {
  const [searchBlock, setSearchBlock] = useState('');
  const [searchPanchayat, setSearchPanchayat] = useState('');
  const [searchVillage, setSearchVillage] = useState('');
  const [searchHabitation, setSearchHabitation] = useState('');
  const [searchQualityParam, setSearchQualityParam] = useState('');
  const [searchYear, setSearchYear] = useState('2012');
  
  // Lists for dropdown options
  const [blocks, setBlocks] = useState([]);
  const [panchayats, setPanchayats] = useState([]);
  const [villages, setVillages] = useState([]);
  const [habitations, setHabitations] = useState([]);

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const [geoTree, setGeoTree] = useState(null);

  // 1. Fetch blocks when state/district changes
  useEffect(() => {
    if (!selectedState || !selectedDistrict) return;
    setBlocks([]);
    setSearchBlock('');
    setPanchayats([]);
    setSearchPanchayat('');
    setVillages([]);
    setSearchVillage('');
    setHabitations([]);
    setSearchHabitation('');

    const sKey = selectedState.toUpperCase();
    const dKey = selectedDistrict.toUpperCase();

    fetch(`/geo/${sKey}_${dKey}.json`)
      .then(r => {
        if (!r.ok) throw new Error("Local geo JSON not found");
        return r.json();
      })
      .then(tree => {
        setGeoTree(tree);
        setBlocks(Object.keys(tree).sort());
      })
      .catch(() => {
        fetch(`/api/constituency/filter-options?state=${selectedState}&district=${selectedDistrict}`)
          .then(r => r.json())
          .then(data => {
            setBlocks(data.blocks || []);
            setGeoTree(null);
          })
          .catch(() => {
            // Fallback mock blocks for demo
            setBlocks(['MANDYA CENTROID', 'MANDYA RURAL', 'RAMAPURA BLOCK']);
            setGeoTree(null);
          });
      });
  }, [selectedState, selectedDistrict]);

  // 2. Fetch panchayats when block changes
  useEffect(() => {
    if (!searchBlock) {
      setPanchayats([]);
      setSearchPanchayat('');
      setVillages([]);
      setSearchVillage('');
      setHabitations([]);
      setSearchHabitation('');
      return;
    }
    setPanchayats([]);
    setSearchPanchayat('');
    setVillages([]);
    setSearchVillage('');
    setHabitations([]);
    setSearchHabitation('');

    if (geoTree && geoTree[searchBlock]) {
      setPanchayats(Object.keys(geoTree[searchBlock]).sort());
    } else {
      fetch(`/api/constituency/filter-options?state=${selectedState}&district=${selectedDistrict}&block=${searchBlock}`)
        .then(r => r.json())
        .then(data => {
          setPanchayats(data.panchayats || []);
        })
        .catch(() => {
          setPanchayats(['RAMAPURA GP', 'KOTHIMIR GP', 'MANDYA TOWN GP']);
        });
    }
  }, [searchBlock, selectedState, selectedDistrict, geoTree]);

  // 3. Fetch villages when panchayat changes
  useEffect(() => {
    if (!searchPanchayat) {
      setVillages([]);
      setSearchVillage('');
      setHabitations([]);
      setSearchHabitation('');
      return;
    }
    setVillages([]);
    setSearchVillage('');
    setHabitations([]);
    setSearchHabitation('');

    if (geoTree && geoTree[searchBlock] && geoTree[searchBlock][searchPanchayat]) {
      setVillages(Object.keys(geoTree[searchBlock][searchPanchayat]).sort());
    } else {
      fetch(`/api/constituency/filter-options?state=${selectedState}&district=${selectedDistrict}&block=${searchBlock}&panchayat=${searchPanchayat}`)
        .then(r => r.json())
        .then(data => {
          setVillages(data.villages || []);
        })
        .catch(() => {
          setVillages(['RAMAPURA', 'KOTHIMIR', 'CENTROID VILLAGE']);
        });
    }
  }, [searchPanchayat, searchBlock, selectedState, selectedDistrict, geoTree]);

  // 4. Fetch habitations when village changes
  useEffect(() => {
    if (!searchVillage) {
      setHabitations([]);
      setSearchHabitation('');
      return;
    }
    setHabitations([]);
    setSearchHabitation('');

    if (geoTree && geoTree[searchBlock] && geoTree[searchBlock][searchPanchayat] && geoTree[searchBlock][searchPanchayat][searchVillage]) {
      setHabitations(geoTree[searchBlock][searchPanchayat][searchVillage].sort());
    } else {
      fetch(`/api/constituency/filter-options?state=${selectedState}&district=${selectedDistrict}&block=${searchBlock}&panchayat=${searchPanchayat}&village=${searchVillage}`)
        .then(r => r.json())
        .then(data => {
          setHabitations(data.habitations || []);
        })
        .catch(() => {
          setHabitations(['RAMAPURA COLONY', 'RAMAPURA WEST', 'RAMAPURA EAST']);
        });
    }
  }, [searchVillage, searchPanchayat, searchBlock, selectedState, selectedDistrict, geoTree]);

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setSearched(true);

    const params = new URLSearchParams();
    if (selectedState) params.append('state', selectedState);
    if (selectedDistrict) params.append('district', selectedDistrict);
    if (searchBlock) params.append('block', searchBlock);
    if (searchPanchayat) params.append('panchayat', searchPanchayat);
    if (searchVillage) params.append('village', searchVillage);
    if (searchHabitation) params.append('habitation', searchHabitation);
    if (searchQualityParam) params.append('quality_parameter', searchQualityParam);
    if (searchYear) params.append('year', searchYear);

    fetch(`/api/constituency/search-projects?${params.toString()}`)
      .then(r => {
        if (!r.ok) throw new Error("Search failed");
        return r.json();
      })
      .then(data => {
        setResults(data.projects || []);
        setLoading(false);
      })
      .catch(() => {
        // Fallback mock results if API fails (e.g. on Firebase Hosting static deployment)
        const mockResults = [
          {
            type: "Water Quality Contamination",
            state_name: selectedState || "TELANGANA",
            district_name: selectedDistrict || "ADILABAD",
            block_name: (searchBlock || "ADILABAD CENTROID").toUpperCase(),
            panchayat_name: (searchPanchayat || "RAMAPURA GP").toUpperCase(),
            village_name: (searchVillage || "RAMAPURA").toUpperCase(),
            habitation_name: (searchHabitation || "RAMAPURA COLONY").toUpperCase(),
            parameter: searchQualityParam || "FLUORIDE",
            year: searchYear || "2012",
            status: "Contaminated"
          },
          {
            type: "Habitation Coverage Status",
            state_name: selectedState || "TELANGANA",
            district_name: selectedDistrict || "ADILABAD",
            block_name: (searchBlock || "ADILABAD CENTROID").toUpperCase(),
            panchayat_name: (searchPanchayat || "RAMAPURA GP").toUpperCase(),
            village_name: (searchVillage || "RAMAPURA").toUpperCase(),
            habitation_name: (searchHabitation || "RAMAPURA WEST").toUpperCase(),
            parameter: "SC Pop: 140 | ST Pop: 320 | Gen Pop: 420",
            year: "01_04_" + (searchYear || "2012"),
            status: "Partially Covered"
          }
        ];
        setResults(mockResults);
        setLoading(false);
      });
  };

  return (
    <>
      <GovPageBanner 
        title="Village Project & Habitation Search" 
        subtitle="Search census records, water quality details, and habitation cover parameters" 
        breadcrumbs={['MP Dashboard', 'Village Search']} 
      />

      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Search Input Form Card */}
        <div className="gov-card" style={{ padding: '24px', background: 'white' }}>
          <SectionHeader title="Constituency Search Filter" subtitle="Provide parameters to narrow down search against national datasets" accent="#FF6B1A" />
          <form onSubmit={handleSearch} className="gov-grid-4col" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <div>
              <label className="gov-label">State</label>
              <input type="text" disabled value={selectedState} className="gov-input" />
            </div>
            <div>
              <label className="gov-label">District</label>
              <input type="text" disabled value={selectedDistrict} className="gov-input" />
            </div>
            <div>
              <label className="gov-label">Block Name</label>
              <select 
                value={searchBlock} 
                onChange={e=>setSearchBlock(e.target.value)} 
                disabled={blocks.length === 0}
                className="gov-input"
              >
                <option value="">— Select Block —</option>
                {blocks.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="gov-label">Panchayat Name</label>
              <select 
                value={searchPanchayat} 
                onChange={e=>setSearchPanchayat(e.target.value)} 
                disabled={!searchBlock || panchayats.length === 0}
                className="gov-input"
              >
                <option value="">— Select Panchayat —</option>
                {panchayats.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="gov-label">Village Name</label>
              <select 
                value={searchVillage} 
                onChange={e=>setSearchVillage(e.target.value)} 
                disabled={!searchPanchayat || villages.length === 0}
                className="gov-input"
              >
                <option value="">— Select Village —</option>
                {villages.map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="gov-label">Habitation Name</label>
              <select 
                value={searchHabitation} 
                onChange={e=>setSearchHabitation(e.target.value)} 
                disabled={!searchVillage || habitations.length === 0}
                className="gov-input"
              >
                <option value="">— Select Habitation —</option>
                {habitations.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
            <div>
              <label className="gov-label">Quality Parameter</label>
              <select value={searchQualityParam} onChange={e=>setSearchQualityParam(e.target.value)} className="gov-input">
                <option value="">— All Parameters —</option>
                <option value="Fluoride">Fluoride</option>
                <option value="Iron">Iron</option>
                <option value="Salinity">Salinity</option>
                <option value="Chloride">Chloride</option>
                <option value="Arsenic">Arsenic</option>
                <option value="Nitrate">Nitrate</option>
              </select>
            </div>
            <div>
              <label className="gov-label">Year</label>
              <select value={searchYear} onChange={e=>setSearchYear(e.target.value)} className="gov-input">
                <option value="2012">2012</option>
                <option value="2011">2011</option>
                <option value="2010">2010</option>
                <option value="2009">2009</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
              <button type="submit" disabled={loading} className="gov-btn gov-btn--saffron" style={{ padding: '12px 24px', fontSize: '13px' }}>
                {loading ? <RefreshCw size={15} className="animate-spin" /> : '🔍 Search Project & Village Records'}
              </button>
            </div>
          </form>
        </div>

        {/* Results Card */}
        {searched && (
          <div className="gov-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
            <SectionHeader title="Query Results" subtitle={`Found ${results.length} matches in database`} accent="#003B7A" />
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <RefreshCw size={32} className="animate-spin" style={{ color: '#FF6B1A', margin: '0 auto 12px' }} />
                <p style={{ fontSize: '13px', color: '#6B6B6B' }}>Searching NITI database records...</p>
              </div>
            ) : results.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', background: '#F5F7FA', borderRadius: '8px', border: '1.5px dashed #DDE1E7' }}>
                <p style={{ fontSize: '13px', color: '#6B6B6B', margin: 0 }}>No records found matching the specified search filters.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="gov-table">
                  <thead>
                    <tr>
                      <th>Record Type</th>
                      <th>Block</th>
                      <th>Panchayat</th>
                      <th>Village</th>
                      <th>Habitation</th>
                      <th>Parameter / Info</th>
                      <th>Year</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 700, color: '#003B7A' }}>{r.type}</td>
                        <td>{r.block_name}</td>
                        <td>{r.panchayat_name}</td>
                        <td>{r.village_name}</td>
                        <td>{r.habitation_name}</td>
                        <td>
                          <span className="gov-badge gov-badge--blue" style={{ fontSize: '11px', textTransform: 'none' }}>
                            {r.parameter}
                          </span>
                        </td>
                        <td>{r.year}</td>
                        <td>
                          <span className={`gov-badge ${
                            r.status.includes('Fully') || r.status.includes('Active') 
                              ? 'gov-badge--green' 
                              : r.status.includes('Partially') || r.status.includes('Contaminated') 
                                ? 'gov-badge--saffron' 
                                : 'gov-badge--red'
                          }`}>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

// ============================================================
// CARD DETAILS MODAL COMPONENT (Dynamic Census Drill-Down)
// ============================================================
function CardDetailsModal({ open, onClose, mode, constituencyData, searchQuery, setSearchQuery, selectedVillage, setSelectedVillage, selectedPanchayat, setSelectedPanchayat }) {
  if (!open || !constituencyData) return null;
  const metrics = constituencyData.metrics || {};

  const handleClose = () => {
    onClose();
  };

  const getTitle = () => {
    if (mode === 'population') return '👥 Demographic & Habitation Register';
    if (mode === 'villages') return '🏘️ Villages Census Directory';
    if (mode === 'panchayats') return '🏛️ Gram Panchayats Directory';
    if (mode === 'roads') return '🛣️ PMGSY Road Connectivity Portfolio';
    if (mode === 'water') return '💧 JJM Water Cover & Quality Audit';
    return 'Details';
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ background: 'white', borderRadius: '12px', width: '90%', maxWidth: '1000px', height: '80vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)' }}>
        {/* Modal Header */}
        <div style={{ padding: '16px 24px', background: '#003B7A', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, fontFamily: 'Space Grotesk, sans-serif' }}>{getTitle()}</h3>
          <button onClick={handleClose} style={{ background: 'none', border: 'none', color: 'white', fontSize: '20px', cursor: 'pointer', fontWeight: 700 }}>✕</button>
        </div>

        {/* Modal Search Panel */}
        {(!selectedVillage && !selectedPanchayat) && (
          <div style={{ padding: '14px 24px', borderBottom: '1px solid #E2E8F0', background: '#F8FAFC', display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase' }}>🔎 Search records:</span>
            <input
              type="text"
              placeholder={`Search by name, block, or status...`}
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', outline: 'none' }}
            />
            <button onClick={() => setSearchQuery('')} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid #DDE1E7', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 600, color: '#4A5568' }}>Clear</button>
          </div>
        )}

        {/* Modal Scroll Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          
          {/* ── MODE: POPULATION ── */}
          {mode === 'population' && (() => {
            const hList = metrics.villages_list || [];
            const allHabs = [];
            hList.forEach(v => {
              (v.habitations || []).forEach(h => {
                allHabs.push({ ...h, villageName: v.name });
              });
            });
            const filtered = allHabs.filter(h => 
              h.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
              h.villageName.toLowerCase().includes(searchQuery.toLowerCase())
            );

            // Compute demographics
            const totalPop = metrics.population || 0;
            const scStPct = metrics.sc_st_percentage || 0;
            const scPop = Math.round(totalPop * (scStPct / 100) * 0.6);
            const stPop = Math.round(totalPop * (scStPct / 100) * 0.4);
            const genPop = totalPop - scPop - stPop;

            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
                  <div style={{ background: '#EEF3FA', border: '1px solid #C5D3E8', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#003B7A' }}>{totalPop.toLocaleString()}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px', textTransform: 'uppercase' }}>Total Population</div>
                  </div>
                  <div style={{ background: '#FDECEA', border: '1px solid #FEB2B2', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#C62B2B' }}>{scPop.toLocaleString()}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px', textTransform: 'uppercase' }}>SC Demographics</div>
                  </div>
                  <div style={{ background: '#FFF3EC', border: '1px solid #FDDCCA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#FF6B1A' }}>{stPop.toLocaleString()}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px', textTransform: 'uppercase' }}>ST Demographics</div>
                  </div>
                  <div style={{ background: '#EAF6EA', border: '1px solid #C3E6C3', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#138808' }}>{genPop.toLocaleString()}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px', textTransform: 'uppercase' }}>General Demographics</div>
                  </div>
                </div>

                <div style={{ border: '1px solid #DDE1E7', borderRadius: '8px', overflow: 'hidden' }}>
                  <table className="gov-table" style={{ margin: 0 }}>
                    <thead>
                      <tr><th>Habitation Name</th><th>Parent Village</th><th>Population</th><th>JJM Status</th></tr>
                    </thead>
                    <tbody>
                      {filtered.map((h, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 600 }}>{h.name}</td>
                          <td>{h.villageName}</td>
                          <td>{h.population?.toLocaleString() || 0}</td>
                          <td>
                            <span className={`gov-badge ${h.status?.includes('Fully') ? 'gov-badge--green' : 'gov-badge--saffron'}`}>
                              {h.status || 'Partially Covered'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })()}

          {/* ── MODE: VILLAGES ── */}
          {mode === 'villages' && (() => {
            if (selectedVillage) {
              // Drill-down village details view
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button onClick={() => setSelectedVillage(null)} style={{ padding: '8px 16px', background: '#F5F7FA', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', color: '#003B7A' }}>← Back to Directory</button>
                    <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>📍 Village: {selectedVillage.name}</h2>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
                    <div style={{ background: '#EEF3FA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#003B7A' }}>{selectedVillage.population?.toLocaleString()}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>POPULATION</div>
                    </div>
                    <div style={{ background: '#FFF3EC', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#FF6B1A' }}>{selectedVillage.habitation_count}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>HABITATIONS</div>
                    </div>
                    <div style={{ background: '#EAF6EA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#138808' }}>{selectedVillage.school_count}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>SCHOOLS</div>
                    </div>
                    <div style={{ background: '#FDECEA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#C62B2B', textTransform: 'uppercase' }}>{selectedVillage.water_status}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>JJM STATUS</div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    {/* Habitations list */}
                    <div className="gov-card" style={{ padding: '16px' }}>
                      <SectionHeader title="Constituent Habitations" />
                      <table className="gov-table">
                        <thead><tr><th>Habitation</th><th>Population</th><th>JJM Cover</th></tr></thead>
                        <tbody>
                          {(selectedVillage.habitations || []).map((h, idx) => (
                            <tr key={idx}>
                              <td>{h.name}</td>
                              <td>{h.population?.toLocaleString()}</td>
                              <td><span className={`gov-badge ${h.status?.includes('Fully') ? 'gov-badge--green' : 'gov-badge--saffron'}`}>{h.status}</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Schools list */}
                    <div className="gov-card" style={{ padding: '16px' }}>
                      <SectionHeader title="Village Schools Directory" />
                      {(selectedVillage.schools || []).length === 0 ? (
                        <p style={{ fontSize: '12px', color: '#6B6B6B', fontStyle: 'italic', padding: '10px' }}>No government schools listed in this village.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {(selectedVillage.schools || []).map((s, idx) => (
                            <div key={idx} style={{ padding: '12px', background: '#F5F7FA', border: '1px solid #DDE1E7', borderRadius: '6px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', fontWeight: 700, color: '#003B7A' }}>
                                <span>{s.name}</span>
                                <span>PTR: {s.ptr}:1</span>
                              </div>
                              <div style={{ fontSize: '11px', color: '#6B6B6B', marginTop: '4px' }}>Category: {s.category} | Teachers: {s.teachers} | Students: {s.students}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            }

            const list = metrics.villages_list || [];
            const filtered = list.filter(v => v.name.toLowerCase().includes(searchQuery.toLowerCase()));
            return (
              <div style={{ border: '1px solid #DDE1E7', borderRadius: '8px', overflow: 'hidden' }}>
                <table className="gov-table" style={{ margin: 0 }}>
                  <thead>
                    <tr><th>Village Name</th><th>Habitations</th><th>Total Population</th><th>Schools count</th><th>JJM Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {filtered.map((v, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600 }}>{v.name}</td>
                        <td>{v.habitation_count}</td>
                        <td>{v.population?.toLocaleString() || 0}</td>
                        <td>{v.school_count}</td>
                        <td>
                          <span className={`gov-badge ${v.water_status?.includes('Fully') ? 'gov-badge--green' : 'gov-badge--saffron'}`}>
                            {v.water_status}
                          </span>
                        </td>
                        <td>
                          <button onClick={() => setSelectedVillage(v)} style={{ background: '#003B7A', border: 'none', color: 'white', padding: '4px 10px', fontSize: '11px', fontWeight: 700, borderRadius: '4px', cursor: 'pointer' }}>Drill-down →</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}

          {/* ── MODE: PANCHAYATS ── */}
          {mode === 'panchayats' && (() => {
            if (selectedPanchayat) {
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button onClick={() => setSelectedPanchayat(null)} style={{ padding: '8px 16px', background: '#F5F7FA', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', color: '#003B7A' }}>← Back to GP Directory</button>
                    <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>🏛️ Gram Panchayat: {selectedPanchayat.name}</h2>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                    <div style={{ background: '#EEF3FA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#003B7A' }}>{selectedPanchayat.population?.toLocaleString()}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>TOTAL POPULATION</div>
                    </div>
                    <div style={{ background: '#FFF3EC', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#FF6B1A' }}>{selectedPanchayat.village_count}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>CONSTITUENT VILLAGES</div>
                    </div>
                    <div style={{ background: '#EAF6EA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: '#138808', textTransform: 'uppercase' }}>{selectedPanchayat.water_status}</div>
                      <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>WATER COVER</div>
                    </div>
                  </div>

                  <div className="gov-card" style={{ padding: '16px' }}>
                    <SectionHeader title="Gram Panchayat Village Directory" />
                    <table className="gov-table">
                      <thead><tr><th>Village Name</th><th>JJM Status</th><th>Constituent Habitations</th></tr></thead>
                      <tbody>
                        {selectedPanchayat.villages.map((vName, idx) => {
                          const vObj = (metrics.villages_list || []).find(x => x.name.toUpperCase() === vName.toUpperCase());
                          return (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600 }}>{vName}</td>
                              <td><span className={`gov-badge ${vObj?.water_status?.includes('Fully') ? 'gov-badge--green' : 'gov-badge--saffron'}`}>{vObj?.water_status || 'Partially Covered'}</span></td>
                              <td>{vObj?.habitation_count || 1}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            }

            const list = metrics.panchayats_list || [];
            const filtered = list.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()));
            return (
              <div style={{ border: '1px solid #DDE1E7', borderRadius: '8px', overflow: 'hidden' }}>
                <table className="gov-table" style={{ margin: 0 }}>
                  <thead>
                    <tr><th>GP Name</th><th>Villages</th><th>Habitations</th><th>Total Population</th><th>JJM Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {filtered.map((p, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600 }}>{p.name}</td>
                        <td>{p.village_count}</td>
                        <td>{p.habitation_count}</td>
                        <td>{p.population?.toLocaleString() || 0}</td>
                        <td>
                          <span className={`gov-badge ${p.water_status?.includes('Fully') ? 'gov-badge--green' : 'gov-badge--saffron'}`}>
                            {p.water_status}
                          </span>
                        </td>
                        <td>
                          <button onClick={() => setSelectedPanchayat(p)} style={{ background: '#003B7A', border: 'none', color: 'white', padding: '4px 10px', fontSize: '11px', fontWeight: 700, borderRadius: '4px', cursor: 'pointer' }}>Drill-down →</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}

          {/* ── MODE: ROADS ── */}
          {mode === 'roads' && (() => {
            const list = metrics.roads_list || [];
            const filtered = list.filter(r => 
              r.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
              r.block.toLowerCase().includes(searchQuery.toLowerCase()) || 
              r.status.toLowerCase().includes(searchQuery.toLowerCase())
            );
            return (
              <div style={{ border: '1px solid #DDE1E7', borderRadius: '8px', overflow: 'hidden' }}>
                <table className="gov-table" style={{ margin: 0 }}>
                  <thead>
                    <tr><th>Road Name</th><th>Block / Habitation</th><th>Length (km)</th><th>Approved Cost</th><th>Surface Type</th><th>Execution Status</th></tr>
                  </thead>
                  <tbody>
                    {filtered.map((r, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600 }}>{r.name}</td>
                        <td>{r.block} / {r.habitation}</td>
                        <td>{r.length_km} km</td>
                        <td>₹{r.cost_lakh ? `${r.cost_lakh} L` : 'N/A'}</td>
                        <td>{r.surface}</td>
                        <td>
                          <span className={`gov-badge ${r.status?.includes('Completed') ? 'gov-badge--green' : r.status?.includes('Pending') ? 'gov-badge--red' : 'gov-badge--blue'}`}>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}

          {/* ── MODE: WATER ── */}
          {mode === 'water' && (() => {
            const wqList = metrics.water_quality_list || [];
            const filteredWq = wqList.filter(w => 
              w.village.toLowerCase().includes(searchQuery.toLowerCase()) || 
              w.parameter.toLowerCase().includes(searchQuery.toLowerCase())
            );
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Statistics card */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                  <div style={{ background: '#EEF3FA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#003B7A' }}>{metrics.water?.total_habitations || 0}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>TOTAL HABITATIONS</div>
                  </div>
                  <div style={{ background: '#EAF6EA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#138808' }}>{metrics.water?.fully_covered || 0}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>FULLY COVERED HABITATIONS</div>
                  </div>
                  <div style={{ background: '#FDECEA', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#C62B2B' }}>{metrics.water?.quality_records || 0}</div>
                    <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>WATER QUALITY INCIDENTS</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
                  <div className="gov-card" style={{ padding: '16px' }}>
                    <SectionHeader title="Water Contamination Incidents Register" />
                    {filteredWq.length === 0 ? (
                      <p style={{ fontSize: '12px', color: '#6B6B6B', fontStyle: 'italic', padding: '10px' }}>No active water quality contamination records registered.</p>
                    ) : (
                      <table className="gov-table">
                        <thead><tr><th>Village / Habitation</th><th>Block Name</th><th>Contaminant Parameter</th><th>Year Recorded</th></tr></thead>
                        <tbody>
                          {filteredWq.map((w, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600 }}>{w.village} / {w.habitation}</td>
                              <td>{w.block}</td>
                              <td><span className="gov-badge gov-badge--red">{w.parameter}</span></td>
                              <td>{w.year}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}

        </div>
      </div>
    </div>
  );
}

// ============================================================
// WEB SCRAPER DATABASE COMPONENT (Real-Time Crawled Assets)
// ============================================================
function WebScraperDatabaseConsole({ selectedState, selectedDistrict, crawledDataType, setCrawledDataType, crawledDataSearch, setCrawledDataSearch, crawledDataList, loadingCrawled, selectedCrawledItem, setSelectedCrawledItem }) {
  const getHeaderLabel = () => {
    if (crawledDataType === 'schemes') return '📚 Crawled Welfare Schemes Registry';
    if (crawledDataType === 'news') return '📰 Crawled Local News Intelligence';
    if (crawledDataType === 'tenders') return '🏗️ Crawled Infrastructure Bids & Tenders';
    return 'Web Scraper Database';
  };

  const getSourceIcon = (item) => {
    if (crawledDataType === 'schemes') return '📋';
    if (crawledDataType === 'news') return '🗞️';
    return '⚡';
  };

  return (
    <>
      <GovPageBanner 
        title="Web Scraper Crawled Database Console" 
        subtitle={`Audit and explore raw, real-time datasets ingested by BeautifulSoup scraper agents for ${selectedDistrict}, ${selectedState}`} 
        breadcrumbs={['MP Dashboard', 'Web Scraper Database']} 
      />

      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Scraper Stats & Filter Toolbar */}
        <div className="gov-card" style={{ padding: '20px', background: 'white' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            {/* Scraper Selector */}
            <div style={{ display: 'flex', gap: '8px' }}>
              {[
                { id: 'schemes', label: 'Welfare Schemes', icon: '📋' },
                { id: 'news', label: 'Local News alerts', icon: '🗞️' },
                { id: 'tenders', label: 'Gov Tenders', icon: '🏗️' }
              ].map(type => {
                const active = crawledDataType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => { setCrawledDataType(type.id); setSelectedCrawledItem(null); }}
                    style={{
                      padding: '8px 16px',
                      background: active ? '#003B7A' : '#F5F7FA',
                      color: active ? 'white' : '#4A5568',
                      border: '1.5px solid',
                      borderColor: active ? '#003B7A' : '#DDE1E7',
                      borderRadius: '6px',
                      fontSize: '12.5px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <span>{type.icon}</span> {type.label}
                  </button>
                );
              })}
            </div>

            {/* Keyword Search */}
            <div style={{ display: 'flex', gap: '8px', flex: 1, maxWidth: '400px' }}>
              <input
                type="text"
                placeholder={`Search crawled ${crawledDataType}...`}
                value={crawledDataSearch}
                onChange={e => setCrawledDataSearch(e.target.value)}
                style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', outline: 'none' }}
              />
              <button onClick={() => setCrawledDataSearch('')} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid #DDE1E7', borderRadius: '6px', fontSize: '12.5px', cursor: 'pointer', color: '#4A5568', fontWeight: 600 }}>Reset</button>
            </div>
          </div>
        </div>

        {/* Database List Panel */}
        <div className="gov-card" style={{ padding: '24px' }}>
          <SectionHeader title={getHeaderLabel()} subtitle={`Displaying ${crawledDataList.length} scraped records matching search criteria`} accent="#003B7A" />
          
          {loadingCrawled ? (
            <div style={{ textAlign: 'center', padding: '48px' }}>
              <div style={{ width: '32px', height: '32px', border: '3px solid #DDE1E7', borderTopColor: '#003B7A', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} className="animate-spin" />
              <p style={{ fontSize: '13px', color: '#6B6B6B' }}>Retrieving live crawled records from PostgreSQL...</p>
            </div>
          ) : crawledDataList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px', background: '#F5F7FA', borderRadius: '8px', border: '1.5px dashed #DDE1E7' }}>
              <p style={{ fontSize: '13px', color: '#6B6B6B', margin: 0 }}>No crawled records found matching state / district filters.</p>
              <p style={{ fontSize: '11px', color: '#999', marginTop: '6px' }}>Run the Web Scraper console under Admin tools to ingest live RSS & governmental data.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              {crawledDataList.map((item, idx) => {
                const subTitle = crawledDataType === 'schemes' ? item.ministry : crawledDataType === 'news' ? item.source : item.authority;
                const bodyText = crawledDataType === 'schemes' ? item.description : crawledDataType === 'news' ? item.summary : `Approved Cost: ${item.cost || 'Under Evaluation'}`;
                const category = item.category || 'General';
                const color = category.includes('Water') ? '#003B7A' : category.includes('Road') ? '#138808' : category.includes('School') ? '#FF6B1A' : '#C62B2B';
                
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedCrawledItem(item)}
                    className="gov-card"
                    style={{
                      padding: '16px',
                      borderLeft: `4px solid ${color}`,
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'all 0.15s',
                      background: 'white'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.06)'; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = ''; }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#999', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, color: '#003B7A', textTransform: 'uppercase' }}>{subTitle}</span>
                        <span>{item.crawled_at ? new Date(item.crawled_at).toLocaleDateString() : 'Recent'}</span>
                      </div>
                      <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#1a1a1a', margin: '0 0 6px 0', fontFamily: 'Space Grotesk, sans-serif', lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                        {item.title}
                      </h4>
                      <p style={{ fontSize: '12px', color: '#4A5568', margin: 0, lineHeight: 1.5, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                        {bodyText}
                      </p>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', borderTop: '1px solid #EDF2F7', paddingTop: '8px' }}>
                      <span className="gov-badge" style={{ background: `${color}15`, color: color, fontSize: '9px' }}>{category}</span>
                      <span style={{ fontSize: '11px', color: '#FF6B1A', fontWeight: 700 }}>Inspect Asset →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Crawled Asset Details Overlay Modal */}
        {selectedCrawledItem && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 99999 }}>
            <div style={{ background: 'white', borderRadius: '12px', width: '90%', maxWidth: '600px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span className="gov-badge gov-badge--blue" style={{ fontSize: '10px', textTransform: 'uppercase' }}>
                    {crawledDataType === 'schemes' ? 'Welfare Scheme' : crawledDataType === 'news' ? 'Local News Alert' : 'Construction Tender'}
                  </span>
                  <h3 style={{ margin: '6px 0 0 0', fontSize: '16px', fontWeight: 800, color: '#003B7A', fontFamily: 'Space Grotesk, sans-serif', lineHeight: 1.4 }}>{selectedCrawledItem.title}</h3>
                </div>
                <button onClick={() => setSelectedCrawledItem(null)} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', fontWeight: 700, color: '#6B6B6B' }}>✕</button>
              </div>

              <div style={{ borderTop: '1px solid #E2E8F0', paddingTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12.5px', color: '#4A5568', lineHeight: 1.6 }}>
                <div>
                  <strong>Source Authority / Ministry:</strong> <span style={{ color: '#1a1a1a', fontWeight: 600 }}>{crawledDataType === 'schemes' ? selectedCrawledItem.ministry : crawledDataType === 'news' ? selectedCrawledItem.source : selectedCrawledItem.authority}</span>
                </div>
                
                {crawledDataType === 'schemes' && (
                  <>
                    <div><strong>Target Demographic Eligibility:</strong> <span style={{ color: '#1a1a1a' }}>Gender: {selectedCrawledItem.eligibility_gender} | Age: {selectedCrawledItem.eligibility_age_min} to {selectedCrawledItem.eligibility_age_max} years | State: {selectedCrawledItem.eligibility_state}</span></div>
                    <div><strong>Max Annual Income Criteria:</strong> <span style={{ color: '#1a1a1a' }}>{selectedCrawledItem.eligibility_income ? `₹${selectedCrawledItem.eligibility_income.toLocaleString()}` : 'No Income Limit'}</span></div>
                    <div><strong>Occupation Coverage:</strong> <span style={{ color: '#1a1a1a' }}>{selectedCrawledItem.eligibility_occupation}</span></div>
                  </>
                )}

                {crawledDataType === 'news' && (
                  <>
                    <div><strong>Geographic Proximity:</strong> <span style={{ color: '#1a1a1a' }}>{selectedCrawledItem.district_name}, {selectedCrawledItem.state_name}</span></div>
                    <div><strong>AI Severity Classification:</strong> <strong style={{ color: selectedCrawledItem.severity_score >= 3.0 ? '#C62B2B' : '#FF6B1A' }}>{selectedCrawledItem.severity_score} / 5.0</strong></div>
                  </>
                )}

                {crawledDataType === 'tenders' && (
                  <>
                    <div><strong>Estimated Project Outlay:</strong> <span style={{ color: '#1a1a1a', fontWeight: 700 }}>{selectedCrawledItem.cost || 'Under Evaluation'}</span></div>
                    <div><strong>Bidding Deadline:</strong> <span style={{ color: '#C62B2B', fontWeight: 600 }}>{selectedCrawledItem.deadline || 'Closed'}</span></div>
                  </>
                )}

                <div>
                  <strong>Ingested Asset Summary:</strong>
                  <p style={{ margin: '4px 0 0 0', background: '#F8FAFC', padding: '12px', border: '1px solid #E2E8F0', borderRadius: '6px', fontSize: '12px', color: '#1a1a1a' }}>
                    {crawledDataType === 'schemes' ? selectedCrawledItem.description : crawledDataType === 'news' ? selectedCrawledItem.summary : selectedCrawledItem.title}
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '11px', color: '#999' }}>
                  <span>Crawled timestamp: {selectedCrawledItem.crawled_at ? new Date(selectedCrawledItem.crawled_at).toLocaleString() : 'N/A'}</span>
                  {selectedCrawledItem.link && (
                    <a href={selectedCrawledItem.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: '#FF6B1A', fontWeight: 700 }}>Open Source Portal ↗</a>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </>
  );
}

// ============================================================
// MAIN APP COMPONENT
// ============================================================
export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [firestoreComplaints, setFirestoreComplaints] = useState([]);
  const [firestoreProjects, setFirestoreProjects] = useState([]);
  const [selectedPortal, setSelectedPortal] = useState(null);
  const [activeTab, setActiveTab] = useState('home');

  // Interactive Card Modal states
  const [cardModalOpen, setCardModalOpen] = useState(false);
  const [cardModalMode, setCardModalMode] = useState(''); // 'population' | 'villages' | 'panchayats' | 'roads' | 'water'
  const [cardSearchQuery, setCardSearchQuery] = useState('');
  const [selectedDetailVillage, setSelectedDetailVillage] = useState(null);
  const [selectedDetailPanchayat, setSelectedDetailPanchayat] = useState(null);

  // Web Scraper Database states
  const [crawledDataType, setCrawledDataType] = useState('schemes');
  const [crawledDataSearch, setCrawledDataSearch] = useState('');
  const [crawledDataList, setCrawledDataList] = useState([]);
  const [loadingCrawled, setLoadingCrawled] = useState(false);
  const [selectedCrawledItem, setSelectedCrawledItem] = useState(null);

  // Constituency states — pre-populated so dropdowns are never blank before API responds
  const FALLBACK_STATES = [
    'ANDHRA PRADESH','ARUNACHAL PRADESH','ASSAM','BIHAR','CHHATTISGARH',
    'GOA','GUJARAT','HARYANA','HIMACHAL PRADESH','JHARKHAND','KARNATAKA',
    'KERALA','MADHYA PRADESH','MAHARASHTRA','MANIPUR','MEGHALAYA','MIZORAM',
    'NAGALAND','ODISHA','PUNJAB','RAJASTHAN','SIKKIM','TAMIL NADU','TELANGANA',
    'TRIPURA','UTTAR PRADESH','UTTARAKHAND','WEST BENGAL',
    'ANDAMAN AND NICOBAR ISLANDS','CHANDIGARH','DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
    'DELHI','JAMMU AND KASHMIR','LADAKH','LAKSHADWEEP','PUDUCHERRY'
  ];
  const FALLBACK_DISTRICTS_TELANGANA = [
    'ADILABAD','BHADRADRI KOTHAGUDEM','HYDERABAD','JAGTIAL','JANGAON',
    'JAYASHANKAR BHUPALPALLY','JOGULAMBA GADWAL','KAMAREDDY','KARIMNAGAR',
    'KHAMMAM','KUMURAM BHEEM ASIFABAD','MAHABUBABAD','MAHABUBNAGAR',
    'MANCHERIAL','MEDAK','MEDCHAL MALKAJGIRI','MULUGU','NAGARKURNOOL',
    'NALGONDA','NARAYANPET','NIRMAL','NIZAMABAD','PEDDAPALLI',
    'RAJANNA SIRCILLA','RANGAREDDY','SANGAREDDY','SIDDIPET','SURYAPET',
    'VIKARABAD','WANAPARTHY','WARANGAL RURAL','WARANGAL URBAN','YADADRI BHUVANAGIRI'
  ];
  const [states, setStates] = useState(FALLBACK_STATES);
  const [districts, setDistricts] = useState(() => {
    const savedState = localStorage.getItem('mp_state') || 'TELANGANA';
    return fallbackDistrictsMap[savedState.toUpperCase()] || FALLBACK_DISTRICTS_TELANGANA;
  });
  // MP constituency persisted in localStorage — locked until MP explicitly edits
  const [selectedState, setSelectedState] = useState(() => localStorage.getItem('mp_state') || 'TELANGANA');
  const [selectedDistrict, setSelectedDistrict] = useState(() => localStorage.getItem('mp_district') || 'ADILABAD');
  const [mpConstituencyLocked, setMpConstituencyLocked] = useState(true);
  const [constituencyData, setConstituencyData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Save MP state/district to localStorage whenever they change
  const handleStateChange = (s) => { setSelectedState(s); localStorage.setItem('mp_state', s); };
  const handleDistrictChange = (d) => { setSelectedDistrict(d); localStorage.setItem('mp_district', d); };

  const dName = selectedDistrict ? (selectedDistrict.charAt(0).toUpperCase() + selectedDistrict.slice(1).toLowerCase()) : 'Mandya';

  // Citizen kiosk states
  const [complaintText, setComplaintText] = useState('');
  const [recording, setRecording] = useState(false);
  const [submittingComplaint, setSubmittingComplaint] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [submissionLogs, setSubmissionLogs] = useState([]);
  const [speechLanguage, setSpeechLanguage] = useState('English');
  const [kioskState, setKioskState] = useState('');
  const [kioskDistrict, setKioskDistrict] = useState('');
  const [kioskVillage, setKioskVillage] = useState('');
  const [kioskDistricts, setKioskDistricts] = useState([]);
  const [kioskVillages, setKioskVillages] = useState([]);
  const [imageFile, setImageFile] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [voiceUsed, setVoiceUsed] = useState(false);
  const [yoloOverlay, setYoloOverlay] = useState(null);
  const [schemeIncome, setSchemeIncome] = useState('');
  const [schemeOccupation, setSchemeOccupation] = useState('');
  const [schemeMatched, setSchemeMatched] = useState([]);
  const [citizenQuery, setCitizenQuery] = useState('');
  const [citizenChat, setCitizenChat] = useState([
    { sender: 'bot', text: 'Namaste! I am your Citizen AI Assistant. Ask me about local water projects, schools, government schemes, or how to track your suggestions.' }
  ]);

  // MP / Admin states
  const [budgetCr, setBudgetCr] = useState(10.0);
  const [weights, setWeights] = useState({ demand: 0.8, benefit: 0.9, urgency: 0.7, cost: 0.5, gap: 0.8 });
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [expandedRowIndex, setExpandedRowIndex] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [copilotQuery, setCopilotQuery] = useState('');
  const [copilotHistory, setCopilotHistory] = useState([
    { sender: 'bot', text: 'Constituency Digital Twin Advisor ready. Ask me how to invest your MPLADS budget, identify development gaps, or retrieve village priority indices.' }
  ]);
  const [queryingCopilot, setQueryingCopilot] = useState(false);
  const [copilotLogs, setCopilotLogs] = useState([]);
  const [activeVillageDetails, setActiveVillageDetails] = useState(null);
  const [reportsLogs, setReportsLogs] = useState(null);
  const [toast, setToast] = useState(null);
  const [newsFeed, setNewsFeed] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);

  useEffect(() => {
    if (!selectedState || !selectedDistrict || activeTab !== 'news') return;
    setLoadingNews(true);
    fetch(`/api/copilot/news?state=${selectedState}&district=${selectedDistrict}`)
      .then(r => r.json())
      .then(d => {
        if (d && d.news) {
          setNewsFeed(d.news);
        }
        setLoadingNews(false);
      })
      .catch(err => {
        console.error("Failed to fetch news:", err);
        setLoadingNews(false);
      });
  }, [selectedState, selectedDistrict, activeTab]);

  // Fetch Crawled Database Assets useEffect
  useEffect(() => {
    if (activeTab !== 'crawled_data') return;
    setLoadingCrawled(true);
    let url = '';
    const qParam = crawledDataSearch ? `&q=${encodeURIComponent(crawledDataSearch)}` : '';
    if (crawledDataType === 'schemes') {
      url = `/api/copilot/schemes?state=${encodeURIComponent(selectedState)}${crawledDataSearch ? `&q=${encodeURIComponent(crawledDataSearch)}` : ''}`;
    } else if (crawledDataType === 'news') {
      url = `/api/copilot/news?state=${encodeURIComponent(selectedState)}&district=${encodeURIComponent(selectedDistrict)}`;
    } else if (crawledDataType === 'tenders') {
      url = `/api/copilot/tenders?state=${encodeURIComponent(selectedState)}&district=${encodeURIComponent(selectedDistrict)}`;
    }
    
    fetch(url)
      .then(r => r.json())
      .then(data => {
        let items = [];
        if (crawledDataType === 'schemes') items = data.schemes || [];
        else if (crawledDataType === 'news') items = data.news || [];
        else if (crawledDataType === 'tenders') items = data.tenders || [];
        
        // Filter news/tenders locally if crawledDataSearch is present
        if (crawledDataSearch && crawledDataType !== 'schemes') {
          const q = crawledDataSearch.toLowerCase();
          items = items.filter(x => 
            (x.title || '').toLowerCase().includes(q) || 
            (x.summary || x.authority || '').toLowerCase().includes(q)
          );
        }

        setCrawledDataList(items);
        setLoadingCrawled(false);
      })
      .catch(err => {
        console.error("Failed to fetch crawled data:", err);
        setLoadingCrawled(false);
        setCrawledDataList([]);
      });
  }, [activeTab, crawledDataType, crawledDataSearch, selectedState, selectedDistrict]);

  // Officer states
  const [officerTasks] = useState([
    { id: 1, title: 'Verify Ramapura PHC site soil reports', status: 'Pending', date: '2026-07-06' },
    { id: 2, title: 'Submit pipeline construction photolog', status: 'In Progress', date: '2026-07-08' },
    { id: 3, title: 'Inspect newly laid road drainage system', status: 'Pending', date: '2026-07-10' }
  ]);
  const [officerInspections] = useState([
    { id: 101, project: 'Ramapura Water Pipeline', schedule: '2026-07-07 10:00 AM', status: 'Scheduled' },
    { id: 102, project: 'Kothimir Primary School Extension', schedule: '2026-07-09 02:30 PM', status: 'Scheduled' }
  ]);

  // Admin states
  const [adminFile, setAdminFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadLogs, setUploadLogs] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Refs
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const markersLayer = useRef(null);
  const d3Container = useRef(null);
  const recognitionRef = useRef(null);

  // ── Effects ────────────────────────────────────────────────────
  useEffect(() => {
    if (currentUser && selectedPortal) setActiveTab('home');
  }, [currentUser, selectedPortal]);

  useEffect(() => {
    const baseUri = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? window.location.origin
      : 'https://mp-mitra-backend-1071706665291.asia-south1.run.app';
    const wsUrl = baseUri.replace('http', 'ws') + '/ws/dashboard';
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_suggestion') {
          setToast({
            title: `New Suggestion: ${data.village}`,
            body: `${data.category}: ${data.ai_summary} (Priority: ${data.priority_score}/100)`,
            id: data.submission_id
          });
          // Play notification sound / pop
          confetti({ particleCount: 30, spread: 20 });
          // Auto clear toast after 8 seconds
          setTimeout(() => setToast(null), 8000);
        }
      } catch (e) {
        console.error('[Dashboard WS Error]', e);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (activeTab === 'kiosk') {
      setKioskState(selectedState || '');
      setKioskDistrict(selectedDistrict || '');
    }
  }, [activeTab, selectedState, selectedDistrict]);

  useEffect(() => {
    if (!kioskState) { setKioskDistricts([]); setKioskVillages([]); return; }
    // Instantly populate with local fallback districts from our JSON map
    const fd = fallbackDistrictsMap[kioskState.toUpperCase()] || [];
    setKioskDistricts(fd);
    
    // Attempt to fetch from API, if any exists
    fetch(`/api/constituency/districts?state=${kioskState}`)
      .then(r => r.json())
      .then(d => {
        if (d.districts && d.districts.length > 0) {
          setKioskDistricts(d.districts);
        }
      })
      .catch(() => {/* keep fallback */});
  }, [kioskState]);

  useEffect(() => {
    if (!kioskState || !kioskDistrict) { setKioskVillages([]); return; }
    fetch(`/api/constituency/villages?state=${kioskState}&district=${kioskDistrict}`)
      .then(r => r.json())
      .then(d => { setKioskVillages(d.villages); if (kioskDistrict !== selectedDistrict) setKioskVillage(''); })
      .catch(console.error);
  }, [kioskState, kioskDistrict]);

  useEffect(() => {
    const unsub = auth.onAuthStateChanged(async (user) => {
      if (user) {
        try {
          const snap = await getDoc(doc(db, 'users', user.uid));
          if (snap.exists()) {
            const p = snap.data();
            setCurrentUser(p);
            if (p.role === 'Citizen') setSelectedPortal('citizen');
            else if (p.role === 'MP') setSelectedPortal('official');
            else if (p.role === 'Officer') setSelectedPortal('officer');
            else if (p.role === 'Admin') setSelectedPortal('admin');
          } else {
            setCurrentUser({ uid: user.uid, email: user.email, displayName: user.displayName || user.email.split('@')[0], role: 'Citizen' });
            setSelectedPortal('citizen');
          }
        } catch (e) { console.error(e); }
      } else setCurrentUser(null);
      setAuthChecking(false);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    if (!selectedState || !selectedDistrict) return;
    const q = query(collection(db, 'complaints'), where('state_name', '==', selectedState.toUpperCase()), where('district_name', '==', selectedDistrict.toUpperCase()));
    return onSnapshot(q, snap => {
      // Find the centroid coordinates for the selected district as a fallback
      const stateKey = selectedState.toUpperCase();
      const distKey = selectedDistrict.toUpperCase();
      let baseLat = 19.0;
      let baseLng = 78.5;
      if (districtCoordsMap[stateKey] && districtCoordsMap[stateKey][distKey]) {
        baseLat = districtCoordsMap[stateKey][distKey][0];
        baseLng = districtCoordsMap[stateKey][distKey][1];
      }

      setFirestoreComplaints(snap.docs.map((d, index) => {
        const data = d.data();
        const ts = data.created_at;
        const date_str = ts?.toDate ? ts.toDate().toISOString().substring(0,16).replace('T',' ') : new Date().toISOString().substring(0,16).replace('T',' ');
        
        // Jitter coordinate slightly to avoid overlapping multiple complaints at the exact same centroid point
        const jitterLat = (Math.sin(index * 1.5) * 0.02);
        const jitterLng = (Math.cos(index * 1.5) * 0.02);
        
        // Overwrite default/empty coordinates with the selected district base coordinates
        let cLat = data.latitude;
        let cLng = data.longitude;
        if (!cLat || cLat === 19.0 || cLat === 0.0) {
          cLat = baseLat + jitterLat;
        }
        if (!cLng || cLng === 78.5 || cLng === 0.0) {
          cLng = baseLng + jitterLng;
        }

        return { id: d.id, text: data.text_content||'', category: data.category||'General', urgency: data.urgency||'Medium', lat: cLat, lng: cLng, status: data.status||'Pending', date: date_str, village: data.village_name||'' };
      }));
    }, err => console.warn(err));
  }, [selectedState, selectedDistrict]);

  useEffect(() => {
    if (!selectedState || !selectedDistrict) return;
    const q = query(collection(db, 'projects'), where('state_name', '==', selectedState.toUpperCase()), where('district_name', '==', selectedDistrict.toUpperCase()));
    return onSnapshot(q, snap => {
      setFirestoreProjects(snap.docs.map(d => ({ id: d.id, ...d.data() })));
    }, err => console.warn(err));
  }, [selectedState, selectedDistrict]);

  useEffect(() => {
    // Fetch live states from API; fallback list already loaded — just update if API responds
    fetch('/api/constituency/states')
      .then(r => r.json())
      .then(d => {
        if (d.states && d.states.length > 0) {
          setStates(d.states);
          if (!d.states.includes(selectedState)) {
            const next = d.states.includes('TELANGANA') ? 'TELANGANA' : d.states[0];
            setSelectedState(next);
          }
        }
      })
      .catch(() => {/* keep fallback */});
  }, []);

  useEffect(() => {
    if (!selectedState) return;
    // Instantly populate with local fallback districts from our JSON map
    const fd = fallbackDistrictsMap[selectedState.toUpperCase()] || [];
    setDistricts(fd);
    
    // Select first district automatically if the current selection is invalid for this state
    if (fd.length > 0 && !fd.includes(selectedDistrict)) {
      const firstDistrict = selectedState.toUpperCase() === 'TELANGANA' && fd.includes('ADILABAD')
        ? 'ADILABAD' : fd[0];
      setSelectedDistrict(firstDistrict);
    }
    
    fetch(`/api/constituency/districts?state=${selectedState}`)
      .then(r => r.json())
      .then(d => {
        if (d.districts && d.districts.length > 0) {
          setDistricts(d.districts);
          if (!d.districts.includes(selectedDistrict)) {
            const firstDistrict = selectedState.toUpperCase() === 'TELANGANA' && d.districts.includes('ADILABAD')
              ? 'ADILABAD' : d.districts[0];
            setSelectedDistrict(firstDistrict);
          }
        }
      })
      .catch(() => {/* keep fallback */});
  }, [selectedState]);

  useEffect(() => {
    if (!selectedState || !selectedDistrict) return;
    setLoading(true);
    fetch(`/api/constituency/data?state=${selectedState}&district=${selectedDistrict}`)
      .then(r => {
        if (!r.ok) throw new Error("API failed");
        return r.json();
      })
      .then(d => {
        if (!d || !d.metrics) throw new Error("Invalid metrics");
        setConstituencyData(d);
        setLoading(false);
      })
      .catch(() => {
        const mockD = generateMockConstituencyData(selectedState, selectedDistrict);
        setConstituencyData(mockD);
        setLoading(false);
      });
  }, [selectedState, selectedDistrict]);

  // Leaflet Map
  useEffect(() => {
    if (!['map','issues','overview'].includes(activeTab) || !mapContainer.current || !constituencyData) return;
    if (mapInstance.current) mapInstance.current.remove();
    const { schools, clinics } = constituencyData.map_points;
    const complaints = firestoreComplaints;
    let center = [19.0, 78.5];
    const all = [...schools,...clinics,...complaints];
    if (all.length) center = [all.reduce((a,p)=>a+p.lat,0)/all.length, all.reduce((a,p)=>a+p.lng,0)/all.length];
    mapInstance.current = L.map(mapContainer.current).setView(center, 10);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors' }).addTo(mapInstance.current);
    markersLayer.current = L.layerGroup().addTo(mapInstance.current);
    schools.forEach(s => L.marker([s.lat,s.lng],{icon:schoolIcon}).bindPopup(`<b style="color:#003B7A">${s.name}</b><br><small>PTR: ${s.teachers>0?(s.students/s.teachers).toFixed(1):0}:1</small>`).addTo(markersLayer.current));
    clinics.forEach(c => L.marker([c.lat,c.lng],{icon:clinicIcon}).bindPopup(`<b style="color:#138808">${c.name}</b><br><small>${c.type.toUpperCase()}</small>`).addTo(markersLayer.current));
    complaints.forEach(c => L.marker([c.lat,c.lng],{icon:complaintIcon}).bindPopup(`<b style="color:#C62B2B">Grievance</b><br><small>📍 ${c.village||'General Area'}</small><br><p style="font-size:12px;margin:4px 0 0">${c.text}</p>`).on('click',()=>setActiveVillageDetails({village:c.village||'Ramapura',population:5200+Math.floor(Math.random()*2000),schools:1+Math.floor(Math.random()*3),clinics:Math.random()>0.5?'1':'None',water_coverage:'18%',road:'Earthen / Potholes',complaints:146,news:'Pipeline Burst / Water Contamination',priority_score:'96/100',recs:['Build PHC','Repair Pipeline','Upgrade Road']})).addTo(markersLayer.current));
  }, [activeTab, constituencyData, firestoreComplaints]);

  // Speech Recognition
  const SPEECH_LANG_CODES = { English:'en-IN', Hindi:'hi-IN', Kannada:'kn-IN', Telugu:'te-IN', Tamil:'ta-IN', Malayalam:'ml-IN' };
  const handleRecordVoice = () => {
    if (recording) { if (recognitionRef.current) recognitionRef.current.stop(); setRecording(false); return; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Your browser does not support voice recording. Please type your complaint below.'); return; }
    const rec = new SR();
    recognitionRef.current = rec;
    rec.continuous = false; rec.interimResults = true;
    rec.lang = SPEECH_LANG_CODES[speechLanguage]||'en-IN';
    setRecording(true); setVoiceUsed(true); setComplaintText('');
    rec.onresult = e => {
      let interim = '', final = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += t; else interim += t;
      }
      setComplaintText(final || interim);
    };
    rec.onend = () => { setRecording(false); recognitionRef.current = null; };
    rec.onerror = e => { setRecording(false); recognitionRef.current = null; if (e.error==='not-allowed') alert('Microphone access denied. Please allow permission and try again.'); };
    rec.start();
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0]; if (!file) return;
    if (type === 'image') { setImageFile(file); setYoloOverlay('Analysing with YOLOv11...'); setTimeout(()=>setYoloOverlay({label:'Water Leakage',confidence:'94.2%'}),1500); }
    else setDocFile(file);
  };

  const submitGrievance = e => {
    e.preventDefault(); setSubmittingComplaint(true); setSubmissionResult(null); setSubmissionLogs([]);
    const fd = new FormData();
    fd.append('state', kioskState); fd.append('district', kioskDistrict); fd.append('village', kioskVillage); fd.append('text_content', complaintText);
    if (imageFile) fd.append('image_file', imageFile);
    if (docFile) fd.append('doc_file', docFile);
    if (voiceUsed) { fd.append('voice_file', new Blob(['voice-recorded'],{type:'audio/wav'}), 'voice.wav'); }
    fetch('/api/citizen/submit', { method:'POST', body:fd })
      .then(r=>r.json()).then(data => {
        setSubmissionResult(data); setSubmittingComplaint(false); setVoiceUsed(false);
        let i = 0;
        const iv = setInterval(() => { if (i < data.agent_logs.length) { setSubmissionLogs(p=>[...p,data.agent_logs[i]]); i++; } else { clearInterval(iv); fetch(`/api/constituency/data?state=${selectedState}&district=${selectedDistrict}`).then(r=>r.json()).then(d=>setConstituencyData(d)); } }, 800);
      }).catch(()=>setSubmittingComplaint(false));
  };

  const runOptimization = () => {
    setOptimizing(true); setOptimizationResult(null);
    fetch('/api/prioritize/optimize', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ state:selectedState, district:selectedDistrict, budget_cr:budgetCr, weight_demand:weights.demand, weight_benefit:weights.benefit, weight_urgency:weights.urgency, weight_cost:weights.cost, weight_gap:weights.gap }) })
      .then(r=>r.json()).then(data => { setOptimizationResult(data); setOptimizing(false); confetti({particleCount:100,spread:60,origin:{y:0.6}}); })
      .catch(()=>setOptimizing(false));
  };

  const askCopilot = e => {
    e.preventDefault(); if (!copilotQuery.trim()) return;
    const userMsg = { sender:'user', text:copilotQuery };
    setCopilotHistory(p=>[...p,userMsg]); setQueryingCopilot(true); setCopilotLogs([]);
    const q = copilotQuery; setCopilotQuery('');
    fetch('/api/copilot/query', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ state:selectedState, district:selectedDistrict, message:q }) })
      .then(r=>r.json()).then(data => {
        setQueryingCopilot(false);
        let i = 0;
        const iv = setInterval(() => { if (i < data.agent_logs.length) { setCopilotLogs(p=>[...p,data.agent_logs[i]]); i++; } else { clearInterval(iv); setCopilotHistory(p=>[...p,{sender:'bot',text:data.response,sources:data.sources}]); } }, 750);
      }).catch(()=>setQueryingCopilot(false));
  };

  const matchSchemes = e => {
    e.preventDefault();
    const income = parseFloat(schemeIncome); const results = [];
    if (income <= 250000) { results.push({name:'PM Kisan Samman Nidhi',desc:'₹6,000/year financial support for small landholders.',link:'pmkisan.gov.in'}); results.push({name:'PMAY-Gramin',desc:'Interest subsidy on housing loans for rural low-income families.',link:'pmayg.nic.in'}); }
    if (schemeOccupation.toLowerCase().includes('labor') || schemeOccupation.toLowerCase().includes('farmer') || income < 350000) results.push({name:'MGNREGA Scheme',desc:'Guarantees 100 days of unskilled wage employment per household.',link:'nrega.nic.in'});
    results.push({name:'Skill India Mission',desc:'Free vocational training programs and certifications.',link:'pmkvyofficial.org'});
    setSchemeMatched(results);
  };

  const handleCitizenQuery = e => {
    e.preventDefault(); if (!citizenQuery.trim()) return;
    const q = citizenQuery.toLowerCase();
    setCitizenChat(p=>[...p,{sender:'user',text:citizenQuery}]); setCitizenQuery('');
    setTimeout(() => {
      let ans = 'I could not find exact proximity matches. Would you like me to submit this suggestion to your local MP?';
      if (q.includes('hospital')||q.includes('clinic')) ans = 'The nearest Primary Health Centre (PHC) is 18 km away in Adilabad Centroid. Would you like to submit a development request to build a local PHC?';
      else if (q.includes('school')||q.includes('education')) ans = 'There are 2 secondary schools within 4 km. The Pupil-Teacher Ratio is 38:1 (NITI standard: 30:1). Would you like to request another teacher assignment?';
      else if (q.includes('water')) ans = 'Jal Jeevan Mission records show Ramapura water coverage is at 18%. Would you like to submit a suggestion to upgrade pipes?';
      setCitizenChat(p=>[...p,{sender:'bot',text:ans}]);
    }, 900);
  };

  const handleAdminUpload = e => {
    e.preventDefault(); if (!adminFile) return; setUploading(true); setUploadResult(null); setUploadLogs([]);
    const fd = new FormData(); fd.append('csv_file', adminFile);
    fetch('/api/admin/upload-dataset', { method:'POST', body:fd })
      .then(r=>r.json()).then(data => {
        setUploadResult(data); setUploading(false);
        let i = 0;
        const iv = setInterval(() => { if (i < data.pipeline_logs.length) { setUploadLogs(p=>[...p,data.pipeline_logs[i]]); i++; } else clearInterval(iv); }, 700);
      }).catch(()=>setUploading(false));
  };

  // ── Loading State ──────────────────────────────────────────
  if (authChecking) {
    return (
      <div style={{ minHeight:'100vh', background:'#F5F7FA', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:'16px', fontFamily:'Inter, sans-serif' }}>
        <div style={{ width:'48px', height:'48px', border:'3px solid #DDE1E7', borderTopColor:'#003B7A', borderRadius:'50%', animation:'spin 1s linear infinite' }} className="animate-spin" />
        <p style={{ color:'#6B6B6B', fontSize:'14px', fontWeight:500 }}>Validating secure government session...</p>
      </div>
    );
  }

  // ── Portal Selection Screen ────────────────────────────────
  if (!selectedPortal) {
    return (
      <div style={{ minHeight:'100vh', background:'#F5F7FA', fontFamily:'Inter, sans-serif' }}>
        {/* Header */}
        <header style={{ background:'#003B7A' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 40px', height:'64px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
              <div style={{ width:'40px', height:'40px', background:'white', borderRadius:'6px', display:'flex', alignItems:'center', justifyContent:'center' }}>
                <span style={{ fontSize:'20px' }}>🇮🇳</span>
              </div>
              <div>
                <div style={{ color:'white', fontWeight:800, fontSize:'18px', lineHeight:1 }}>MP MITRA</div>
                <div style={{ color:'rgba(255,255,255,0.65)', fontSize:'10px', textTransform:'uppercase', letterSpacing:'0.07em' }}>National AI Governance Intelligence Platform</div>
              </div>
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:'12px', fontSize:'12px', color:'rgba(255,255,255,0.7)' }}>
              <span>Government of India Initiative</span>
              <span>•</span>
              <span>Digital India Programme</span>
            </div>
          </div>
          <div style={{ display:'flex', height:'3px' }}>
            <div style={{ flex:1, background:'#FF6B1A' }} />
            <div style={{ flex:1, background:'white' }} />
            <div style={{ flex:1, background:'#138808' }} />
          </div>
        </header>

        {/* Hero Banner */}
        <div style={{ background:'linear-gradient(135deg, #002a5a 0%, #003B7A 60%, #004fa8 100%)', padding:'48px 40px', textAlign:'center' }}>
          <div style={{ display:'inline-flex', alignItems:'center', gap:'8px', background:'rgba(255,255,255,0.1)', border:'1px solid rgba(255,255,255,0.2)', borderRadius:'20px', padding:'4px 16px', marginBottom:'20px' }}>
            <span style={{ fontSize:'11px', fontWeight:700, color:'white', textTransform:'uppercase', letterSpacing:'0.08em' }}>AI-Powered • Evidence-Based • Citizen-First</span>
          </div>
          <h1 style={{ fontSize:'36px', fontWeight:800, color:'white', margin:'0 0 12px', fontFamily:'Space Grotesk, sans-serif', lineHeight:1.2 }}>MP Mitra: Constituency Intelligence Platform</h1>
          <p style={{ fontSize:'15px', color:'rgba(255,255,255,0.75)', maxWidth:'640px', margin:'0 auto 32px', lineHeight:1.7 }}>
            Bridging citizens with elected representatives through AI-powered suggestion processing, real-time infrastructure gap analysis, and transparent project tracking.
          </p>
          {/* Stats row */}
          <div style={{ display:'flex', justifyContent:'center', gap:'48px', flexWrap:'wrap' }}>
            {[['15,247', 'Suggestions Processed'],['1,24,000', 'Citizens Served'],['₹18.2 Cr', 'MPLADS Budget Tracked'],['94.6%', 'AI Accuracy Score']].map(([v,l]) => (
              <div key={l} style={{ textAlign:'center' }}>
                <div style={{ fontSize:'24px', fontWeight:800, color:'#FF6B1A', fontFamily:'Space Grotesk, sans-serif', lineHeight:1 }}>{v}</div>
                <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.6)', marginTop:'4px', fontWeight:500 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Portal Cards */}
        <div style={{ padding:'48px 40px', maxWidth:'1200px', margin:'0 auto' }}>
          <div style={{ textAlign:'center', marginBottom:'36px' }}>
            <h2 style={{ fontSize:'22px', fontWeight:700, color:'#1a1a1a', margin:'0 0 8px', fontFamily:'Space Grotesk, sans-serif' }}>Select Your Portal</h2>
            <p style={{ fontSize:'13px', color:'#6B6B6B', margin:0 }}>Please select the designated portal for your role to access your dashboard.</p>
          </div>

          <div className="gov-grid-4col" style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:'20px' }}>
            {/* Citizen */}
            <div onClick={() => setSelectedPortal('citizen')} className="gov-card gov-card--navy" style={{ padding:'28px', cursor:'pointer', transition:'all 0.2s' }} onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.boxShadow='0 8px 24px rgba(0,59,122,0.15)'}} onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow=''}}>
              <div style={{ width:'52px', height:'52px', background:'#EEF3FA', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'20px', fontSize:'24px' }}>👥</div>
              <h3 style={{ fontSize:'17px', fontWeight:700, color:'#003B7A', margin:'0 0 10px', fontFamily:'Space Grotesk, sans-serif' }}>Citizen Services</h3>
              <p style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.6, margin:'0 0 20px' }}>Submit voice/text/image grievances, track suggestion progress, and match government welfare schemes.</p>
              <div style={{ display:'flex', alignItems:'center', gap:'6px', color:'#003B7A', fontSize:'13px', fontWeight:700 }}>Access Portal <ChevronRight size={14} /></div>
            </div>

            {/* MP */}
            <div onClick={() => setSelectedPortal('official')} className="gov-card gov-card--saffron" style={{ padding:'28px', cursor:'pointer', transition:'all 0.2s' }} onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.boxShadow='0 8px 24px rgba(255,107,26,0.15)'}} onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow=''}}>
              <div style={{ width:'52px', height:'52px', background:'#FFF3EC', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'20px', fontSize:'24px' }}>🏛️</div>
              <h3 style={{ fontSize:'17px', fontWeight:700, color:'#FF6B1A', margin:'0 0 10px', fontFamily:'Space Grotesk, sans-serif' }}>MP Dashboard</h3>
              <p style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.6, margin:'0 0 20px' }}>View constituency digital twin, run budget optimizers, review GIS priority maps, and query AI advisors.</p>
              <div style={{ display:'flex', alignItems:'center', gap:'6px', color:'#FF6B1A', fontSize:'13px', fontWeight:700 }}>Access Portal <ChevronRight size={14} /></div>
            </div>

            {/* Officer */}
            <div onClick={() => setSelectedPortal('officer')} className="gov-card gov-card--green" style={{ padding:'28px', cursor:'pointer', transition:'all 0.2s' }} onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.boxShadow='0 8px 24px rgba(19,136,8,0.15)'}} onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow=''}}>
              <div style={{ width:'52px', height:'52px', background:'#EAF6EA', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'20px', fontSize:'24px' }}>⚙️</div>
              <h3 style={{ fontSize:'17px', fontWeight:700, color:'#138808', margin:'0 0 10px', fontFamily:'Space Grotesk, sans-serif' }}>Officer Portal</h3>
              <p style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.6, margin:'0 0 20px' }}>Update project checklists, log inspections, post field photos, and file construction completion logs.</p>
              <div style={{ display:'flex', alignItems:'center', gap:'6px', color:'#138808', fontSize:'13px', fontWeight:700 }}>Access Portal <ChevronRight size={14} /></div>
            </div>

            {/* Admin */}
            <div onClick={() => setSelectedPortal('admin')} className="gov-card gov-card--red" style={{ padding:'28px', cursor:'pointer', transition:'all 0.2s' }} onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.boxShadow='0 8px 24px rgba(198,43,43,0.15)'}} onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow=''}}>
              <div style={{ width:'52px', height:'52px', background:'#FDECEA', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'20px', fontSize:'24px' }}>🛡️</div>
              <h3 style={{ fontSize:'17px', fontWeight:700, color:'#C62B2B', margin:'0 0 10px', fontFamily:'Space Grotesk, sans-serif' }}>Admin Console</h3>
              <p style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.6, margin:'0 0 20px' }}>Ingest national dataset CSVs, monitor pipeline logs, track AI model health, and broadcast notices.</p>
              <div style={{ display:'flex', alignItems:'center', gap:'6px', color:'#C62B2B', fontSize:'13px', fontWeight:700 }}>Access Portal <ChevronRight size={14} /></div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="gov-footer" style={{ background:'#003B7A', padding:'24px 40px', marginTop:'20px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', maxWidth:'1200px', margin:'0 auto' }}>
            <div style={{ color:'rgba(255,255,255,0.6)', fontSize:'12px' }}>
              © 2026 MP Mitra — Government of India Initiative. All Rights Reserved.
            </div>
            <div style={{ display:'flex', gap:'24px' }}>
              {['Help & Support','Privacy Policy','Terms of Use','Contact Us'].map(l => (
                <span key={l} style={{ color:'rgba(255,255,255,0.6)', fontSize:'12px', cursor:'pointer' }}>{l}</span>
              ))}
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // ── Auth Gate ──────────────────────────────────────────────
  if (!currentUser) {
    return <AuthScreen portal={selectedPortal} onAuthSuccess={p=>setCurrentUser(p)} onBackToPortals={()=>setSelectedPortal(null)} />;
  }

  // ── CITIZEN PORTAL (Top-Nav Layout) ───────────────────────
  if (selectedPortal === 'citizen') {
    const navItems = [
      { id:'home', label:'Home', icon:Home },
      { id:'kiosk', label:'Submit Suggestion', icon:Volume2 },
      { id:'assistant', label:'AI Assistant', icon:Bot },
      { id:'issues', label:'Nearby Issues', icon:MapPin },
      { id:'track', label:'Track Status', icon:Clock },
      { id:'schemes', label:'Welfare Schemes', icon:Award },
    ];

    return (
      <div style={{ minHeight:'100vh', background:'#F5F7FA', fontFamily:'Inter, sans-serif' }}>
        <GovHeader portalLabel="Citizen Services Portal" portalColor="citizen" currentUser={currentUser} onExit={()=>{signOut(auth);setSelectedPortal(null);}} />

        {/* Top Navigation Bar */}
        <div className="gov-header-nav-row" style={{ background:'white', borderBottom:'1px solid #DDE1E7', padding:'0 32px', boxShadow:'0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ display:'flex', gap:'4px', overflowX:'auto' }}>
            {navItems.map(item => (
              <button key={item.id} onClick={()=>setActiveTab(item.id)} className={`gov-nav-tab ${activeTab===item.id?'active':''}`}>
                <item.icon size={15} />
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Page Banner */}
        {activeTab === 'home' && <GovPageBanner title={`Welcome, ${currentUser.displayName || 'Citizen'}!`} subtitle="Your gateway to local governance — submit suggestions, track progress, and access government welfare programmes." breadcrumbs={['Citizen Portal','Home']} />}
        {activeTab === 'kiosk' && <GovPageBanner title="Submit Development Suggestion" subtitle="Describe the public issue you wish to report. Select your location before describing the problem." breadcrumbs={['Citizen Portal','Submit Suggestion']} />}
        {activeTab === 'assistant' && <GovPageBanner title="Citizen AI Assistant" subtitle="Ask about local infrastructure, government schemes, or check service availability near you." breadcrumbs={['Citizen Portal','AI Assistant']} />}
        {activeTab === 'issues' && <GovPageBanner title="Nearby Issues Map" subtitle="View all active grievances and infrastructure points in your constituency." breadcrumbs={['Citizen Portal','Nearby Issues']} />}
        {activeTab === 'track' && <GovPageBanner title="Track Suggestion Status" subtitle="Monitor the resolution progress of your submitted suggestions." breadcrumbs={['Citizen Portal','Track Status']} />}
        {activeTab === 'schemes' && <GovPageBanner title="Government Welfare Schemes" subtitle="Find eligible schemes based on your income and occupation profile." breadcrumbs={['Citizen Portal','Welfare Schemes']} />}

        <main style={{ padding:'28px 32px', maxWidth:'1200px', margin:'0 auto' }}>

          {/* HOME TAB */}
          {activeTab === 'home' && (
            <div style={{ display:'grid', gap:'24px' }}>
              {/* Quick Action Cards */}
              <div className="gov-grid-3col" style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:'16px' }}>
                <StatCard label="My Active Suggestions" value="3" color="#003B7A" icon={Volume2} sub="1 AI verified, 2 under review" />
                <StatCard label="Nearby Active Grievances" value={firestoreComplaints.length || 0} color="#FF6B1A" icon={MapPin} sub="Filed in your constituency" />
                <StatCard label="Schemes You May Qualify" value="4" color="#138808" icon={Award} sub="Based on your profile" />
              </div>

              <div className="gov-grid-split" style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:'20px' }}>
                {/* Quick Actions */}
                <div className="gov-card" style={{ padding:'24px' }}>
                  <SectionHeader title="Quick Actions" subtitle="Common services for citizens" />
                  <div className="gov-grid-2col" style={{ display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:'12px' }}>
                    {[
                      {label:'Submit Voice Grievance', desc:'Record or type your issue', tab:'kiosk', color:'#003B7A', icon:'🎙️'},
                      {label:'Check Welfare Schemes', desc:'Find schemes you qualify for', tab:'schemes', color:'#138808', icon:'📋'},
                      {label:'View Nearby Issues', desc:'See active grievances on map', tab:'issues', color:'#FF6B1A', icon:'🗺️'},
                      {label:'Track My Suggestions', desc:'Follow up on submitted issues', tab:'track', color:'#C62B2B', icon:'📊'},
                    ].map(a => (
                      <button key={a.label} onClick={()=>setActiveTab(a.tab)} style={{ display:'flex', alignItems:'flex-start', gap:'12px', padding:'16px', background:'#F5F7FA', border:`1.5px solid ${a.color}20`, borderRadius:'8px', cursor:'pointer', transition:'all 0.2s', textAlign:'left' }} onMouseEnter={e=>{e.currentTarget.style.background=`${a.color}08`;e.currentTarget.style.borderColor=`${a.color}40`}} onMouseLeave={e=>{e.currentTarget.style.background='#F5F7FA';e.currentTarget.style.borderColor=`${a.color}20`}}>
                        <span style={{ fontSize:'24px', lineHeight:1 }}>{a.icon}</span>
                        <div>
                          <div style={{ fontSize:'13px', fontWeight:700, color:'#1a1a1a', marginBottom:'2px' }}>{a.label}</div>
                          <div style={{ fontSize:'11px', color:'#6B6B6B' }}>{a.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Announcements */}
                <div className="gov-card" style={{ padding:'24px' }}>
                  <SectionHeader title="Announcements" accent="#138808" />
                  <div style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
                    {[
                      {title:'Pipeline Works Complete', desc:'Mandya sector 4 pipeline laid and tested. Clean water supply now active.', date:'Today', color:'#138808'},
                      {title:'PHC Doctor Drive', desc:'Free medical checkup camp at Ramapura PHC on July 10.', date:'2 days ago', color:'#003B7A'},
                    ].map((a,i) => (
                      <div key={i} style={{ padding:'12px', background:'#F5F7FA', borderRadius:'8px', borderLeft:`3px solid ${a.color}` }}>
                        <div style={{ fontSize:'12px', fontWeight:700, color:'#1a1a1a', marginBottom:'4px' }}>{a.title}</div>
                        <div style={{ fontSize:'11px', color:'#6B6B6B', lineHeight:1.5 }}>{a.desc}</div>
                        <div style={{ fontSize:'10px', color:'#999', marginTop:'6px' }}>{a.date}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SUBMIT SUGGESTION TAB */}
          {activeTab === 'kiosk' && (
            <div className="gov-grid-2col" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'24px' }}>
              <div className="gov-card" style={{ padding:'28px' }}>
                <SectionHeader title="Step 1: Select Your Location" subtitle="Choose state, district, and your village / habitation" />
                <div className="gov-grid-2col" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px', marginBottom:'12px' }}>
                  <div>
                    <label className="gov-label">State</label>
                    <select value={kioskState} onChange={e=>{ setKioskState(e.target.value); setKioskDistrict(''); setKioskVillage(''); }} className="gov-input">
                      <option value="">— Select State —</option>
                      {states.map(s=><option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="gov-label">District</label>
                    <select
                      value={kioskDistrict}
                      onChange={e=>{ setKioskDistrict(e.target.value); setKioskVillage(''); }}
                      disabled={!kioskState}
                      className="gov-input"
                    >
                      <option value="">— Select District —</option>
                      {/* Use loaded fallback districts when same state, else fetch result */}
                      {(kioskState === selectedState ? districts : kioskDistricts).map(d=>
                        <option key={d} value={d}>{d}</option>
                      )}
                    </select>
                  </div>
                </div>
                <div style={{ marginBottom:'20px' }}>
                  <label className="gov-label">Village / Habitation / Town</label>
                  <input
                    type="text"
                    value={kioskVillage}
                    onChange={e=>setKioskVillage(e.target.value)}
                    disabled={!kioskDistrict}
                    placeholder={kioskDistrict ? `e.g. Ramapura, Kothimir, Mandya...` : 'Select district first'}
                    className="gov-input"
                    style={{ marginTop:'2px' }}
                    list="kiosk-villages-list"
                  />
                  <datalist id="kiosk-villages-list">
                    {kioskVillages.map(v => (
                      <option key={v} value={v} />
                    ))}
                  </datalist>
                  {kioskDistrict && kioskVillage && (
                    <div style={{ marginTop: '6px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {kioskVillages.some(v => v.toUpperCase() === kioskVillage.toUpperCase()) ? (
                        <span style={{ color: '#138808', fontWeight: 600 }}>✅ Census Verified Village</span>
                      ) : (
                        <span style={{ color: '#FF6B1A', fontWeight: 600 }}>
                          ⚠️ Warning: Not found in Census records. Please verify spelling.
                        </span>
                      )}
                    </div>
                  )}
                  {kioskDistrict && !kioskVillage && (
                    <p style={{ fontSize:'11px', color:'#FF6B1A', margin:'4px 0 0', fontWeight:500 }}>⚠️ Type your village or habitation name to continue</p>
                  )}
                </div>

                {!kioskVillage ? (
                  <div style={{ padding:'32px', background:'#F5F7FA', borderRadius:'8px', textAlign:'center', border:'1.5px dashed #DDE1E7' }}>
                    <div style={{ fontSize:'32px', marginBottom:'10px' }}>📍</div>
                    <p style={{ fontSize:'13px', color:'#6B6B6B', margin:0 }}>Please select your location above to proceed with the suggestion.</p>
                  </div>
                ) : (
                  <form onSubmit={submitGrievance}>
                    <SectionHeader title="Step 2: Describe the Problem" subtitle="Use voice, text, image, or document" />

                    {/* Voice + Language */}
                    <div style={{ display:'flex', gap:'8px', marginBottom:'12px' }}>
                      <button type="button" onClick={handleRecordVoice} style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center', gap:'8px', padding:'10px 16px', background: recording ? '#FDECEA' : '#EEF3FA', border: `1.5px solid ${recording ? '#C62B2B' : '#003B7A'}`, borderRadius:'6px', color: recording ? '#C62B2B' : '#003B7A', fontSize:'13px', fontWeight:700, cursor:'pointer' }}>
                        <Volume2 size={15} /> {recording ? '⏹ Stop Recording' : '🎙 Record Voice'}
                      </button>
                      <select value={speechLanguage} onChange={e=>setSpeechLanguage(e.target.value)} className="gov-input" style={{ width:'auto', minWidth:'140px' }}>
                        <option value="English">English</option>
                        <option value="Hindi">Hindi (हिंदी)</option>
                        <option value="Kannada">Kannada (ಕನ್ನಡ)</option>
                        <option value="Telugu">Telugu (తెలుగు)</option>
                        <option value="Tamil">Tamil (தமிழ்)</option>
                        <option value="Malayalam">Malayalam (മലയാളം)</option>
                      </select>
                    </div>

                    <textarea rows={4} value={complaintText} onChange={e=>setComplaintText(e.target.value)} placeholder="Describe the problem in your language..." className="gov-input" style={{ resize:'vertical', marginBottom:'12px', lineHeight:1.6 }} />

                    {/* File uploads */}
                    <div className="gov-grid-2col" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'8px', marginBottom:'12px' }}>
                      <label style={{ display:'flex', alignItems:'center', gap:'8px', padding:'10px 14px', background:'#F5F7FA', border:'1.5px dashed #DDE1E7', borderRadius:'6px', cursor:'pointer', fontSize:'12px', color:'#6B6B6B', fontWeight:500 }}>
                        <Camera size={15} color="#003B7A" /> {imageFile ? imageFile.name : 'Upload Photo'}
                        <input type="file" accept="image/*" onChange={e=>handleFileChange(e,'image')} style={{ display:'none' }} />
                      </label>
                      <label style={{ display:'flex', alignItems:'center', gap:'8px', padding:'10px 14px', background:'#F5F7FA', border:'1.5px dashed #DDE1E7', borderRadius:'6px', cursor:'pointer', fontSize:'12px', color:'#6B6B6B', fontWeight:500 }}>
                        <FileText size={15} color="#003B7A" /> {docFile ? docFile.name : 'Upload PDF / Doc'}
                        <input type="file" accept=".pdf,.doc,.docx" onChange={e=>handleFileChange(e,'doc')} style={{ display:'none' }} />
                      </label>
                    </div>

                    {yoloOverlay && (
                      <div style={{ padding:'10px 14px', background:'#EAF6EA', border:'1px solid #138808', borderRadius:'6px', fontSize:'12px', color:'#138808', marginBottom:'12px', fontWeight:600 }}>
                        🤖 AI Detection: {typeof yoloOverlay === 'string' ? yoloOverlay : `${yoloOverlay.label} (${yoloOverlay.confidence})`}
                      </div>
                    )}

                    <button type="submit" disabled={submittingComplaint || !complaintText} className="gov-btn gov-btn--primary" style={{ width:'100%', padding:'12px', fontSize:'14px', opacity: (submittingComplaint||!complaintText) ? 0.5 : 1 }}>
                      {submittingComplaint ? '⏳ Processing Submission...' : 'Submit Grievance →'}
                    </button>
                  </form>
                )}
              </div>

              {/* AI Pipeline Logs */}
              <div className="gov-card" style={{ padding:'28px', display:'flex', flexDirection:'column' }}>
                <SectionHeader title="AI Agent Ingestion Pipeline" subtitle="Real-time processing logs" accent="#003B7A" />
                <div className="gov-log-panel" style={{ flex:1, minHeight:'340px' }}>
                  {submissionLogs.length === 0 && !submittingComplaint && (
                    <div style={{ color:'#555', fontStyle:'italic' }}>Submit a suggestion to view the AI pipeline execution logs...</div>
                  )}
                  {submissionLogs.map((log,i) => <div key={i} className="gov-log-panel__entry">{log}</div>)}
                  {submissionResult && submissionLogs.length === submissionResult.agent_logs.length && (
                    <div style={{ marginTop:'16px', padding:'14px', background:'#EAF6EA', border:'1px solid #138808', borderRadius:'6px' }}>
                      <div style={{ color:'#138808', fontFamily:'Inter,sans-serif', fontWeight:700, marginBottom:'8px' }}>✅ Suggestion Registered Successfully</div>
                      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'6px', fontFamily:'Inter,sans-serif', fontSize:'11px', color:'#3A3A3A' }}>
                        <div>ID: <strong>#{submissionResult.complaint_id}</strong></div>
                        <div>Language: <strong>{submissionResult.language_detected}</strong></div>
                        <div>Category: <strong>{submissionResult.category}</strong></div>
                        <div>Priority: <strong style={{ color:'#C62B2B' }}>{submissionResult.urgency}</strong></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* AI ASSISTANT TAB */}
          {activeTab === 'assistant' && (
            <div style={{ maxWidth:'800px', margin:'0 auto' }}>
              <div className="gov-card" style={{ display:'flex', flexDirection:'column', height:'520px', overflow:'hidden' }}>
                {/* Chat header */}
                <div style={{ padding:'16px 20px', background:'#003B7A', display:'flex', alignItems:'center', gap:'12px' }}>
                  <div style={{ width:'36px', height:'36px', background:'rgba(255,255,255,0.15)', borderRadius:'8px', display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <Bot size={20} color="white" />
                  </div>
                  <div>
                    <div style={{ fontWeight:700, color:'white', fontSize:'14px', lineHeight:1 }}>Citizen AI Copilot</div>
                    <div style={{ fontSize:'10px', color:'rgba(255,255,255,0.65)', marginTop:'2px', textTransform:'uppercase', letterSpacing:'0.06em' }}>Proximity & Scheme Resolver</div>
                  </div>
                  <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:'6px' }}>
                    <div style={{ width:'8px', height:'8px', background:'#4ade80', borderRadius:'50%' }} />
                    <span style={{ fontSize:'11px', color:'rgba(255,255,255,0.65)' }}>Online</span>
                  </div>
                </div>

                {/* Messages */}
                <div style={{ flex:1, overflowY:'auto', padding:'20px', display:'flex', flexDirection:'column', gap:'16px' }}>
                  {citizenChat.map((msg,i) => (
                    <div key={i} style={{ display:'flex', gap:'10px', flexDirection: msg.sender==='user'?'row-reverse':'row', maxWidth:'80%', alignSelf: msg.sender==='user'?'flex-end':'flex-start' }}>
                      <div style={{ width:'30px', height:'30px', borderRadius:'8px', background: msg.sender==='user'?'#003B7A':'#EEF3FA', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                        <span style={{ fontSize:'14px' }}>{msg.sender==='user'?'👤':'🤖'}</span>
                      </div>
                      <div style={{ padding:'12px 16px', borderRadius:'10px', background: msg.sender==='user'?'#EEF3FA':'white', border:'1px solid #DDE1E7', fontSize:'13px', color:'#1a1a1a', lineHeight:1.6, boxShadow:'0 1px 3px rgba(0,0,0,0.05)' }}>
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Input */}
                <form onSubmit={handleCitizenQuery} style={{ padding:'16px 20px', borderTop:'1px solid #DDE1E7', display:'flex', gap:'8px' }}>
                  <input type="text" value={citizenQuery} onChange={e=>setCitizenQuery(e.target.value)} placeholder="Ask: 'Is there a hospital nearby?' or 'Water problem in my area'" className="gov-input" style={{ flex:1 }} />
                  <button type="submit" className="gov-btn gov-btn--primary" style={{ padding:'10px 18px' }}><ArrowRight size={16} /></button>
                </form>
              </div>
            </div>
          )}

          {/* NEARBY ISSUES MAP TAB */}
          {activeTab === 'issues' && (
            <div className="gov-card" style={{ padding:'0', overflow:'hidden', height:'560px' }}>
              <div ref={mapContainer} style={{ width:'100%', height:'100%' }} />
            </div>
          )}

          {/* TRACK STATUS TAB */}
          {activeTab === 'track' && (
            <div style={{ maxWidth:'680px', margin:'0 auto' }}>
              <div className="gov-card" style={{ padding:'28px' }}>
                <SectionHeader title="Suggestion #701 — Pipeline Leakage Repair" subtitle="Filed: 2026-07-04 | Location: Ramapura, Adilabad" />
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'12px', marginBottom:'28px' }}>
                  <StatCard label="Status" value="Under Review" color="#FF6B1A" />
                  <StatCard label="Priority" value="High" color="#C62B2B" />
                  <StatCard label="Category" value="Water Supply" color="#003B7A" />
                </div>

                <div style={{ position:'relative', paddingLeft:'28px', borderLeft:'2px solid #DDE1E7' }}>
                  {[
                    {step:'Submitted', desc:'Grievance submitted by citizen with GPS location tag.', done:true, date:'Jul 4'},
                    {step:'AI Verified', desc:'Speech processed and TF-IDF duplicate analysis complete.', done:true, date:'Jul 4'},
                    {step:'Under Review', desc:'Referred to constituency planning group for assessment.', done:true, date:'Jul 5'},
                    {step:'Approved', desc:'Pending MP approval. Awaiting project assignment.', done:false, date:'–'},
                    {step:'Work Started', desc:'Officer assignment and materials dispatch pending.', done:false, date:'–'},
                    {step:'Completed', desc:'Site inspection, quality certification, and case closure.', done:false, date:'–'},
                  ].map((s,i) => (
                    <div key={i} style={{ position:'relative', marginBottom:'24px', paddingBottom:'4px' }}>
                      <div style={{ position:'absolute', left:'-37px', width:'18px', height:'18px', borderRadius:'50%', background: s.done ? '#003B7A' : 'white', border:`2px solid ${s.done?'#003B7A':'#DDE1E7'}`, display:'flex', alignItems:'center', justifyContent:'center' }}>
                        {s.done && <span style={{ color:'white', fontSize:'10px', fontWeight:700 }}>✓</span>}
                      </div>
                      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
                        <div>
                          <div style={{ fontSize:'14px', fontWeight:700, color: s.done?'#003B7A':'#999', marginBottom:'3px' }}>{s.step}</div>
                          <div style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.5 }}>{s.desc}</div>
                        </div>
                        <span style={{ fontSize:'11px', color:'#999', fontWeight:500, marginLeft:'12px', flexShrink:0 }}>{s.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* WELFARE SCHEMES TAB */}
          {activeTab === 'schemes' && (
            <div className="gov-grid-split" style={{ display:'grid', gridTemplateColumns:'340px 1fr', gap:'24px' }}>
              <div className="gov-card" style={{ padding:'24px' }}>
                <SectionHeader title="Eligibility Check" subtitle="Enter your profile to match schemes" />
                <form onSubmit={matchSchemes} style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
                  <div>
                    <label className="gov-label">Annual Income (₹)</label>
                    <input type="number" required value={schemeIncome} onChange={e=>setSchemeIncome(e.target.value)} placeholder="e.g. 1,50,000" className="gov-input" />
                  </div>
                  <div>
                    <label className="gov-label">Occupation</label>
                    <input type="text" required value={schemeOccupation} onChange={e=>setSchemeOccupation(e.target.value)} placeholder="e.g. Farmer / Labour / Student" className="gov-input" />
                  </div>
                  <button type="submit" className="gov-btn gov-btn--primary" style={{ width:'100%', padding:'12px' }}>Find Matching Schemes</button>
                </form>
              </div>

              <div className="gov-card" style={{ padding:'24px', display:'flex', flexDirection:'column' }}>
                <SectionHeader title="Available Government Schemes" accent="#138808" />
                <div style={{ flex:1, overflowY:'auto', display:'flex', flexDirection:'column', gap:'12px' }}>
                  {schemeMatched.length === 0 ? (
                    <div style={{ textAlign:'center', padding:'40px 20px', color:'#6B6B6B' }}>
                      <div style={{ fontSize:'36px', marginBottom:'12px' }}>🏛️</div>
                      <p style={{ fontSize:'13px', margin:0 }}>Enter your profile on the left panel to discover welfare schemes you may be eligible for.</p>
                    </div>
                  ) : schemeMatched.map((s,i) => (
                    <div key={i} className="gov-card gov-card--green" style={{ padding:'16px', display:'flex', justifyContent:'space-between', alignItems:'center', gap:'16px' }}>
                      <div>
                        <div style={{ fontSize:'14px', fontWeight:700, color:'#1a1a1a', marginBottom:'4px' }}>{s.name}</div>
                        <div style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.5 }}>{s.desc}</div>
                      </div>
                      <a href={`https://${s.link}`} target="_blank" rel="noopener noreferrer" className="gov-btn gov-btn--green" style={{ padding:'8px 14px', fontSize:'11px', flexShrink:0, textDecoration:'none' }}>
                        Apply →
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </main>

        {/* Footer */}
        <footer style={{ background:'#003B7A', padding:'20px 32px', marginTop:'40px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
            <div style={{ color:'rgba(255,255,255,0.6)', fontSize:'11px' }}>© 2026 MP Mitra — Government of India Initiative</div>
            <div style={{ display:'flex', gap:'20px' }}>
              {['Help','Privacy Policy','Contact'].map(l=><span key={l} style={{ color:'rgba(255,255,255,0.6)', fontSize:'11px', cursor:'pointer' }}>{l}</span>)}
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // ── ADMIN / MP / OFFICER SHARED SIDEBAR LAYOUT ────────────
  const isMp = selectedPortal === 'official';
  const isOfficer = selectedPortal === 'officer';
  const isAdmin = selectedPortal === 'admin';

  const sidebarColor = isMp ? '#FF6B1A' : isOfficer ? '#138808' : '#C62B2B';
  const sidebarBg = isMp ? '#FFF3EC' : isOfficer ? '#EAF6EA' : '#FDECEA';
  const portalName = isMp ? 'MP Dashboard' : isOfficer ? 'Officer Portal' : 'Admin Console';

  const mpNav = [
    {id:'home', label:'Dashboard Home', icon:LayoutDashboard},
    {id:'digital_twin', label:'Constituency Digital Twin', icon:Map},
    {id:'research_engine', label:'AI Research Engine', icon:Globe},
    {id:'function_level', label:'Function Level', icon:SlidersHorizontal},
    {id:'search_projects', label:'Village Census & Quality', icon:Search},
    {id:'map', label:'AI Priority Map', icon:MapPin},
    {id:'recommendations', label:'AI Recommendations', icon:Sparkles},
    {id:'gaps', label:'Infrastructure Gaps', icon:Activity},
    {id:'chat', label:'AI Advisor Chat', icon:Bot},
    {id:'optimizer', label:'Budget Optimizer', icon:SlidersHorizontal},
    {id:'tracking', label:'Project Tracking', icon:Briefcase},
    {id:'news', label:'News Intelligence', icon:Globe},
    {id:'crawled_data', label:'Web Scraper Database', icon:Database},
    {id:'reports', label:'Reports & Exports', icon:FileDown},
  ];
  const officerNav = [
    {id:'home', label:'Assigned Projects', icon:LayoutDashboard},
    {id:'inspections', label:'Inspection Schedule', icon:Calendar},
    {id:'tasks', label:'Pending Tasks', icon:ListTodo},
    {id:'photos', label:'Field Uploads', icon:Camera},
  ];
  const adminNav = [
    {id:'admin', label:'Dataset Ingestion', icon:Upload},
    {id:'scraper', label:'AI Web Scraper', icon:Globe},
    {id:'users', label:'User Access Control', icon:Users},
    {id:'models', label:'AI Models Health', icon:Activity},
    {id:'audit', label:'Audit System Logs', icon:Database},
  ];
  const currentNav = isMp ? mpNav : isOfficer ? officerNav : adminNav;

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#F5F7FA', fontFamily:'Inter, sans-serif' }}>
      <GovHeader portalLabel={portalName} portalColor={selectedPortal} currentUser={currentUser} onExit={()=>{signOut(auth);setSelectedPortal(null);}} />

      <div className="gov-portal-layout" style={{ display:'flex', flex:1, overflow:'hidden' }}>

        {/* ── Sidebar ── */}
        <aside className="gov-sidebar" style={{ width:'240px', background:'white', borderRight:'1px solid #DDE1E7', display:'flex', flexDirection:'column', flexShrink:0, overflowY:'auto' }}>
          {/* Portal badge */}
          <div style={{ padding:'16px', borderBottom:'1px solid #DDE1E7', background: sidebarBg }}>
            <div style={{ fontSize:'11px', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.06em', color: sidebarColor, marginBottom:'2px' }}>{portalName}</div>
            {isMp && (
              <div style={{ marginTop:'10px' }}>
                {mpConstituencyLocked ? (
                  // LOCKED VIEW — shows current selection with edit button
                  <div style={{ background:'white', border:'1px solid #FDDCCA', borderRadius:'8px', padding:'10px 12px' }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'6px' }}>
                      <span style={{ fontSize:'10px', fontWeight:700, textTransform:'uppercase', color:'#FF6B1A', letterSpacing:'0.05em' }}>📍 My Constituency</span>
                      <button onClick={()=>setMpConstituencyLocked(false)} style={{ background:'none', border:'none', cursor:'pointer', fontSize:'10px', color:'#003B7A', fontWeight:700, padding:'2px 6px', borderRadius:'4px', background:'#EEF3FA' }}>✏️ Edit</button>
                    </div>
                    <div style={{ fontSize:'13px', fontWeight:800, color:'#1a1a1a', lineHeight:1.2 }}>{selectedDistrict}</div>
                    <div style={{ fontSize:'11px', color:'#6B6B6B', marginTop:'2px' }}>{selectedState}</div>
                  </div>
                ) : (
                  // EDIT MODE — shows dropdowns with a lock/save button
                  <div style={{ display:'flex', flexDirection:'column', gap:'6px' }}>
                    <div style={{ fontSize:'10px', fontWeight:700, textTransform:'uppercase', color:'#FF6B1A', letterSpacing:'0.05em', marginBottom:'2px' }}>Select Constituency</div>
                    <select value={selectedState} onChange={e=>handleStateChange(e.target.value)} className="gov-input" style={{ fontSize:'12px', padding:'7px 10px' }}>
                      {states.map(s=><option key={s} value={s}>{s}</option>)}
                    </select>
                    <select value={selectedDistrict} onChange={e=>handleDistrictChange(e.target.value)} className="gov-input" style={{ fontSize:'12px', padding:'7px 10px' }}>
                      {districts.length > 0
                        ? districts.map(d=><option key={d} value={d}>{d}</option>)
                        : <option value={selectedDistrict}>{selectedDistrict}</option>
                      }
                    </select>
                    <button onClick={()=>setMpConstituencyLocked(true)} style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:'6px', padding:'8px', background:'#FF6B1A', color:'white', border:'none', borderRadius:'6px', fontSize:'12px', fontWeight:700, cursor:'pointer' }}>🔒 Lock &amp; Save</button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Nav items */}
          <nav className="gov-sidebar-nav" style={{ padding:'8px', flex:1 }}>
            {currentNav.map(item => {
              const activeClass = activeTab === item.id ? (isMp ? 'active-saffron' : isOfficer ? 'active-green' : 'active') : '';
              return (
                <button key={item.id} onClick={()=>setActiveTab(item.id)} className={`gov-sidebar-item ${activeClass}`}>
                  <item.icon size={15} style={{ flexShrink:0 }} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status indicator */}
          <div className="gov-sidebar-status" style={{ padding:'12px 16px', borderTop:'1px solid #DDE1E7' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'6px', fontSize:'11px', color:'#6B6B6B' }}>
              <div style={{ width:'6px', height:'6px', background:'#138808', borderRadius:'50%' }} />
              Server Online
              {loading && <RefreshCw size={11} style={{ marginLeft:'auto', animation:'spin 1s linear infinite', color:'#003B7A' }} className="animate-spin" />}
            </div>
          </div>
        </aside>

        {/* ── Main Content ── */}
        <main style={{ flex:1, overflowY:'auto', display:'flex', flexDirection:'column' }}>

          {/* ────── MP PORTAL TABS ────── */}
          {isMp && (
            <>
              {activeTab === 'home' && (() => {
                // Calculate dynamic metrics based on real database/Firestore state
                const ptrDeficitCount = constituencyData?.map_points?.schools?.filter(s => s.teachers > 0 && (s.students / s.teachers) > 30).length || 0;
                const clinicDeficitCount = (constituencyData?.metrics?.healthcare?.count || 0) < 6 ? 1 : 0;
                const waterDeficitCount = ((constituencyData?.metrics?.water?.total_habitations || 0) - (constituencyData?.metrics?.water?.fully_covered || 0)) || 0;
                const roadDeficitCount = ((constituencyData?.metrics?.roads?.count || 0) - (constituencyData?.metrics?.roads?.completed || 0)) || 0;
                const totalDeficits = ptrDeficitCount + clinicDeficitCount + (waterDeficitCount > 0 ? 1 : 0) + (roadDeficitCount > 0 ? 1 : 0);

                const whatsappCount = firestoreComplaints.filter(c => c.whatsapp_sim).length;
                const webCount = firestoreComplaints.filter(c => !c.whatsapp_sim).length;

                const criticalAlerts = firestoreComplaints.filter(c => c.urgency?.toLowerCase() === 'high' || c.urgency?.toLowerCase() === 'critical');
                const waterQualityIssues = constituencyData?.metrics?.water?.quality_records || 0;
                const totalRiskAlerts = criticalAlerts.length + waterQualityIssues;

                // Most demanded categories calculation
                const categoryStats = {};
                firestoreComplaints.forEach(c => {
                  const cat = c.category || 'General Development';
                  categoryStats[cat] = (categoryStats[cat] || 0) + 1;
                });
                const sortedCategories = Object.entries(categoryStats)
                  .sort((a,b) => b[1] - a[1]);

                return (
                  <>
                    <GovPageBanner title="Constituency Digital Twin Dashboard" subtitle={`Active Area: ${selectedDistrict}, ${selectedState} — AI-integrated intelligence summary`} breadcrumbs={['MP Dashboard','Home']} />
                    <div style={{ padding:'24px 28px', display:'grid', gap:'20px' }}>
                      <div className="gov-stat-grid" style={{ display:'grid', gridTemplateColumns:'repeat(5, 1fr)', gap:'14px' }}>
                        <StatCard label="Health Score" value={`${constituencyData?.health_score||82}/100`} color="#003B7A" icon={Activity} />
                        <StatCard label="AI Deficits Today" value={`${totalDeficits} Deficits`} color="#FF6B1A" icon={Sparkles} sub={totalDeficits > 0 ? `${ptrDeficitCount} School / ${clinicDeficitCount} Clinic gaps` : "All sectors optimal"} />
                        <StatCard label="Citizen Suggestions" value={firestoreComplaints.length.toLocaleString()} color="#138808" icon={Users} sub={`💬 ${whatsappCount} WhatsApp / 💻 ${webCount} Web`} />
                        <StatCard label="Completed Projects" value={constituencyData?.metrics?.roads?.completed || 0} color="#003B7A" icon={CheckCircle2} sub={`Out of ${constituencyData?.metrics?.roads?.count || 0} Road Projects`} />
                        <StatCard label="Risk Alerts" value={`${totalRiskAlerts} Active`} color="#C62B2B" icon={AlertCircle} sub={totalRiskAlerts > 0 ? `${criticalAlerts.length} High Urgency / ${waterQualityIssues} Water Gaps` : "No active warnings"} />
                      </div>

                      <div className="gov-grid-split" style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:'20px' }}>
                        <div style={{ display:'flex', flexDirection:'column', gap:'20px' }}>
                          {/* Ask AI */}
                          <div className="gov-card" style={{ padding:'24px' }}>
                            <SectionHeader title="Ask AI Decision Advisor" subtitle="Get evidence-based investment recommendations" />
                            <form onSubmit={askCopilot} style={{ display:'flex', gap:'8px' }}>
                              <input type="text" value={copilotQuery} onChange={e=>setCopilotQuery(e.target.value)} placeholder="e.g. Which ₹5 crore investment benefits most citizens?" className="gov-input" style={{ flex:1 }} />
                              <button type="submit" className="gov-btn gov-btn--saffron"><Bot size={15} /> Ask AI</button>
                            </form>
                            {copilotHistory.slice(-1).map((m,i)=>(
                              m.sender==='bot' && m !== copilotHistory[0] && (
                                <div key={i} style={{ marginTop:'14px', padding:'14px', background:'#F5F7FA', borderRadius:'8px', fontSize:'13px', color:'#1a1a1a', lineHeight:1.6, borderLeft:'3px solid #FF6B1A' }}>{m.text}</div>
                              )
                            ))}
                          </div>

                          {/* Live Citizen Suggestions Feed */}
                          <div className="gov-card" style={{ padding:'24px', display:'flex', flexDirection:'column', gap:'12px' }}>
                            <SectionHeader title="📥 Live Citizen Suggestions & Grievance Feed" subtitle="Real-time incoming requests from WhatsApp and Web Kiosk channels" />
                            
                            {firestoreComplaints.length === 0 ? (
                              <div style={{ textAlign:'center', padding:'30px', color:'#6B6B6B', fontSize:'13px' }}>
                                📭 No active suggestions filed in {selectedDistrict} yet. Use the WhatsApp Simulator to send a message!
                              </div>
                            ) : (
                              <div style={{ display:'flex', flexDirection:'column', gap:'12px', maxHeight:'400px', overflowY:'auto', paddingRight:'4px' }}>
                                {firestoreComplaints.map((c, i) => (
                                  <div key={c.id || i} style={{ padding:'14px', background:'#F8FAFC', border:'1px solid #E2E8F0', borderRadius:'8px', position:'relative' }}>
                                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                                      <span style={{ fontSize:'10px', fontWeight:700, padding:'3px 8px', borderRadius:'12px', background: c.whatsapp_sim ? '#E2F7E3' : '#E2EEFC', color: c.whatsapp_sim ? '#138808' : '#003B7A', textTransform:'uppercase' }}>
                                        {c.whatsapp_sim ? '💬 WhatsApp Suggestion' : '💻 Web Kiosk'}
                                      </span>
                                      <span style={{ fontSize:'10px', color:'#999' }}>{c.date || 'Recent'}</span>
                                    </div>
                                    <p style={{ fontSize:'12.5px', color:'#1a1a1a', fontWeight:500, margin:'0 0 10px 0', lineHeight:1.5 }}>"{c.text}"</p>
                                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', borderTop:'1px solid #EDF2F7', paddingTop:'8px', fontSize:'11px', color:'#6B6B6B' }}>
                                      <span>📍 Village: <strong style={{ color:'#1a1a1a' }}>{c.village || 'General Area'}</strong></span>
                                      <span>Category: <strong style={{ color:'#1a1a1a' }}>{c.category}</strong></span>
                                      <span className="gov-badge" style={{ background: c.urgency?.toLowerCase() === 'high' || c.urgency?.toLowerCase() === 'critical' ? '#FFF5F5' : '#F7FAFC', color: c.urgency?.toLowerCase() === 'high' || c.urgency?.toLowerCase() === 'critical' ? '#E53E3E' : '#4A5568' }}>{c.urgency}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        <div style={{ display:'flex', flexDirection:'column', gap:'20px' }}>
                          {/* Most Demanded Categories Chart */}
                          <div className="gov-card" style={{ padding:'24px' }}>
                            <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'14px', fontWeight:700, color:'#003B7A', marginBottom:'14px', paddingBottom:'8px', borderBottom:'1px solid #DDE1E7' }}>
                              🎯 Most Demanded Sectors
                            </div>
                            {sortedCategories.length === 0 ? (
                              <div style={{ fontSize:'12px', color:'#6B6B6B', padding:'10px 0' }}>No demand data available yet.</div>
                            ) : (
                              <div style={{ display:'flex', flexDirection:'column', gap:'10px' }}>
                                {sortedCategories.map(([cat, count]) => {
                                  const total = firestoreComplaints.length || 1;
                                  const pct = Math.round((count / total) * 100);
                                  const barColor = cat.includes('Water') ? '#003B7A' : cat.includes('Road') ? '#138808' : cat.includes('Health') ? '#FF6B1A' : '#6B6B6B';
                                  return (
                                    <div key={cat}>
                                      <div style={{ display:'flex', justifyContent:'space-between', fontSize:'11.5px', fontWeight:700, color:'#1a1a1a', marginBottom:'4px' }}>
                                        <span>{cat}</span>
                                        <span>{count} ({pct}%)</span>
                                      </div>
                                      <div className="gov-progress-bar" style={{ height:'6px' }}>
                                        <div className="gov-progress-bar__fill" style={{ width:`${pct}%`, background:barColor }} />
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>

                          {/* Active Risk Alerts */}
                          <div className="gov-card" style={{ padding:'24px' }}>
                            <SectionHeader title="Active Risk Alerts" accent="#C62B2B" />
                            <div style={{ display:'flex', flexDirection:'column', gap:'10px' }}>
                              {criticalAlerts.length === 0 && waterQualityIssues === 0 ? (
                                <div style={{ fontSize:'12px', color:'#6B6B6B', textAlign:'center', padding:'10px 0' }}>✅ No critical risk alerts reported.</div>
                              ) : (
                                <>
                                  {/* Water Quality Alerts */}
                                  {waterQualityIssues > 0 && (
                                    <div style={{ padding:'10px 12px', background:'#FFF5F5', border:'1px solid #FEB2B2', borderRadius:'6px', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                                      <div>
                                        <div style={{ fontSize:'12px', fontWeight:700, color:'#C62B2B' }}>⚠️ Water Contamination Alert</div>
                                        <div style={{ fontSize:'11px', color:'#6B6B6B' }}>📍 {waterQualityIssues} habitations affected</div>
                                      </div>
                                      <span className="gov-badge gov-badge--red" style={{ background:'#E53E3E', color:'white' }}>Critical</span>
                                    </div>
                                  )}
                                  
                                  {/* Citizen High Urgency Alerts */}
                                  {criticalAlerts.slice(0, 3).map((a,i)=>(
                                    <div key={i} style={{ padding:'10px 12px', background:'#FFF5F5', border:'1px solid #FEB2B2', borderRadius:'6px', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                                      <div style={{ flex:1, marginRight:'8px' }}>
                                        <div style={{ fontSize:'12px', fontWeight:700, color:'#C62B2B', textOverflow:'ellipsis', overflow:'hidden', whiteSpace:'nowrap' }}>{a.text}</div>
                                        <div style={{ fontSize:'11px', color:'#6B6B6B' }}>📍 {a.village || 'General Area'}</div>
                                      </div>
                                      <span className="gov-badge gov-badge--red" style={{ background:'#E53E3E', color:'white' }}>High</span>
                                    </div>
                                  ))}
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                );
              })()}

              {activeTab === 'digital_twin' && (() => {
                const totalPopVal = constituencyData?.metrics?.population;
                const popVal = totalPopVal
                  ? (totalPopVal >= 100000 
                      ? `${(totalPopVal / 100000).toFixed(2)} Lakh`
                      : totalPopVal.toLocaleString())
                  : '4.2 Lakh';
                
                const villagesCount = constituencyData?.metrics?.total_villages || '312';
                const panchayatsCount = constituencyData?.metrics?.total_panchayats || '43';
                
                const totalRoads = constituencyData?.metrics?.roads?.count || 0;
                const completedRoads = constituencyData?.metrics?.roads?.completed || 0;
                const roadCoverPct = totalRoads > 0 ? Math.round((completedRoads / totalRoads) * 100) : 91;
                
                const totalHabs = constituencyData?.metrics?.water?.total_habitations || 0;
                const fullyCovered = constituencyData?.metrics?.water?.fully_covered || 0;
                const waterCoverPct = totalHabs > 0 ? Math.round((fullyCovered / totalHabs) * 100) : 78;

                const ptrVal = constituencyData?.metrics?.schools?.avg_ptr || 35;
                const healthScoreVal = constituencyData?.metrics?.healthcare?.count && totalPopVal
                  ? Math.round(Math.min(100, Math.min(100, 100 * ((constituencyData.metrics.healthcare.count / (totalPopVal / 10000)) / 2.5))))
                  : 72;
                const ptrScoreVal = ptrVal ? Math.round(Math.max(0, Math.min(100, 100 * (1 - (ptrVal - 20) / 40)))) : 61;

                const sectors = [
                  {sector:'Healthcare',score:healthScoreVal || 72,color:'#FF6B1A'},
                  {sector:'Education (PTR)',score:ptrScoreVal || 61,color:'#C62B2B'},
                  {sector:'Water Supply (JJM)',score:waterCoverPct || 78,color:'#003B7A'},
                  {sector:'Road Connectivity',score:roadCoverPct || 91,color:'#138808'},
                  {sector:'Digital Connectivity',score:55 + (selectedDistrict.length % 30),color:'#FF6B1A'},
                  {sector:'Sanitation (SBM)',score:80 + (selectedDistrict.length % 15),color:'#138808'},
                ];

                const activeRoads = constituencyData?.metrics?.roads_list || [];
                const pipelineProjects = activeRoads.slice(0, 4).map(r => {
                  let phase = 'Proposal';
                  let pct = 10;
                  let color = '#C62B2B';
                  const status = (r.status || '').toLowerCase();
                  if (status.includes('completed')) {
                    phase = 'Completed';
                    pct = 100;
                    color = '#138808';
                  } else if (status.includes('progress') || status.includes('stage') || status.includes('course')) {
                    phase = 'Construction';
                    pct = status.includes('base') ? 50 : status.includes('subbase') ? 40 : 70;
                    color = '#003B7A';
                  } else if (status.includes('tender')) {
                    phase = 'Tender';
                    pct = 30;
                    color = '#FF6B1A';
                  }
                  return {
                    name: r.name || 'Unnamed Road Project',
                    budget: `₹${r.cost_lakh ? r.cost_lakh.toFixed(0) : '0'}L`,
                    phase: phase,
                    pct: pct,
                    color: color
                  };
                });
                const finalPipeline = pipelineProjects.length > 0 ? pipelineProjects : [
                  {name:`${selectedDistrict} PHC Reconstruction`,budget:'₹42L',phase:'Tender',pct:30,color:'#FF6B1A'},
                  {name:`${selectedDistrict} Rural Water Pipeline (JJM)`,budget:'₹1.8Cr',phase:'Construction',pct:65,color:'#003B7A'},
                  {name:`${selectedDistrict} School Boundary Fencing`,budget:'₹8L',phase:'Completed',pct:100,color:'#138808'},
                  {name:`${selectedDistrict} PMGSY Link Road`,budget:'₹84L',phase:'Proposal',pct:10,color:'#C62B2B'},
                ];

                const dynamicDeficits = [];
                const highPtrSchools = constituencyData?.map_points?.schools?.filter(s => s.teachers > 0 && (s.students / s.teachers) > 35) || [];
                highPtrSchools.slice(0, 2).forEach(s => {
                  const ratio = (s.students / s.teachers).toFixed(1);
                  dynamicDeficits.push({
                    title: `Critical PTR: ${ratio}:1`,
                    loc: `${s.name} (${s.students} students, ${s.teachers} teachers)`,
                    level: 'High',
                    icon: '🏫',
                    color: '#FF6B1A'
                  });
                });
                const waterQ = constituencyData?.metrics?.water_quality_list || [];
                waterQ.slice(0, 2).forEach(w => {
                  dynamicDeficits.push({
                    title: `${w.parameter} Contamination`,
                    loc: `Village: ${w.village} (${w.habitation} habitation)`,
                    level: 'Critical',
                    icon: '⚗️',
                    color: '#C62B2B'
                  });
                });
                const partiallyCovered = (constituencyData?.metrics?.villages_list || []).filter(v => v.water_status === 'Partially Covered');
                partiallyCovered.slice(0, 2).forEach(v => {
                  dynamicDeficits.push({
                    title: 'Partial Water Cover',
                    loc: `Village: ${v.name} (${v.habitation_count} habitations)`,
                    level: 'Medium',
                    icon: '💧',
                    color: '#FF6B1A'
                  });
                });
                const complaints = firestoreComplaints || [];
                complaints.slice(0, 2).forEach(c => {
                  dynamicDeficits.push({
                    title: `${c.category || 'Local'} Grievance`,
                    loc: `📍 ${c.village || 'Habitation'}: "${c.text}"`,
                    level: c.urgency === 'High' ? 'Critical' : 'High',
                    icon: '🎙️',
                    color: c.urgency === 'High' ? '#C62B2B' : '#FF6B1A'
                  });
                });
                const finalDeficits = dynamicDeficits.length > 0 ? dynamicDeficits.slice(0, 6) : [
                  {title:'Fluoride Alert',loc:`Nagamangala Block — 28 habitations`,level:'Critical',icon:'⚗️',color:'#C62B2B'},
                  {title:'PHC Doctor Absence',loc:`${selectedDistrict} Sub-Centre — 3 consecutive days`,level:'High',icon:'🏥',color:'#FF6B1A'},
                  {title:'School PTR > 36:1',loc:`${selectedDistrict} Rural Upper Primary`,level:'High',icon:'🏫',color:'#FF6B1A'},
                ];

                return (
                  <>
                    <GovPageBanner title="Constituency Digital Twin" subtitle={`Live multi-layer intelligence model for ${selectedDistrict}, ${selectedState}`} breadcrumbs={['MP Dashboard','Digital Twin']} />
                    <div style={{ padding:'24px 28px', display:'grid', gap:'20px' }}>
                      <div className="gov-stat-grid" style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:'14px' }}>
                        {[
                          {id:'population',label:'Population',value:popVal,icon:'👥',color:'#003B7A'},
                          {id:'villages',label:'Villages',value:villagesCount,icon:'🏘️',color:'#138808'},
                          {id:'panchayats',label:'Gram Panchayats',value:panchayatsCount,icon:'🏛️',color:'#FF6B1A'},
                          {id:'roads',label:'PMGSY Road Cover',value:`${roadCoverPct}%`,icon:'🛣️',color:'#003B7A'},
                          {id:'water',label:'JJM Water Cover',value:`${waterCoverPct}%`,icon:'💧',color:'#C62B2B'},
                        ].map((s,i)=>(
                          <div 
                            key={i} 
                            onClick={() => {
                              setCardModalMode(s.id);
                              setCardSearchQuery('');
                              setSelectedDetailVillage(null);
                              setSelectedDetailPanchayat(null);
                              setCardModalOpen(true);
                            }}
                            className="gov-card" 
                            style={{ padding:'20px', textAlign:'center', borderTop:`3px solid ${s.color}`, cursor:'pointer', transition:'transform 0.15s' }}
                            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                            onMouseLeave={e => e.currentTarget.style.transform = 'none'}
                          >
                            <div style={{ fontSize:'28px', marginBottom:'6px' }}>{s.icon}</div>
                            <div style={{ fontSize:'20px', fontWeight:800, color:s.color, fontFamily:'Space Grotesk, sans-serif' }}>{s.value}</div>
                            <div style={{ fontSize:'11px', color:'#6B6B6B', fontWeight:600, marginTop:'4px' }}>{s.label}</div>
                          </div>
                        ))}
                      </div>
                      <div className="gov-grid-split" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'20px' }}>
                        <div className="gov-card" style={{ padding:'24px' }}>
                          <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>📊 Sector Health Index</div>
                          {sectors.map((s,i)=>(
                            <div key={i} style={{ marginBottom:'12px' }}>
                              <div style={{ display:'flex', justifyContent:'space-between', fontSize:'12px', fontWeight:700, color:'#1a1a1a', marginBottom:'5px' }}>
                                <span>{s.sector}</span><span style={{ color:s.color }}>{s.score}/100</span>
                              </div>
                              <div className="gov-progress-bar"><div className="gov-progress-bar__fill" style={{ width:`${s.score}%`, background:s.color }} /></div>
                            </div>
                          ))}
                        </div>
                        <div className="gov-card" style={{ padding:'24px' }}>
                          <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>🏗️ Active Project Pipeline</div>
                          {finalPipeline.map((p,i)=>(
                            <div key={i} style={{ marginBottom:'14px', padding:'12px', background:'#F5F7FA', borderRadius:'8px', border:'1px solid #DDE1E7' }}>
                              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'6px' }}>
                                <span style={{ fontSize:'12px', fontWeight:700, color:'#1a1a1a', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:'220px' }} title={p.name}>{p.name}</span>
                                <span className="gov-badge" style={{ background:`${p.color}15`, color:p.color }}>{p.phase}</span>
                              </div>
                              <div style={{ display:'flex', justifyContent:'space-between', fontSize:'11px', color:'#6B6B6B', marginBottom:'5px' }}><span>{p.budget}</span><span>{p.pct}%</span></div>
                              <div className="gov-progress-bar"><div className="gov-progress-bar__fill" style={{ width:`${p.pct}%`, background:p.color }} /></div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="gov-card" style={{ padding:'24px' }}>
                        <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>📡 AI Deficit Signals (Real-time)</div>
                        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'14px' }}>
                          {finalDeficits.map((a,i)=>(
                            <div key={i} style={{ padding:'14px', background:`${a.color}08`, border:`1px solid ${a.color}30`, borderRadius:'8px', borderLeft:`3px solid ${a.color}`, display:'flex', flexDirection:'column', justifyContent:'space-between' }}>
                              <div>
                                <div style={{ fontSize:'18px', marginBottom:'6px' }}>{a.icon}</div>
                                <div style={{ fontSize:'12px', fontWeight:700, color:a.color, marginBottom:'4px' }}>{a.title}</div>
                                <div style={{ fontSize:'11px', color:'#6B6B6B', marginBottom:'8px', lineHeight:1.4 }}>{a.loc}</div>
                              </div>
                              <span className="gov-badge" style={{ background:`${a.color}15`, color:a.color, fontSize:'10px', alignSelf:'flex-start' }}>{a.level}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                );
              })()}

              {activeTab === 'research_engine' && (
                <>
                  <GovPageBanner title="MP MITRA AI Research Engine" subtitle="Multi-agent knowledge retrieval + live web intelligence for evidence-based governance" breadcrumbs={['MP Dashboard','AI Research Engine']} />
                  <div style={{ padding:'24px 28px', display:'grid', gap:'20px' }}>
                    {/* Orchestrator Architecture Diagram */}
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>🧠 AI Orchestration Architecture</div>
                      <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'0', fontFamily:'monospace', fontSize:'12px' }}>
                        <div style={{ padding:'10px 28px', background:'linear-gradient(135deg,#003B7A,#0055aa)', color:'white', borderRadius:'10px', fontWeight:700, fontSize:'14px', boxShadow:'0 4px 12px rgba(0,59,122,0.3)' }}>🏛️ MP MITRA PLATFORM</div>
                        <div style={{ width:'2px', height:'20px', background:'#DDE1E7' }} />
                        <div style={{ padding:'10px 24px', background:'linear-gradient(135deg,#FF6B1A,#ff8c4a)', color:'white', borderRadius:'10px', fontWeight:700, fontSize:'13px', boxShadow:'0 4px 12px rgba(255,107,26,0.3)' }}>🤖 AI Orchestrator (Brain)</div>
                        <div style={{ width:'2px', height:'16px', background:'#DDE1E7' }} />
                        <div style={{ display:'flex', gap:'48px', alignItems:'flex-start' }}>
                          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'0' }}>
                            <div style={{ padding:'10px 20px', background:'#EEF3FA', border:'2px solid #003B7A', borderRadius:'10px', fontWeight:700, color:'#003B7A', textAlign:'center' }}>📚 Knowledge Agent<br/><span style={{ fontWeight:400, fontSize:'10px', color:'#6B6B6B' }}>Scheme DB • Census • NITI</span></div>
                            <div style={{ width:'2px', height:'14px', background:'#DDE1E7' }} />
                            <div style={{ padding:'8px 16px', background:'#F5F7FA', border:'1px solid #DDE1E7', borderRadius:'8px', fontSize:'10px', fontWeight:600, color:'#6B6B6B', textAlign:'center' }}>PostgreSQL • Firestore<br/>Crawled Schemes DB</div>
                          </div>
                          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'0' }}>
                            <div style={{ padding:'10px 20px', background:'#EAF6EA', border:'2px solid #138808', borderRadius:'10px', fontWeight:700, color:'#138808', textAlign:'center' }}>🌐 Live Research Agent<br/><span style={{ fontWeight:400, fontSize:'10px', color:'#6B6B6B' }}>Browser • Web Scraper</span></div>
                            <div style={{ width:'2px', height:'14px', background:'#DDE1E7' }} />
                            <div style={{ padding:'8px 16px', background:'#F5F7FA', border:'1px solid #DDE1E7', borderRadius:'8px', fontSize:'10px', fontWeight:600, color:'#6B6B6B', textAlign:'center' }}>PIB • MyScheme.gov.in<br/>Official District Portals</div>
                          </div>
                        </div>
                        <div style={{ width:'2px', height:'16px', background:'#DDE1E7' }} />
                        <div style={{ padding:'10px 24px', background:'linear-gradient(135deg,#138808,#1aaa0a)', color:'white', borderRadius:'10px', fontWeight:700, fontSize:'13px', boxShadow:'0 4px 12px rgba(19,136,8,0.3)' }}>✅ Recommendation Engine → MP Briefing</div>
                      </div>
                    </div>

                    {/* Live Research Query Panel */}
                    <div className="gov-grid-split" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'20px' }}>
                      <div className="gov-card" style={{ padding:'24px' }}>
                        <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>🔍 Research Query Interface</div>
                        <form onSubmit={e => { e.preventDefault(); const q = e.target.query.value; if (q) { alert(`AI Research Engine: Querying government databases and live web for: "${q}"\n\nSources checked:\n• PostgreSQL scheme database (${HISTORICAL_SCHEMES.length || 30}+ schemes)\n• PIB press release feeds\n• MyScheme.gov.in portal\n• District ${selectedDistrict} official portal\n\nResults ready. See Knowledge Panel →`); e.target.reset(); }}} style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
                          <input name="query" className="gov-input" placeholder={`e.g. "Water schemes for farmers in ${selectedDistrict}"...`} style={{ padding:'12px' }} />
                          <div style={{ display:'flex', gap:'8px', flexWrap:'wrap' }}>
                            {['Housing schemes for SC/ST','PMGSY road status','Jal Jeevan Mission coverage','MGNREGA wages delayed'].map((q,i)=>(
                              <button key={i} type="button" onClick={e=>{ e.currentTarget.closest('form').querySelector('input').value=q; }} style={{ padding:'5px 10px', background:'#EEF3FA', border:'1px solid #C5D3E8', borderRadius:'20px', fontSize:'11px', fontWeight:600, color:'#003B7A', cursor:'pointer' }}>{q}</button>
                            ))}
                          </div>
                          <button type="submit" className="gov-btn gov-btn--saffron" style={{ padding:'11px' }}>🔍 Run AI Research Query</button>
                        </form>
                        <div style={{ marginTop:'16px', padding:'12px', background:'#F5F7FA', borderRadius:'8px' }}>
                          <div style={{ fontSize:'11px', fontWeight:700, color:'#6B6B6B', textTransform:'uppercase', marginBottom:'8px' }}>Data Coverage</div>
                          {[
                            {label:'Historical Schemes (2010–2026)',count:'30+'},
                            {label:'District News Articles',count:'13+'},
                            {label:'Active Tenders',count:'7+'},
                            {label:'PIB Press Releases',count:'Live Feed'},
                          ].map((r,i)=>(
                            <div key={i} style={{ display:'flex', justifyContent:'space-between', fontSize:'12px', padding:'4px 0', borderBottom:'1px solid #DDE1E7' }}>
                              <span style={{ color:'#1a1a1a' }}>{r.label}</span>
                              <span style={{ fontWeight:700, color:'#003B7A' }}>{r.count}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="gov-card" style={{ padding:'24px' }}>
                        <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>💡 Top Scheme Matches — {selectedDistrict}</div>
                        <div style={{ display:'flex', flexDirection:'column', gap:'10px' }}>
                          {[
                            {name:'Jal Jeevan Mission (Har Ghar Jal)',ministry:'Ministry of Jal Shakti',cat:'Water & Sanitation',match:97,link:'https://jaljeevanmission.gov.in/'},
                            {name:'PM-KISAN Samman Nidhi',ministry:'Ministry of Agriculture',cat:'Agriculture',match:94,link:'https://pmkisan.gov.in/'},
                            {name:'PMAY-Gramin (Rural Housing)',ministry:'Ministry of Rural Development',cat:'Housing',match:91,link:'https://pmayg.nic.in/'},
                            {name:'Ayushman Bharat PM-JAY',ministry:'Ministry of Health',cat:'Healthcare',match:88,link:'https://pmjay.gov.in/'},
                            {name:'MGNREGA Employment',ministry:'Ministry of Rural Dev.',cat:'Employment',match:85,link:'https://nrega.nic.in/'},
                          ].map((s,i)=>(
                            <a key={i} href={s.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration:'none', display:'block', padding:'12px', background:'#F5F7FA', border:'1px solid #DDE1E7', borderRadius:'8px', borderLeft:'3px solid #003B7A', transition:'all 0.15s' }}
                              onMouseEnter={e=>e.currentTarget.style.background='#EEF3FA'}
                              onMouseLeave={e=>e.currentTarget.style.background='#F5F7FA'}>
                              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'4px' }}>
                                <span style={{ fontSize:'12px', fontWeight:700, color:'#003B7A', lineHeight:1.3, flex:1 }}>{s.name}</span>
                                <span style={{ fontSize:'10px', fontWeight:800, color:'#138808', background:'#EAF6EA', padding:'2px 7px', borderRadius:'10px', marginLeft:'8px', flexShrink:0 }}>{s.match}% match</span>
                              </div>
                              <div style={{ display:'flex', gap:'6px', flexWrap:'wrap', marginTop:'4px' }}>
                                <span className="gov-badge gov-badge--blue" style={{ fontSize:'10px' }}>{s.ministry}</span>
                                <span className="gov-badge" style={{ fontSize:'10px', background:'#F5F7FA', color:'#6B6B6B' }}>{s.cat}</span>
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Recent Crawled Intelligence */}
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <div style={{ fontFamily:'Space Grotesk, sans-serif', fontSize:'15px', fontWeight:700, color:'#003B7A', marginBottom:'16px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>📰 Live Intelligence Feed — Recent Crawled Data</div>
                      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'14px' }}>
                        {[
                          {title:'PIB: PMKISAN 17th Installment ₹20,000 Cr Released','source':'Press Information Bureau','time':'June 2024','cat':'Agriculture','color':'#138808'},
                          {title:`Fluoride in 28 Habitations — ${selectedDistrict}`,'source':'KSPCB Water Survey','time':'Dec 2023','cat':'Water Quality','color':'#C62B2B'},
                          {title:'PM-JAY: 7.37 Cr Hospitalizations Covered','source':'National Health Authority','time':'2024','cat':'Healthcare','color':'#003B7A'},
                          {title:`${selectedDistrict} PMGSY Road Connectivity at 91%`,'source':'MORD District Report','time':'2024','cat':'Roads','color':'#138808'},
                          {title:'MGNREGA: 346 Cr Person-Days 2023-24','source':'Ministry of Rural Dev.','time':'Apr 2024','cat':'Employment','color':'#FF6B1A'},
                          {title:`${selectedDistrict}: 2,140 PMAY-G Houses Completed`,'source':'Karnataka Housing Board','time':'2023-24','cat':'Housing','color':'#003B7A'},
                        ].map((n,i)=>(
                          <div key={i} style={{ padding:'14px', background:'white', border:'1px solid #DDE1E7', borderRadius:'8px', borderTop:`3px solid ${n.color}` }}>
                            <div style={{ fontSize:'12px', fontWeight:700, color:'#1a1a1a', marginBottom:'6px', lineHeight:1.4 }}>{n.title}</div>
                            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:'8px' }}>
                              <span style={{ fontSize:'10px', color:'#6B6B6B' }}>{n.source}</span>
                              <span className="gov-badge" style={{ background:`${n.color}15`, color:n.color, fontSize:'10px' }}>{n.cat}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'function_level' && (
                <FunctionLevelDashboard
                  selectedState={selectedState}
                  selectedDistrict={selectedDistrict}
                  constituencyData={constituencyData}
                  firestoreComplaints={firestoreComplaints}
                />
              )}

              {activeTab === 'search_projects' && (
                <VillageProjectSearch
                  selectedState={selectedState}
                  selectedDistrict={selectedDistrict}
                />
              )}

              {activeTab === 'map' && (
                <>
                  <GovPageBanner title="AI Priority Map & Heat Index" subtitle="Click category heatmap nodes to view detailed village deficit reports" breadcrumbs={['MP Dashboard','AI Priority Map']} />
                  <div style={{ padding:'20px 24px' }}>
                    <div className="gov-card" style={{ padding: 0, overflow: 'hidden' }}>
                      <ConstituencyMap activeDistrict={selectedDistrict} />
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'recommendations' && (
                <RecommendationsPanel sName={sName} dName={dName} />
              )}

              {activeTab === 'gaps' && (
                <>
                  <GovPageBanner title="Infrastructure Gap Analysis" subtitle="Deficits compared against NITI Aayog national guidelines" breadcrumbs={['MP Dashboard','Infrastructure Gaps']} />
                  <div style={{ padding:'24px 28px' }}>
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <div style={{ display:'flex', flexDirection:'column', gap:'24px' }}>
                        {[
                          {sector:'Primary Education (PTR Ratio)',status:'High Deficit',color:'#C62B2B',pct:82,desc:`${dName} average is 36:1, NITI guideline is 30:1.`},
                          {sector:'Potable Drinking Water (JJM Coverage)',status:'Critical Deficit',color:'#C62B2B',pct:91,desc:`Water coverage in 4 rural villages of ${dName} is under 20%.`},
                          {sector:'Road Connectivity (PMGSY Completion)',status:'Medium Deficit',color:'#FF6B1A',pct:48,desc:`${dName} connector road PMGSY tender pending.`},
                          {sector:'Primary Health Clinics (PHC Access)',status:'Critical Deficit',color:'#C62B2B',pct:88,desc:`Only 1 sub-centre clinic active for 12,000 citizens in ${dName}.`},
                          {sector:'Digital Connectivity (BharatNet)',status:'Low Deficit',color:'#138808',pct:22,desc:`70% village coverage achieved in ${dName} under BharatNet Phase II.`},
                        ].map((g,i) => (
                          <div key={i}>
                            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                              <span style={{ fontSize:'13px', fontWeight:700, color:'#1a1a1a' }}>{g.sector}</span>
                              <span className="gov-badge" style={{ background:`${g.color}15`, color:g.color }}>{g.status}</span>
                            </div>
                            <div className="gov-progress-bar">
                              <div className="gov-progress-bar__fill" style={{ width:`${g.pct}%`, background:g.color }} />
                            </div>
                            <p style={{ fontSize:'11px', color:'#6B6B6B', margin:'6px 0 0' }}>{g.desc}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'chat' && (
                <>
                  <GovPageBanner title="AI Decision Advisor" subtitle="MPLADS investment planning with multi-agent RAG reasoning" breadcrumbs={['MP Dashboard','AI Advisor Chat']} />
                  <div className="gov-chat-container" style={{ padding:'24px 28px', display:'flex', gap:'20px', flex:1, overflow:'hidden' }}>
                    <div className="gov-card" style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
                      <div style={{ flex:1, overflowY:'auto', padding:'20px', display:'flex', flexDirection:'column', gap:'16px' }}>
                        {copilotHistory.map((msg,i) => (
                          <div key={i} style={{ display:'flex', gap:'10px', flexDirection:msg.sender==='user'?'row-reverse':'row', maxWidth:'85%', alignSelf:msg.sender==='user'?'flex-end':'flex-start' }}>
                            <div style={{ width:'32px', height:'32px', borderRadius:'8px', background:msg.sender==='user'?'#003B7A':'#FF6B1A', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                              <span style={{ color:'white', fontSize:'14px' }}>{msg.sender==='user'?'MP':'AI'}</span>
                            </div>
                            <div style={{ padding:'14px 16px', borderRadius:'10px', background:msg.sender==='user'?'#EEF3FA':'white', border:'1px solid #DDE1E7', fontSize:'13px', color:'#1a1a1a', lineHeight:1.6 }}>
                              {msg.text}
                              {msg.sources && msg.sources.length > 0 && (
                                <div style={{ display:'flex', gap:'6px', flexWrap:'wrap', marginTop:'8px' }}>
                                  {msg.sources.map((s,si)=><span key={si} className="gov-badge gov-badge--blue" style={{ fontSize:'10px' }}>📂 {s}</span>)}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                      <form onSubmit={askCopilot} style={{ padding:'16px 20px', borderTop:'1px solid #DDE1E7', display:'flex', gap:'8px' }}>
                        <input type="text" value={copilotQuery} onChange={e=>setCopilotQuery(e.target.value)} placeholder="MP: 'Which ₹5 crore investment benefits most citizens?'" className="gov-input" style={{ flex:1 }} />
                        <button type="submit" disabled={queryingCopilot} className="gov-btn gov-btn--saffron"><ArrowRight size={15} /></button>
                      </form>
                    </div>

                    <div className="gov-card" style={{ width:'280px', padding:'16px', display:'flex', flexDirection:'column', overflow:'hidden' }}>
                      <div style={{ fontSize:'11px', fontWeight:700, textTransform:'uppercase', color:'#FF6B1A', letterSpacing:'0.06em', marginBottom:'12px' }}>Pipeline Execution Logs</div>
                      <div className="gov-log-panel" style={{ flex:1 }}>
                        {copilotLogs.length===0 && !queryingCopilot && <span style={{ color:'#555', fontStyle:'italic' }}>Submit queries to view logs...</span>}
                        {queryingCopilot && copilotLogs.length===0 && <span style={{ color:'#68d391' }}>Initialising RAG search agents...</span>}
                        {copilotLogs.map((log,i)=><div key={i} className="gov-log-panel__entry">{log}</div>)}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'optimizer' && (
                <>
                  <GovPageBanner title="MPLADS Budget Portfolio Optimizer" subtitle="Knapsack integer linear programming for optimal fund allocation" breadcrumbs={['MP Dashboard','Budget Optimizer']} />
                  <div className="gov-grid-split" style={{ padding:'24px 28px', display:'grid', gridTemplateColumns:'300px 1fr', gap:'20px' }}>
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <SectionHeader title="Optimization Parameters" />
                      <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
                        <div>
                          <label className="gov-label">MPLADS Budget Limit (₹ Crores)</label>
                          <input type="number" step="0.5" value={budgetCr} onChange={e=>setBudgetCr(parseFloat(e.target.value))} className="gov-input" />
                        </div>
                        <div>
                          <label className="gov-label">Citizen Demand Weight: {weights.demand}</label>
                          <input type="range" min="0" max="1" step="0.1" value={weights.demand} onChange={e=>setWeights({...weights,demand:parseFloat(e.target.value)})} style={{ width:'100%', accentColor:'#FF6B1A' }} />
                        </div>
                        <div>
                          <label className="gov-label">Infrastructure Gap Weight: {weights.gap}</label>
                          <input type="range" min="0" max="1" step="0.1" value={weights.gap} onChange={e=>setWeights({...weights,gap:parseFloat(e.target.value)})} style={{ width:'100%', accentColor:'#FF6B1A' }} />
                        </div>
                        <button onClick={runOptimization} disabled={optimizing} className="gov-btn gov-btn--saffron" style={{ width:'100%', padding:'12px' }}>
                          {optimizing ? '⏳ Solving...' : '⚡ Run Knapsack Solver'}
                        </button>
                      </div>
                    </div>

                    <div className="gov-card" style={{ padding:'24px', display:'flex', flexDirection:'column', overflow:'hidden' }}>
                      <SectionHeader title="Recommended Project Portfolio" />
                      <div style={{ flex:1, overflowY:'auto' }}>
                        {!optimizationResult ? (
                          <div style={{ textAlign:'center', padding:'60px 20px', color:'#6B6B6B' }}>
                            <div style={{ fontSize:'40px', marginBottom:'12px' }}>⚡</div>
                            <p style={{ fontSize:'13px', margin:0 }}>Configure parameters and click "Run Knapsack Solver" to generate AI-optimised project portfolio.</p>
                          </div>
                        ) : (
                          <>
                            <div className="gov-grid-3col" style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'12px', marginBottom:'20px' }}>
                              <StatCard label="Total Allocation" value={`₹${optimizationResult.total_cost_lakh?.toFixed(1)} L`} color="#FF6B1A" />
                              <StatCard label="Beneficiaries" value={optimizationResult.total_beneficiaries?.toLocaleString()} color="#138808" />
                              <StatCard label="Portfolio Score" value={`${optimizationResult.aggregate_score?.toFixed(1)}/100`} color="#003B7A" />
                            </div>
                            <table className="gov-table">
                              <thead><tr><th>Project</th><th>Village</th><th>Cost</th><th>Scheme</th><th>Score</th></tr></thead>
                              <tbody>
                                {optimizationResult.selected_projects?.map((p,i)=>(
                                  <React.Fragment key={i}>
                                    <tr 
                                      onClick={() => setExpandedRowIndex(expandedRowIndex === i ? null : i)}
                                      style={{ cursor: 'pointer', background: expandedRowIndex === i ? '#F0F4F8' : '' }}
                                    >
                                      <td style={{ fontWeight:600 }}>
                                        <div style={{ display:'flex', alignItems:'center', gap:'6px' }}>
                                          <span style={{ fontSize:'10px', color:'#003B7A' }}>{expandedRowIndex === i ? '▼' : '▶'}</span>
                                          {p.name}
                                        </div>
                                      </td>
                                      <td>{p.village}</td>
                                      <td>₹{p.cost_lakh}L</td>
                                      <td><span className="gov-badge gov-badge--blue">{p.scheme}</span></td>
                                      <td><strong style={{ color:'#FF6B1A' }}>{p.priority_score?.toFixed(1)}</strong></td>
                                    </tr>
                                    {expandedRowIndex === i && (
                                      <tr>
                                        <td colSpan={5} style={{ background: '#F8FAFC', padding: '16px 24px', borderTop: 'none' }}>
                                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px', color: '#4A5568', lineHeight: 1.5 }}>
                                            <div>
                                              <strong>📍 Location:</strong> <span style={{ color: '#1a1a1a', fontWeight: 600 }}>{p.location || `${p.village}, ${selectedDistrict}, ${selectedState}`}</span>
                                            </div>
                                            <div>
                                              <strong>❓ What is the problem:</strong> <span style={{ color: '#1a1a1a' }}>{p.problem || "Infrastructure deficit detected in sector."}</span>
                                            </div>
                                            <div>
                                              <strong>🎯 Why Chosen:</strong> <span style={{ color: '#1a1a1a' }}>{p.why_chosen || p.rationale || "Selected based on priority score optimization."}</span>
                                            </div>
                                            <div>
                                              <strong>🛠️ Solution:</strong> <span style={{ color: '#1a1a1a' }}>{p.how_to_fix || "Allocate budget to execute community development upgrade."}</span>
                                            </div>
                                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: '#EDF2F7', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', color: '#2D3748', width: 'fit-content', marginTop: '4px' }}>
                                              <span>🗣️</span> <strong>Citizen Volume:</strong> <span style={{ fontWeight: 700, color: '#FF6B1A' }}>{p.citizens_voice || `${Math.floor(p.priority_score * 2.8)} complaints registered`}</span>
                                            </div>
                                          </div>
                                        </td>
                                      </tr>
                                    )}
                                  </React.Fragment>
                                ))}
                              </tbody>
                            </table>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'tracking' && (
                <>
                  <GovPageBanner title="Project Lifecycle Tracking" subtitle="Monitor project execution phases from proposal to completion" breadcrumbs={['MP Dashboard','Project Tracking']} />
                  <div style={{ padding:'24px 28px', overflowX:'auto' }}>
                    <div style={{ display:'flex', gap:'16px', minWidth:'900px' }}>
                      {[
                        {step:'Proposal', list:[`${dName} PHC Building`,`${dName} East Water Pipe`]},
                        {step:'Approved', list:[`${dName} Drainage Layout`]},
                        {step:'Tender', list:[]},
                        {step:'Construction', list:[`${dName} Sector 4 Tube Well`]},
                        {step:'Inspection', list:[]},
                        {step:'Completed', list:[`${dName} School Fencing`]},
                      ].map((col,i) => (
                        <div key={i} className="gov-card" style={{ flex:1, padding:'16px', display:'flex', flexDirection:'column', minHeight:'400px' }}>
                          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'14px', paddingBottom:'10px', borderBottom:'1px solid #DDE1E7' }}>
                            <span style={{ fontSize:'12px', fontWeight:700, color:'#003B7A', textTransform:'uppercase' }}>{col.step}</span>
                            <span className="gov-badge gov-badge--blue">{col.list.length}</span>
                          </div>
                          <div style={{ display:'flex', flexDirection:'column', gap:'8px' }}>
                            {col.list.map((p,pi) => (
                              <div key={pi} style={{ padding:'10px 12px', background:'#F5F7FA', border:'1px solid #DDE1E7', borderRadius:'6px', fontSize:'12px', fontWeight:600, color:'#1a1a1a' }}>{p}</div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'news' && (
                <>
                  <GovPageBanner title="News & Alert Intelligence Feed" subtitle="Real-time monitoring of local news portals and district updates" breadcrumbs={['MP Dashboard','News Intelligence']} />
                  <div style={{ padding:'24px 28px' }}>
                    {loadingNews ? (
                      <div style={{ textAlign:'center', color:'#6B6B6B', fontSize:'14px', padding:'40px' }}>⏳ Loading real-time news intelligence feed...</div>
                    ) : newsFeed.length === 0 ? (
                      <div style={{ textAlign:'center', color:'#6B6B6B', fontSize:'14px', padding:'40px', background:'white', borderRadius:'12px', border:'1px solid #DDE1E7' }}>
                        📭 No recent news intelligence feed items found for {selectedDistrict}. 
                        <br /><span style={{ fontSize:'11.5px', marginTop:'8px', display:'block', color:'#A0AEC0' }}>Try running the **AI Web Scraper** from the Admin Console to crawl real-time development feeds.</span>
                      </div>
                    ) : (
                      <div className="gov-grid-3col" style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'20px' }}>
                        {newsFeed.map((n,i) => {
                          const pubDate = n.crawled_at ? new Date(n.crawled_at).toLocaleDateString() : 'Recent';
                          const cardColor = n.category?.includes('Water') ? '#003B7A' : n.category?.includes('Road') ? '#138808' : n.category?.includes('School') ? '#FF6B1A' : '#C62B2B';
                          return (
                            <div key={i} className="gov-card" style={{ padding:'20px', borderLeft:`4px solid ${cardColor}`, display:'flex', flexDirection:'column', justifyContent:'space-between', gap:'12px' }}>
                              <div>
                                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                                  <span style={{ fontSize:'10px', fontWeight:700, textTransform:'uppercase', color:'#003B7A' }}>{n.source}</span>
                                  <span style={{ fontSize:'10px', color:'#999' }}>{pubDate}</span>
                                </div>
                                <h4 style={{ fontSize:'14px', fontWeight:700, color:'#1a1a1a', margin:'0 0 6px 0', fontFamily:'Space Grotesk, sans-serif', lineHeight:1.4 }}>{n.title}</h4>
                                <p style={{ fontSize:'12.5px', color:'#4A5568', lineHeight:1.6, margin:0 }}>{n.summary}</p>
                              </div>

                              {/* Render dynamic columns if present */}
                              <div style={{ display:'flex', flexDirection:'column', gap:'6px', borderTop:'1px solid #E2E8F0', paddingTop:'10px', fontSize:'11.5px', color:'#4A5568' }}>
                                {n.exact_area && <div><strong>📍 Location:</strong> <span style={{ color:'#1a1a1a' }}>{n.exact_area}</span></div>}
                                {n.pothole_count > 0 && <div><strong>🕳️ Potholes Count:</strong> <span style={{ color:'#C62B2B', fontWeight:700 }}>{n.pothole_count}</span></div>}
                                {n.road_length_km > 0 && <div><strong>🛣️ Length:</strong> <span style={{ color:'#1a1a1a' }}>{n.road_length_km} km</span></div>}
                                {n.estimated_cost && <div><strong>💰 Cost Estimate:</strong> <span style={{ color:'#FF6B1A', fontWeight:700 }}>{n.estimated_cost}</span></div>}
                                {n.affected_pop > 0 && <div><strong>🗣️ Affected Population:</strong> <span style={{ color:'#1a1a1a' }}>{n.affected_pop} citizens</span></div>}
                                {n.remediation_plan && <div><strong>🛠️ Remediation:</strong> <span style={{ color:'#003B7A', fontStyle:'italic' }}>{n.remediation_plan}</span></div>}
                              </div>

                              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:'4px' }}>
                                <span className="gov-badge" style={{ background:`${cardColor}15`, color:cardColor }}>{n.category}</span>
                                <a href={n.link} target="_blank" rel="noreferrer" style={{ fontSize:'11px', color:'#FF6B1A', fontWeight:700 }}>Source link ↗</a>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </>
              )}

              {activeTab === 'crawled_data' && (
                <WebScraperDatabaseConsole
                  selectedState={selectedState}
                  selectedDistrict={selectedDistrict}
                  crawledDataType={crawledDataType}
                  setCrawledDataType={setCrawledDataType}
                  crawledDataSearch={crawledDataSearch}
                  setCrawledDataSearch={setCrawledDataSearch}
                  crawledDataList={crawledDataList}
                  loadingCrawled={loadingCrawled}
                  selectedCrawledItem={selectedCrawledItem}
                  setSelectedCrawledItem={setSelectedCrawledItem}
                />
              )}

              {activeTab === 'reports' && (
                <>
                  <GovPageBanner title="Reports & Document Exports" subtitle="Generate parliamentary briefings and district intelligence documents" breadcrumbs={['MP Dashboard','Reports & Exports']} />
                  <div className="gov-grid-2col" style={{ padding:'24px 28px', display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'20px', maxWidth:'720px' }}>
                    {[
                      {type:'Parliament Report',desc:'Detailed MPLADS allocation briefing with NITI indices and priority scores.',icon:'📄'},
                      {type:'District Intelligence Brief',desc:'Summary of active grievances, village water cover, and PHC shortages.',icon:'📊'},
                    ].map((r,i) => (
                      <button key={i} onClick={()=>{setReportsLogs(`Generating ${r.type}... Ingesting Firestore records... Compiling charts... Export ready!`);confetti({particleCount:60,spread:40});}} className="gov-card gov-card--navy" style={{ padding:'24px', cursor:'pointer', textAlign:'left', background:'white', border:'1px solid #DDE1E7', transition:'all 0.2s' }}>
                        <div style={{ fontSize:'32px', marginBottom:'14px' }}>{r.icon}</div>
                        <h3 style={{ fontSize:'15px', fontWeight:700, color:'#003B7A', margin:'0 0 8px', fontFamily:'Space Grotesk, sans-serif' }}>{r.type}</h3>
                        <p style={{ fontSize:'12px', color:'#6B6B6B', lineHeight:1.5, margin:0 }}>{r.desc}</p>
                      </button>
                    ))}
                    {reportsLogs && (
                      <div className="gov-log-panel" style={{ gridColumn:'1/-1', maxHeight:'120px' }}>
                        <div className="gov-log-panel__entry">{reportsLogs}</div>
                      </div>
                    )}
                  </div>
                </>
              )}

              {activeTab === 'whatsapp_sim' && (
                <WhatsAppSimulator />
              )}
            </>
          )}

          {/* ────── OFFICER PORTAL TABS ────── */}
          {isOfficer && (
            <>
              {activeTab === 'home' && (
                <>
                  <GovPageBanner title="Assigned Projects" subtitle="Monitor construction and compliance steps for projects in your sector" breadcrumbs={['Officer Portal','Assigned Projects']} />
                  <div className="gov-grid-2col" style={{ padding:'24px 28px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:'20px' }}>
                    {[
                      {name:`${dName} Tube Well Installation`,village:`${dName} Rural`,cost:'₹14 Lakhs',progress:65,status:'Construction'},
                      {name:`${dName} Primary School Boundary Fencing`,village:`${dName} Centroid`,cost:'₹8 Lakhs',progress:100,status:'Completed'},
                    ].map((p,i) => (
                      <div key={i} className="gov-card gov-card--green" style={{ padding:'20px' }}>
                        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'14px' }}>
                          <div>
                            <h3 style={{ fontSize:'15px', fontWeight:700, color:'#1a1a1a', margin:'0 0 4px', fontFamily:'Space Grotesk, sans-serif' }}>{p.name}</h3>
                            <span style={{ fontSize:'11px', color:'#138808', fontWeight:600 }}>📍 {p.village}</span>
                          </div>
                          <span className="gov-badge gov-badge--green">{p.status}</span>
                        </div>
                        <div style={{ marginBottom:'8px', display:'flex', justifyContent:'space-between', fontSize:'12px', color:'#6B6B6B', fontWeight:600 }}>
                          <span>Progress</span><span>{p.progress}%</span>
                        </div>
                        <div className="gov-progress-bar"><div className="gov-progress-bar__fill" style={{ width:`${p.progress}%`, background:'#138808' }} /></div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {activeTab === 'inspections' && (
                <>
                  <GovPageBanner title="Inspection Schedule" subtitle="Upcoming site visits and verification checks" breadcrumbs={['Officer Portal','Inspection Schedule']} />
                  <div style={{ padding:'24px 28px', maxWidth:'680px' }}>
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <table className="gov-table">
                        <thead><tr><th>Project</th><th>Scheduled Date & Time</th><th>Status</th></tr></thead>
                        <tbody>
                          {officerInspections.map(ins => (
                            <tr key={ins.id}><td style={{ fontWeight:600 }}>{ins.project.replace('Ramapura', dName).replace('Kothimir', dName + ' East')}</td><td>{ins.schedule}</td><td><span className="gov-badge gov-badge--green">{ins.status}</span></td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'tasks' && (
                <>
                  <GovPageBanner title="Pending Task Checklist" subtitle="Administrative tasks required to register project completion" breadcrumbs={['Officer Portal','Pending Tasks']} />
                  <div style={{ padding:'24px 28px', maxWidth:'680px' }}>
                    <div className="gov-card" style={{ padding:'24px', display:'flex', flexDirection:'column', gap:'12px' }}>
                      {officerTasks.map(t => (
                        <div key={t.id} style={{ display:'flex', alignItems:'center', gap:'12px', padding:'14px', background:'#F5F7FA', border:'1px solid #DDE1E7', borderRadius:'8px' }}>
                          <CheckSquare size={18} color="#138808" />
                          <span style={{ flex:1, fontSize:'13px', fontWeight:600, color:'#1a1a1a' }}>{t.title.replace('Ramapura', dName)}</span>
                          <span className="gov-badge gov-badge--gray">Due {t.date}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'photos' && (
                <>
                  <GovPageBanner title="Field Proof Uploads" subtitle="Upload geotagged inspection photos and completion documents" breadcrumbs={['Officer Portal','Field Uploads']} />
                  <div style={{ padding:'24px 28px', maxWidth:'480px' }}>
                    <div className="gov-card" style={{ padding:'28px', textAlign:'center' }}>
                      <div style={{ fontSize:'48px', marginBottom:'16px' }}>📷</div>
                      <h3 style={{ fontSize:'16px', fontWeight:700, color:'#003B7A', margin:'0 0 8px', fontFamily:'Space Grotesk, sans-serif' }}>Upload Field Inspection Proof</h3>
                      <p style={{ fontSize:'12px', color:'#6B6B6B', marginBottom:'20px', lineHeight:1.6 }}>Upload geotagged site photographs or PDF completion reports for assigned projects.</p>
                      <label style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'12px', padding:'32px', background:'#F5F7FA', border:'2px dashed #DDE1E7', borderRadius:'8px', cursor:'pointer' }}>
                        <Upload size={24} color="#003B7A" />
                        <span style={{ fontSize:'13px', fontWeight:600, color:'#003B7A' }}>Select Files or Drag & Drop</span>
                        <span style={{ fontSize:'11px', color:'#999' }}>Supports JPG, PNG, PDF up to 10MB</span>
                        <input type="file" style={{ display:'none' }} multiple />
                      </label>
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {/* ────── ADMIN PORTAL TABS ────── */}
          {isAdmin && (
            <>
              {activeTab === 'admin' && (
                <>
                  <GovPageBanner title="National Dataset Ingestion" subtitle="Upload government registry CSV files to retrain AI models" breadcrumbs={['Admin Console','Dataset Ingestion']} />
                  <div className="gov-grid-split" style={{ padding:'24px 28px', display:'grid', gridTemplateColumns:'320px 1fr', gap:'20px' }}>
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <SectionHeader title="Upload CSV Dataset" accent="#C62B2B" />
                      <form onSubmit={handleAdminUpload} style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
                        <label style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'12px', padding:'24px', background:'#F5F7FA', border:'2px dashed #DDE1E7', borderRadius:'8px', cursor:'pointer' }}>
                          <FileSpreadsheet size={28} color="#C62B2B" />
                          <span style={{ fontSize:'12px', fontWeight:600, color:'#1a1a1a' }}>{adminFile ? adminFile.name : 'Select CSV File'}</span>
                          <input type="file" accept=".csv" onChange={e=>setAdminFile(e.target.files[0])} style={{ display:'none' }} />
                        </label>
                        <button type="submit" disabled={uploading||!adminFile} className="gov-btn gov-btn--red" style={{ width:'100%', padding:'12px', opacity:(uploading||!adminFile)?0.5:1 }}>
                          {uploading ? '⏳ Processing...' : 'Ingest Dataset'}
                        </button>
                      </form>
                    </div>

                    <div className="gov-card" style={{ padding:'24px', display:'flex', flexDirection:'column' }}>
                      <SectionHeader title="Auto-Training Pipeline Logs" />
                      <div className="gov-log-panel" style={{ flex:1, minHeight:'280px' }}>
                        {uploadLogs.length===0 && !uploading && <span style={{ color:'#555', fontStyle:'italic' }}>Submit a CSV to launch the auto-schema classifier and retraining agent...</span>}
                        {uploading && uploadLogs.length===0 && <span style={{ color:'#fbd38d' }}>Admin Agent: Parsing file rows...</span>}
                        {uploadLogs.map((log,i)=><div key={i} className="gov-log-panel__entry">{log}</div>)}
                        {uploadResult && uploadLogs.length===uploadResult.pipeline_logs?.length && (
                          <div style={{ marginTop:'12px', padding:'12px', background:'rgba(20,200,60,0.1)', border:'1px solid #138808', borderRadius:'6px', fontFamily:'Inter,sans-serif', color:'#138808', fontWeight:700 }}>
                            ✅ Dataset Ingested — {uploadResult.rows_processed} rows | Type: {uploadResult.detected_type}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'scraper' && (
                <ScraperConsole />
              )}


              {activeTab === 'users' && (
                <>
                  <GovPageBanner title="User Access Control" subtitle="Manage registered system profiles and role assignments" breadcrumbs={['Admin Console','User Access Control']} />
                  <div style={{ padding:'24px 28px' }}>
                    <div className="gov-card" style={{ padding:'24px', overflowX:'auto' }}>
                      <table className="gov-table">
                        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
                        <tbody>
                          {[{name:'Harshith Kd',email:'citizen@gmail.com',role:'Citizen'},{name:'Dr. Ramesh Kumar',email:'mp@parliament.nic.in',role:'MP'},{name:'Amit Singh',email:'officer@constituency.gov.in',role:'Officer'},{name:'Admin Root',email:'admin@parliament.nic.in',role:'Admin'}].map((u,i)=>(
                            <tr key={i}>
                              <td style={{ fontWeight:600 }}>{u.name}</td>
                              <td>{u.email}</td>
                              <td><span className="gov-badge" style={{ background: u.role==='Citizen'?'#EEF3FA':u.role==='MP'?'#FFF3EC':u.role==='Officer'?'#EAF6EA':'#FDECEA', color: u.role==='Citizen'?'#003B7A':u.role==='MP'?'#FF6B1A':u.role==='Officer'?'#138808':'#C62B2B' }}>{u.role}</span></td>
                              <td><span className="gov-badge gov-badge--green">Active</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'models' && (
                <>
                  <GovPageBanner title="AI Model Health Monitor" subtitle="Real-time accuracy and performance metrics for deployed models" breadcrumbs={['Admin Console','AI Models Health']} />
                  <div className="gov-grid-4col" style={{ padding:'24px 28px', display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'16px' }}>
                    {[{model:'Whisper indic-v3',type:'Speech Transcription',health:98.2},{model:'YOLOv11-infra',type:'Image Defect Detection',health:94.6},{model:'TF-IDF Clusterer',type:'Duplicate Detection',health:100},{model:'Qwen RAG Agent',type:'Copilot Chatbot',health:97.8}].map((m,i)=>(
                      <div key={i} className="gov-card gov-card--navy" style={{ padding:'20px', textAlign:'center' }}>
                        <div style={{ fontSize:'28px', fontWeight:800, color:'#003B7A', fontFamily:'Space Grotesk, sans-serif', lineHeight:1 }}>{m.health}%</div>
                        <div style={{ fontSize:'13px', fontWeight:700, color:'#1a1a1a', margin:'10px 0 4px' }}>{m.model}</div>
                        <div style={{ fontSize:'11px', color:'#6B6B6B' }}>{m.type}</div>
                        <div style={{ display:'flex', alignItems:'center', gap:'6px', justifyContent:'center', marginTop:'12px' }}>
                          <div style={{ width:'6px', height:'6px', background:'#138808', borderRadius:'50%' }} />
                          <span style={{ fontSize:'10px', color:'#138808', fontWeight:700 }}>ACTIVE</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {activeTab === 'audit' && (
                <>
                  <GovPageBanner title="Audit System Logs" subtitle="Immutable real-time log of system actions and API executions" breadcrumbs={['Admin Console','Audit Logs']} />
                  <div style={{ padding:'24px 28px' }}>
                    <div className="gov-card" style={{ padding:'24px' }}>
                      <div className="gov-log-panel" style={{ maxHeight:'400px' }}>
                        {['[2026-07-05 23:01:14] Ingested 1 complaint for State: KARNATAKA, District: MANDYA.','[2026-07-05 22:58:32] Run knapsack pulp solver: Budget=₹10Cr, beneficiaries=1.2 Lakhs.','[2026-07-05 22:55:04] AI Ingest Classifier Retraining triggered. Loss=0.042.','[2026-07-05 22:51:19] Broadcaster: Dispatched FCM notification payload.','[2026-07-05 22:48:05] Admin uploaded: PMGSY_roads_2024.csv — 4821 rows parsed.'].map((log,i)=>(
                          <div key={i} style={{ padding:'4px 0', borderBottom:'1px solid rgba(255,255,255,0.06)', color:'#a0aec0' }}>{log}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'whatsapp_sim' && (
                <WhatsAppSimulator />
              )}
            </>
          )}

          {toast && (
            <div style={{ position: 'fixed', bottom: '24px', right: '24px', background: '#003B7A', color: 'white', padding: '18px 24px', borderRadius: '10px', boxShadow: '0 10px 25px rgba(0,0,0,0.15)', zIndex: 99999, maxWidth: '340px', borderLeft: '4px solid #FF6B1A', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 800, fontSize: '13px', fontFamily: 'Space Grotesk, sans-serif' }}>🔔 {toast.title}</span>
                <button onClick={() => setToast(null)} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '12px', padding: '2px' }}>✕</button>
              </div>
              <div style={{ fontSize: '11px', lineHeight: 1.5, opacity: 0.9 }}>{toast.body}</div>
              <span style={{ fontSize: '9px', fontFamily: 'monospace', opacity: 0.6, alignSelf: 'flex-end' }}>{toast.id}</span>
            </div>
          )}

          {cardModalOpen && (
            <CardDetailsModal
              open={cardModalOpen}
              onClose={() => setCardModalOpen(false)}
              mode={cardModalMode}
              constituencyData={constituencyData}
              searchQuery={cardSearchQuery}
              setSearchQuery={setCardSearchQuery}
              selectedVillage={selectedDetailVillage}
              setSelectedVillage={setSelectedDetailVillage}
              selectedPanchayat={selectedDetailPanchayat}
              setSelectedPanchayat={setSelectedDetailPanchayat}
            />
          )}
        </main>
      </div>
    </div>
  );
}
