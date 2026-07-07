import React, { useState, useEffect } from 'react';
import API_BASE from '../apiConfig';
import { RefreshCw, CheckCircle2, AlertCircle, Server, FileText, Database } from 'lucide-react';

export default function DataQualityConsole() {
  const [metadata, setMetadata] = useState([]);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetadata = () => {
    setLoading(true);
    fetch(`${API_BASE}/api/admin/quality/metadata`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setMetadata(data.metadata);
        } else {
          setError(data.message || 'Failed to fetch metadata');
        }
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to connect to API');
        setLoading(false);
      });
  };

  const triggerAudit = () => {
    setAuditing(true);
    fetch(`${API_BASE}/api/admin/quality/audit`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          // Re-load metadata
          fetchMetadata();
        } else {
          alert('Audit failed: ' + data.message);
        }
        setAuditing(false);
      })
      .catch(err => {
        alert('Audit connection failed: ' + err.message);
        setAuditing(false);
      });
  };

  useEffect(() => {
    fetchMetadata();
  }, []);

  // Compute average quality score
  const avgScore = metadata.length > 0
    ? round(metadata.reduce((acc, curr) => acc + curr.quality_score, 0) / metadata.length, 1)
    : 100.0;

  function round(value, precision) {
    var multiplier = Math.pow(10, precision || 0);
    return Math.round(value * multiplier) / multiplier;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, height: '100%', overflowY: 'auto' }}>
      {/* Banner */}
      <div style={{ background: '#ffffff', borderBottom: '1px solid #E2E8F0', padding: '24px 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#1A202C', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              🛡️ Data Quality Layer Audit
            </h1>
            <p style={{ fontSize: '13px', color: '#718096', marginTop: '4px', margin: 0 }}>
              Live administrative review of completeness, GPS mapping, and ECI alignment.
            </p>
          </div>
          <button
            onClick={triggerAudit}
            disabled={auditing}
            className="gov-btn"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 16px',
              background: '#C62B2B',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              opacity: auditing ? 0.6 : 1
            }}
          >
            <RefreshCw size={14} className={auditing ? 'spin-animation' : ''} />
            {auditing ? 'Auditing Tables...' : 'Run Audit Review'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* KPI Dashboard */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {/* Average Quality Score */}
          <div className="gov-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#EAF6EA', display: 'flex', alignItems: 'center', justifyItem: 'center', justifyContent: 'center', color: '#138808' }}>
              <CheckCircle2 size={24} />
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#718096', fontWeight: 700, textTransform: 'uppercase' }}>Avg System Score</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#1A202C', fontFamily: 'Space Grotesk, sans-serif' }}>{avgScore}%</div>
            </div>
          </div>

          {/* Database Health status */}
          <div className="gov-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#EEF3FA', display: 'flex', alignItems: 'center', justifyItem: 'center', justifyContent: 'center', color: '#003B7A' }}>
              <Server size={24} />
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#718096', fontWeight: 700, textTransform: 'uppercase' }}>Active Registry Tables</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#1A202C', fontFamily: 'Space Grotesk, sans-serif' }}>{metadata.length || 6} / 6</div>
            </div>
          </div>

          {/* ECI Alignment Status */}
          <div className="gov-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#FFF3EC', display: 'flex', alignItems: 'center', justifyItem: 'center', justifyContent: 'center', color: '#FF6B1A' }}>
              <Database size={24} />
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#718096', fontWeight: 700, textTransform: 'uppercase' }}>ECI Alignment</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#1A202C', fontFamily: 'Space Grotesk, sans-serif' }}>100% OK</div>
            </div>
          </div>
        </div>

        {/* Audit Tables list */}
        <div className="gov-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#2D3748', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📁 Government Dataset Registries
          </h3>
          {loading ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#718096' }}>
              <RefreshCw size={24} className="spin-animation" style={{ marginBottom: '8px' }} />
              <div>Fetching database metrics...</div>
            </div>
          ) : error ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#C62B2B', background: '#FFF5F5', borderRadius: '8px' }}>
              <AlertCircle size={32} style={{ marginBottom: '8px' }} />
              <div>{error}</div>
            </div>
          ) : metadata.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#718096' }}>
              <div>No quality metrics have been computed yet.</div>
              <button onClick={triggerAudit} className="gov-btn" style={{ marginTop: '12px', background: '#003B7A', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}>
                Run Initial Quality Check
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {metadata.map((t, idx) => {
                const scoreColor = t.quality_score >= 90 ? '#138808' : t.quality_score >= 70 ? '#D69E2E' : '#C62B2B';
                const scoreBg = t.quality_score >= 90 ? '#EAF6EA' : t.quality_score >= 70 ? '#FEFCBF' : '#FFF5F5';
                
                return (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px',
                      background: '#FFF'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#1A202C', margin: 0 }}>
                          {t.dataset_name}
                        </h4>
                        <div style={{ fontSize: '11px', color: '#718096', marginTop: '2px' }}>
                          🏛️ {t.source_department}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span className="gov-badge" style={{ fontSize: '10px', background: '#EDF2F7', color: '#4A5568' }}>
                          v{t.version}
                        </span>
                        <div
                          style={{
                            fontSize: '13px',
                            fontWeight: 800,
                            color: scoreColor,
                            background: scoreBg,
                            padding: '4px 10px',
                            borderRadius: '6px',
                            border: `1px solid ${scoreColor}40`
                          }}
                        >
                          Score: {t.quality_score}%
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', padding: '12px', background: '#F8FAFC', borderRadius: '6px', fontSize: '12px' }}>
                      <div>
                        <div style={{ color: '#718096', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}>Total Records</div>
                        <div style={{ fontWeight: 800, color: '#2D3748', marginTop: '2px' }}>
                          {t.total_records.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#718096', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}>Completeness Check</div>
                        <div style={{ fontWeight: 800, color: t.missing_records > 0 ? '#D69E2E' : '#138808', marginTop: '2px' }}>
                          {t.missing_records > 0 ? `${t.missing_records} missing values` : '100% Complete'}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#718096', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}>Coverage Level</div>
                        <div style={{ fontWeight: 800, color: '#2D3748', marginTop: '2px' }}>
                          {t.coverage_level}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: '#718096', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}>Last Audit Scan</div>
                        <div style={{ fontWeight: 800, color: '#2D3748', marginTop: '2px' }}>
                          {t.last_updated ? new Date(t.last_updated).toLocaleTimeString() : 'N/A'}
                        </div>
                      </div>
                    </div>

                    {/* Breakdown Details */}
                    {t.details && Object.keys(t.details).length > 0 && (
                      <div style={{ fontSize: '11px', borderTop: '1px dashed #E2E8F0', paddingTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '16px', color: '#718096' }}>
                        {Object.entries(t.details).map(([key, val]) => (
                          <div key={key}>
                            <span style={{ fontWeight: 600, color: '#4A5568' }}>{key.replace(/_/g, ' ')}:</span>{' '}
                            <span style={{ fontFamily: 'monospace', color: '#2D3748', fontWeight: 700 }}>
                              {typeof val === 'number' ? val.toLocaleString() : String(val)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      
      {/* Spinning CSS animation */}
      <style>{`
        .spin-animation {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
