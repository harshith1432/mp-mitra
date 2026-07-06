import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ChevronRight } from 'lucide-react';

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

export default function ScraperConsole() {
  const API = '';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const WS = `${protocol}//${window.location.host}`;

  const [crawlerRunning, setCrawlerRunning] = useState(false);
  const [crawlerStage, setCrawlerStage] = useState('idle');
  const [crawlerItems, setCrawlerItems] = useState(0);
  const [crawlerScanned, setCrawlerScanned] = useState(0);
  const [crawlerRunId, setCrawlerRunId] = useState(null);
  const [crawlerLogs, setCrawlerLogs] = useState([]);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [dbStats, setDbStats] = useState({ schemes: 0, news: 0, tenders: 0 });
  const [filterLevel, setFilterLevel] = useState('ALL');
  
  const [runSchemesAdded, setRunSchemesAdded] = useState(0);
  const [runNewsAdded, setRunNewsAdded] = useState(0);
  const [runTendersAdded, setRunTendersAdded] = useState(0);
  
  const logBoxRef = useRef(null);
  const wsRef = useRef(null);
  const autoScroll = useRef(true);

  // Fetch DB stats
  const refreshStats = useCallback(() => {
    fetch(`${API}/api/admin/crawler/status`)
      .then(r => r.json())
      .then(d => {
        if (d.stats) setDbStats(d.stats);
      })
      .catch(() => {});
  }, [API]);

  // Fetch live status
  const refreshStatus = useCallback(() => {
    fetch(`${API}/api/admin/crawler/realtime-status`)
      .then(r => r.json())
      .then(d => {
        setCrawlerRunning(d.running);
        setCrawlerStage(d.current_stage || 'idle');
        setCrawlerItems(d.items_added || 0);
        setCrawlerScanned(d.items_scanned || 0);
        setCrawlerRunId(d.run_id || null);
        setRunSchemesAdded(d.schemes_added_run || 0);
        setRunNewsAdded(d.news_added_run || 0);
        setRunTendersAdded(d.tenders_added_run || 0);
      })
      .catch(() => {});
  }, [API]);

  // WebSocket connection
  const connectWS = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState < 2) return;
    const ws = new WebSocket(`${WS}/ws/crawler-logs`);
    wsRef.current = ws;
    setWsStatus('connecting');

    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => {
      setWsStatus('disconnected');
      setTimeout(connectWS, 4000); // auto-reconnect
    };
    ws.onerror = () => setWsStatus('error');
    ws.onmessage = (ev) => {
      try {
        const evt = JSON.parse(ev.data);
        if (evt.type === 'ping') return;
        setCrawlerLogs(prev => [...prev.slice(-499), evt]);
        
        if (evt.stats) {
          setDbStats({
            schemes: evt.stats.total_schemes || 0,
            news: evt.stats.total_news || 0,
            tenders: evt.stats.total_tenders || 0
          });
          setCrawlerItems(evt.stats.items_added || 0);
          setCrawlerScanned(evt.stats.items_scanned || 0);
          setRunSchemesAdded(evt.stats.schemes_added_run || 0);
          setRunNewsAdded(evt.stats.news_added_run || 0);
          setRunTendersAdded(evt.stats.tenders_added_run || 0);
        }
        
        if (evt.level === 'DATA' && evt.data) {
          refreshStats();
          refreshStatus();
        }
        if (evt.level === 'SYSTEM' && evt.message && evt.message.includes('stopped')) {
          setCrawlerRunning(false);
          setCrawlerStage('idle');
          refreshStats();
        }
      } catch (e) {}
    };
  }, [WS, refreshStats, refreshStatus]);

  useEffect(() => {
    refreshStats();
    refreshStatus();
    connectWS();
    const iv = setInterval(() => {
      refreshStats();
      refreshStatus();
    }, 10000);
    return () => {
      clearInterval(iv);
      if (wsRef.current) wsRef.current.close();
    };
  }, [refreshStats, refreshStatus, connectWS]);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll.current && logBoxRef.current) {
      logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight;
    }
  }, [crawlerLogs]);

  const handleStart = () => {
    fetch(`${API}/api/admin/crawler/start`, { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.run_id) {
          setCrawlerRunning(true);
          setCrawlerStage('starting');
          setCrawlerRunId(d.run_id);
        }
      })
      .catch(e => alert('Start failed: ' + e));
  };

  const handleStop = () => {
    fetch(`${API}/api/admin/crawler/stop`, { method: 'POST' })
      .then(() => {
        setCrawlerRunning(false);
        setCrawlerStage('stopping');
      })
      .catch(e => alert('Stop failed: ' + e));
  };

  const levelColor = { SUCCESS: '#68d391', WARNING: '#fbd38d', ERROR: '#fc8181', DATA: '#90cdf4', SYSTEM: '#718096', INFO: '#a0aec0' };
  const levelBg = { SUCCESS: 'rgba(104,211,145,0.08)', WARNING: 'rgba(251,211,141,0.08)', ERROR: 'rgba(252,129,129,0.08)', DATA: 'rgba(144,205,244,0.08)', SYSTEM: 'rgba(113,128,150,0.06)', INFO: 'transparent' };
  const stageLabel = { idle: '—', starting: 'Initializing…', stage1: 'Stage 1: Schemes', stage2: 'Stage 2: District News', stage3: 'Stage 3: Tenders', stage4: 'Stage 4: Topic Web Scraper', stage5: 'Stage 5: MyScheme', stopping: 'Stopping…' };

  const filteredLogs = filterLevel === 'ALL' ? crawlerLogs : crawlerLogs.filter(e => e.level === filterLevel);

  return (
    <>
      <GovPageBanner title="AI Web Scraper — Real-Time Console" subtitle={`Live WebSocket log stream from the BeautifulSoup crawler. Covers 36 States/UTs · 750+ Districts · ${new Date().getFullYear()}`} breadcrumbs={['Admin Console', 'AI Web Scraper']} />
      <div style={{ padding: '20px 24px', display: 'grid', gap: '16px' }}>

        {/* ── Status Bar ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: '10px' }}>
          {[
            { label: 'Crawler', value: crawlerRunning ? '🟢 Running' : '🔴 Idle', color: crawlerRunning ? '#138808' : '#C62B2B' },
            { label: 'Current Stage', value: stageLabel[crawlerStage] || crawlerStage, color: '#003B7A' },
            { label: 'Items Scanned', value: crawlerScanned.toLocaleString(), color: '#8696A0' },
            { label: 'Items Stored', value: crawlerItems.toLocaleString(), color: '#FF6B1A' },
            { label: 'Schemes in DB', value: (dbStats.total_schemes || dbStats.schemes || 0).toLocaleString(), color: '#003B7A' },
            { label: 'News in DB', value: (dbStats.total_news || dbStats.news || 0).toLocaleString(), color: '#138808' },
            { label: 'Tenders in DB', value: (dbStats.total_tenders || dbStats.tenders || 0).toLocaleString(), color: '#C62B2B' },
          ].map((s, i) => (
            <div key={i} className="gov-card" style={{ padding: '14px', textAlign: 'center', borderTop: `3px solid ${s.color}` }}>
              <div style={{ fontSize: '16px', fontWeight: 800, color: s.color, fontFamily: 'Space Grotesk,sans-serif' }}>{s.value}</div>
              <div style={{ fontSize: '10px', color: '#6B6B6B', fontWeight: 600, marginTop: '4px' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* ── Controls + WS Status ── */}
        <div className="gov-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: wsStatus === 'connected' ? '#138808' : wsStatus === 'connecting' ? '#FF6B1A' : '#C62B2B' }} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#6B6B6B' }}>WebSocket: {wsStatus}</span>
          </div>
          <div style={{ flex: 1 }} />
          {crawlerRunId && <span style={{ fontSize: '10px', color: '#6B6B6B', fontFamily: 'monospace' }}>Run ID: {crawlerRunId}</span>}
          <div style={{ display: 'flex', gap: '8px' }}>
            {['ALL', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'DATA', 'SYSTEM'].map(lvl => (
              <button key={lvl} onClick={() => setFilterLevel(lvl)} style={{
                padding: '4px 10px', fontSize: '10px', fontWeight: 700, borderRadius: '12px', border: '1px solid', cursor: 'pointer',
                background: filterLevel === lvl ? levelColor[lvl] || '#003B7A' : 'transparent',
                color: filterLevel === lvl ? '#000' : '#6B6B6B',
                borderColor: filterLevel === lvl ? levelColor[lvl] || '#003B7A' : '#DDE1E7'
              }}>{lvl}</button>
            ))}
          </div>
          <button
            disabled={crawlerRunning}
            onClick={handleStart}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: crawlerRunning ? '#DDE1E7' : '#138808', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 18px', fontWeight: 700, fontSize: '12px', cursor: crawlerRunning ? 'not-allowed' : 'pointer', opacity: crawlerRunning ? 0.6 : 1 }}
          >▶ Start Crawler</button>
          <button
            disabled={!crawlerRunning}
            onClick={handleStop}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: !crawlerRunning ? '#DDE1E7' : '#C62B2B', color: 'white', border: 'none', borderRadius: '6px', padding: '8px 18px', fontWeight: 700, fontSize: '12px', cursor: !crawlerRunning ? 'not-allowed' : 'pointer', opacity: !crawlerRunning ? 0.6 : 1 }}
          >⏹ Stop Crawler</button>
          <button onClick={() => setCrawlerLogs([])} style={{ background: 'transparent', border: '1px solid #DDE1E7', borderRadius: '6px', padding: '8px 14px', fontSize: '11px', fontWeight: 600, color: '#6B6B6B', cursor: 'pointer' }}>🗑 Clear</button>
        </div>

        {/* ── Ingestion Session Metrics (Current Run) ── */}
        <div className="gov-card" style={{ padding: '16px 20px', background: '#F8FAFC', border: '1px solid #DDE1E7', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #E2E8F0', paddingBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#003B7A', fontFamily: 'Space Grotesk, sans-serif' }}>📊 Current Ingestion Session Metrics (From Start to Stop)</span>
            {crawlerRunning && <span style={{ fontSize: '11px', color: '#138808', fontWeight: 700, animation: 'pulse 1.5s infinite' }}>● ACTIVE CRAWL SESSION</span>}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
            <div style={{ background: 'white', padding: '10px', borderRadius: '6px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#003B7A', fontFamily: 'Space Grotesk, sans-serif' }}>{runSchemesAdded}</div>
              <div style={{ fontSize: '9px', color: '#6B6B6B', textTransform: 'uppercase', fontWeight: 700, marginTop: '2px' }}>Schemes Ingested</div>
            </div>
            <div style={{ background: 'white', padding: '10px', borderRadius: '6px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#138808', fontFamily: 'Space Grotesk, sans-serif' }}>{runNewsAdded}</div>
              <div style={{ fontSize: '9px', color: '#6B6B6B', textTransform: 'uppercase', fontWeight: 700, marginTop: '2px' }}>News Ingested</div>
            </div>
            <div style={{ background: 'white', padding: '10px', borderRadius: '6px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#FF6B1A', fontFamily: 'Space Grotesk, sans-serif' }}>{runTendersAdded}</div>
              <div style={{ fontSize: '9px', color: '#6B6B6B', textTransform: 'uppercase', fontWeight: 700, marginTop: '2px' }}>Tenders Ingested</div>
            </div>
            <div style={{ background: '#FFF3EC', padding: '10px', borderRadius: '6px', border: '1px solid #FFD54F', textAlign: 'center' }}>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#FF6B1A', fontFamily: 'Space Grotesk, sans-serif' }}>{crawlerItems}</div>
              <div style={{ fontSize: '9px', color: '#744210', textTransform: 'uppercase', fontWeight: 700, marginTop: '2px' }}>Total Ingested (this run)</div>
            </div>
          </div>
        </div>

        {/* ── Live Log Terminal ── */}
        <div className="gov-card" style={{ padding: 0, overflow: 'hidden', border: '1px solid #1a2a3a' }}>
          <div style={{ background: '#0d1117', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '10px', borderBottom: '1px solid #1a2a3a' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff5f57' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#febc2e' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#28c840' }} />
            </div>
            <span style={{ color: '#6B6B6B', fontSize: '11px', fontFamily: 'monospace', flex: 1 }}>MP MITRA Crawler — Live Console</span>
            <span style={{ color: '#4a5568', fontSize: '10px', fontFamily: 'monospace' }}>{filteredLogs.length} events</span>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#6B6B6B', cursor: 'pointer' }}>
              <input type="checkbox" defaultChecked onChange={e => { autoScroll.current = e.target.checked; }} />
              Auto-scroll
            </label>
          </div>
          <div
            ref={logBoxRef}
            onScroll={e => { const el = e.target; autoScroll.current = (el.scrollHeight - el.scrollTop - el.clientHeight) < 40; }}
            style={{ background: '#0d1117', height: '420px', overflowY: 'auto', padding: '10px 16px', fontFamily: 'Consolas,Monaco,monospace', fontSize: '11.5px', lineHeight: '1.7' }}
          >
            {filteredLogs.length === 0 ? (
              <div style={{ color: '#4a5568', textAlign: 'center', marginTop: '60px', fontSize: '13px' }}>
                {wsStatus === 'connected' ? (
                  crawlerRunning ? '⏳ Crawler running — log events will appear here…' : '▶ Click "Start Crawler" to begin a real-time crawl run.'
                ) : '🔌 Connecting to WebSocket…'}
              </div>
            ) : filteredLogs.map((evt, i) => (
              <div key={evt.id || i} style={{ padding: '2px 0', borderBottom: '1px solid rgba(255,255,255,0.03)', background: levelBg[evt.level] || 'transparent', marginBottom: '1px', borderRadius: '2px' }}>
                <span style={{ color: '#4a5568', marginRight: '8px', fontSize: '10px', userSelect: 'none' }}>{evt.ts}</span>
                <span style={{ color: levelColor[evt.level] || '#a0aec0', fontWeight: evt.level === 'SUCCESS' || evt.level === 'ERROR' ? 700 : 400, marginRight: '6px', fontSize: '10px', textTransform: 'uppercase' }}>[{evt.level}]</span>
                <span style={{ color: '#718096', marginRight: '6px', fontSize: '10px' }}>[{evt.stage}]</span>
                <span style={{ color: levelColor[evt.level] || '#a0aec0' }}>{evt.message}</span>
                {evt.url && <span style={{ color: '#4299e1', marginLeft: '8px', fontSize: '10px', fontStyle: 'italic' }}>{evt.url}</span>}
                {evt.data && Object.keys(evt.data).length > 0 && (
                  <span style={{ color: '#68d391', marginLeft: '8px', fontSize: '10px' }}>
                    {Object.entries(evt.data).map(([k, v]) => `${k}=${v}`).join(' | ')}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── Recent DB snapshot ── */}
        <div className="gov-card" style={{ padding: '20px' }}>
          <div style={{ fontFamily: 'Space Grotesk,sans-serif', fontSize: '14px', fontWeight: 700, color: '#003B7A', marginBottom: '14px', paddingBottom: '8px', borderBottom: '1px solid #DDE1E7' }}>
            📦 Database Snapshot (Real-time Live Stats)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '12px', textAlign: 'center' }}>
            {[
              { icon: '📋', label: 'Schemes', val: (dbStats.total_schemes || dbStats.schemes || 0).toLocaleString(), color: '#003B7A' },
              { icon: '📰', label: 'News Articles', val: (dbStats.total_news || dbStats.news || 0).toLocaleString(), color: '#138808' },
              { icon: '🏗️', label: 'Tenders', val: (dbStats.total_tenders || dbStats.tenders || 0).toLocaleString(), color: '#FF6B1A' },
            ].map((s, i) => (
              <div key={i} style={{ padding: '16px', background: '#F5F7FA', borderRadius: '10px', border: '1px solid #DDE1E7' }}>
                <div style={{ fontSize: '22px', marginBottom: '6px' }}>{s.icon}</div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: s.color, fontFamily: 'Space Grotesk,sans-serif' }}>{s.val}</div>
                <div style={{ fontSize: '11px', color: '#6B6B6B', marginTop: '4px', fontWeight: 600 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </>
  );
}
