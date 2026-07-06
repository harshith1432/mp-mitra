import React, { useState, useEffect } from 'react';
import { Database, RefreshCw, Download, Trash2, ShieldAlert, CheckCircle, Play, AlertTriangle, Settings, HelpCircle, HardDrive } from 'lucide-react';
import API_BASE from '../apiConfig';

export default function DatasetManagerConsole() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [editingConfig, setEditingConfig] = useState(false);
  
  // Form state
  const [provider, setProvider] = useState('default');
  const [providerUrl, setProviderUrl] = useState('');
  
  // Refresh data from API
  const refreshData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/datasets`);
      if (response.ok) {
        const json = await response.json();
        setData(json);
        setProvider(json.provider);
        setProviderUrl(json.provider_url);
        
        // Auto-refresh if download is running
        if (json.download_state && json.download_state.status !== 'idle' && json.download_state.status !== 'completed' && json.download_state.status !== 'failed') {
          setUpdating(true);
        } else {
          setUpdating(false);
        }
      }
    } catch (error) {
      console.error("Failed to load datasets:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Poll progress when downloading
  useEffect(() => {
    let timer;
    if (updating) {
      timer = setInterval(() => {
        refreshData();
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [updating]);

  const handleConfigure = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/api/datasets/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, provider_url: providerUrl })
      });
      if (response.ok) {
        setEditingConfig(false);
        refreshData();
      }
    } catch (err) {
      alert("Failed to update config: " + err.message);
    }
  };

  const handleUpdate = async (datasetId) => {
    try {
      const response = await fetch(`${API_BASE}/api/datasets/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId })
      });
      if (response.ok) {
        setUpdating(true);
        refreshData();
      }
    } catch (err) {
      alert("Failed to start download: " + err.message);
    }
  };

  const handleRepair = async (datasetId) => {
    if (!confirm("Are you sure you want to verify and re-download this dataset? Any local changes to the CSV files will be overwritten.")) {
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/datasets/repair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId })
      });
      if (response.ok) {
        setUpdating(true);
        refreshData();
      }
    } catch (err) {
      alert("Failed to repair dataset: " + err.message);
    }
  };

  const handleRemove = async (datasetId) => {
    if (!confirm("Are you sure you want to remove this dataset from local AppData directory? The application won't be able to query this data until re-installed.")) {
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/datasets/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId })
      });
      if (response.ok) {
        refreshData();
      }
    } catch (err) {
      alert("Failed to remove dataset: " + err.message);
    }
  };

  // Helper to format bytes
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'Inter, sans-serif' }}>
        <RefreshCw className="animate-spin" size={32} style={{ color: '#003B7A', margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Loading Dataset Environment...</h3>
      </div>
    );
  }

  const { datasets, datasets_dir, download_state } = data || {};
  const isDlActive = download_state && download_state.status !== 'idle' && download_state.status !== 'completed' && download_state.status !== 'failed';

  return (
    <div style={{ padding: '24px 28px', fontFamily: 'Inter, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* HEADER CONTROLS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#1a1a1a', letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={24} color="#003B7A" /> Intelligent Dataset Manager
          </h2>
          <p style={{ fontSize: '13px', color: '#6B6B6B', marginTop: '4px' }}>
            Verify, download, repair and configure the complete dataset repository for MP Mitra.
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setEditingConfig(!editingConfig)}
            className="gov-btn" 
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'white', border: '1px solid #DDE1E7', padding: '8px 14px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', borderRadius: '6px' }}
          >
            <Settings size={15} /> Configure Provider
          </button>
          
          <button 
            onClick={() => handleUpdate('all')}
            disabled={isDlActive}
            className="gov-btn gov-btn--blue" 
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', fontSize: '13px', fontWeight: 700, cursor: 'pointer', borderRadius: '6px', opacity: isDlActive ? 0.6 : 1 }}
          >
            <Download size={15} /> Update All Datasets
          </button>
        </div>
      </div>

      {/* STORAGE & DIRECTORY DETAILS BAR */}
      <div className="gov-card" style={{ padding: '12px 18px', background: '#F0F4F8', border: '1px solid #D1DCE5', borderRadius: '8px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: '#4A5568' }}>
        <HardDrive size={16} color="#003B7A" />
        <span style={{ fontWeight: 600, color: '#1A202C' }}>Dedicated Datasets Directory:</span>
        <code style={{ background: 'white', padding: '3px 8px', border: '1px solid #E2E8F0', borderRadius: '4px', fontFamily: 'Consolas, monospace', flex: 1, overflowX: 'auto', whiteSpace: 'nowrap' }}>{datasets_dir}</code>
      </div>

      {/* CONFIGURATION EDITOR */}
      {editingConfig && (
        <div className="gov-card" style={{ padding: '24px', marginBottom: '24px', border: '1.5px solid #003B7A', background: '#F8FAFC' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#003B7A', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Settings size={16} /> Dataset Cloud Provider Settings
          </h3>
          <form onSubmit={handleConfigure} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '14px', alignItems: 'end' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#4A5568' }}>Storage Provider</label>
              <select value={provider} onChange={e => setProvider(e.target.value)} className="gov-input" style={{ width: '100%', padding: '9px 12px', fontSize: '13px' }}>
                <option value="default">Default Repository</option>
                <option value="google_drive">Google Drive</option>
                <option value="gcs">Google Cloud Storage (GCS)</option>
                <option value="aws_s3">AWS S3</option>
                <option value="azure_blob">Azure Blob Storage</option>
                <option value="custom">Custom Web Host</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#4A5568' }}>Base Download URL / Manifest Endpoint</label>
              <input 
                type="text" 
                value={providerUrl} 
                onChange={e => setProviderUrl(e.target.value)} 
                className="gov-input" 
                placeholder="https://..."
                required
                style={{ width: '100%', padding: '8px 12px', fontSize: '13px' }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="submit" className="gov-btn gov-btn--blue" style={{ padding: '10px 18px', fontSize: '13px', fontWeight: 700, borderRadius: '6px', cursor: 'pointer' }}>Save Settings</button>
              <button type="button" onClick={() => setEditingConfig(false)} className="gov-btn" style={{ padding: '10px 14px', fontSize: '13px', border: '1px solid #DDE1E7', background: 'white', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* ACTIVE DOWNLOAD PANEL */}
      {isDlActive && (
        <div className="gov-card" style={{ padding: '24px', marginBottom: '24px', background: '#F8FAFC', border: '1px solid #BEE3F8', borderLeft: '5px solid #3182CE', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#2B6CB0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <RefreshCw className="animate-spin" size={15} /> 
              Active Operation: {download_state.status.toUpperCase()} — {download_state.current_dataset}
            </h4>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#4A5568' }}>
              Speed: {download_state.speed_kbps ? `${(download_state.speed_kbps / 1024).toFixed(2)} MB/s` : 'Calculating...'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '10px', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ height: '8px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
              <div 
                style={{ 
                  height: '100%', 
                  background: 'linear-gradient(90deg, #FF6B1A, #003B7A, #138808)', 
                  width: `${download_state.total_bytes ? (download_state.downloaded_bytes / download_state.total_bytes * 100) : 0}%`,
                  transition: 'width 0.3s ease'
                }} 
              />
            </div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#1A202C' }}>
              {download_state.total_bytes ? `${(download_state.downloaded_bytes / download_state.total_bytes * 100).toFixed(1)}%` : '0%'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#718096', fontWeight: 500 }}>
            <span>File: {download_state.current_file} ({formatBytes(download_state.downloaded_bytes)} / {formatBytes(download_state.total_bytes)})</span>
            <span>ETA: {download_state.eta_seconds ? `${Math.floor(download_state.eta_seconds / 60)}m ${download_state.eta_seconds % 60}s` : 'Unknown'} | Verification: {download_state.verification.toUpperCase()}</span>
          </div>
        </div>
      )}

      {/* COMPLETED/FAILED NOTIFICATION STATS */}
      {download_state && (download_state.status === 'completed' || download_state.status === 'failed') && (
        <div 
          className="gov-card" 
          style={{ 
            padding: '16px 20px', 
            marginBottom: '24px', 
            borderRadius: '8px',
            background: download_state.status === 'completed' ? '#F0FDF4' : '#FFF5F5',
            border: download_state.status === 'completed' ? '1px solid #DCFCE7' : '1px solid #FED7D7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {download_state.status === 'completed' ? (
              <CheckCircle size={20} color="#15803D" />
            ) : (
              <ShieldAlert size={20} color="#C53030" />
            )}
            <div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: download_state.status === 'completed' ? '#15803D' : '#9B2C2C' }}>
                {download_state.status === 'completed' ? 'All Datasets Synchronized Successfully!' : 'Dataset Operation Failed'}
              </div>
              <div style={{ fontSize: '11px', color: '#718096', marginTop: '2px' }}>
                {download_state.status === 'completed' ? 'The system is ready to launch. Database tables are validated.' : download_state.error}
              </div>
            </div>
          </div>
          
          <button 
            onClick={refreshData} 
            className="gov-btn" 
            style={{ fontSize: '11px', padding: '5px 10px', background: 'white', border: '1px solid #DDE1E7', borderRadius: '4px', cursor: 'pointer' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* DATASETS DIRECTORY TABLE */}
      <div className="gov-card" style={{ padding: '24px', overflowX: 'auto' }}>
        <table className="gov-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '2px solid #E2E8F0' }}>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096' }}>Dataset Details</th>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096' }}>Target Files</th>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096', textAlign: 'center' }}>Version</th>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096', textAlign: 'right' }}>Compressed Size</th>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096', textAlign: 'center' }}>Status</th>
              <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: '#718096', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {datasets && Object.entries(datasets).map(([id, info]) => {
              return (
                <tr key={id} style={{ borderBottom: '1px solid #EDF2F7', transition: 'background 0.2s' }}>
                  
                  {/* Name + Details */}
                  <td style={{ padding: '16px' }}>
                    <div style={{ fontWeight: 700, color: '#2D3748', fontSize: '13px' }}>{info.name}</div>
                    <div style={{ fontSize: '11px', color: '#718096', marginTop: '2px', fontFamily: 'Consolas, monospace' }}>ID: {id}</div>
                  </td>
                  
                  {/* Expected extracted CSV files */}
                  <td style={{ padding: '16px', fontSize: '12px', color: '#4A5568' }}>
                    {info.expected_files.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <code style={{ background: '#F7FAFC', border: '1px solid #E2E8F0', padding: '1px 5px', borderRadius: '3px', fontSize: '11px' }}>{f}</code>
                      </div>
                    ))}
                  </td>
                  
                  {/* Local version vs Cloud version */}
                  <td style={{ padding: '16px', fontSize: '12px', textAlign: 'center' }}>
                    <div style={{ fontWeight: 600 }}>{info.installed_version || '—'}</div>
                    {info.installed_version !== info.version && (
                      <div style={{ fontSize: '10px', color: '#DD6B20', marginTop: '2px' }}>Latest: {info.version}</div>
                    )}
                  </td>
                  
                  {/* File size */}
                  <td style={{ padding: '16px', fontSize: '12px', textAlign: 'right', fontWeight: 500, color: '#4A5568' }}>
                    {formatBytes(info.size)}
                  </td>
                  
                  {/* Status Indicator */}
                  <td style={{ padding: '16px', textAlign: 'center' }}>
                    {info.installed ? (
                      info.installed_version === info.version ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#C6F6D5', color: '#22543D', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
                          <CheckCircle size={11} /> Verified
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#FEEBC8', color: '#744210', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
                          <AlertTriangle size={11} /> Outdated
                        </span>
                      )
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#FED7D7', color: '#742A2A', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
                        <ShieldAlert size={11} /> Missing
                      </span>
                    )}
                  </td>
                  
                  {/* Action buttons */}
                  <td style={{ padding: '16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '8px' }}>
                      <button 
                        onClick={() => handleUpdate(id)}
                        disabled={isDlActive || (info.installed && info.installed_version === info.version)}
                        title="Download / Update Dataset"
                        style={{ 
                          padding: '6px', 
                          background: (info.installed && info.installed_version === info.version) ? '#E2E8F0' : '#EBF8FF', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: (info.installed && info.installed_version === info.version) ? 'not-allowed' : 'pointer',
                          color: (info.installed && info.installed_version === info.version) ? '#A0AEC0' : '#2B6CB0'
                        }}
                      >
                        <Download size={14} />
                      </button>
                      
                      <button 
                        onClick={() => handleRepair(id)}
                        disabled={isDlActive || !info.installed}
                        title="Repair / Re-download Dataset"
                        style={{ 
                          padding: '6px', 
                          background: !info.installed ? '#E2E8F0' : '#FEFCBF', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: !info.installed ? 'not-allowed' : 'pointer',
                          color: !info.installed ? '#A0AEC0' : '#B7791F'
                        }}
                      >
                        <RefreshCw size={14} />
                      </button>
                      
                      <button 
                        onClick={() => handleRemove(id)}
                        disabled={isDlActive || !info.installed}
                        title="Uninstall Dataset"
                        style={{ 
                          padding: '6px', 
                          background: !info.installed ? '#E2E8F0' : '#FFF5F5', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: !info.installed ? 'not-allowed' : 'pointer',
                          color: !info.installed ? '#A0AEC0' : '#E53E3E'
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                  
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}
