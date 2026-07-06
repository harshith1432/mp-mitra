import React, { useState, useEffect, useRef } from 'react';
import { Send, Image, MapPin, Mic, MoreVertical, Check, CheckCheck } from 'lucide-react';
import API_BASE from '../apiConfig';

export default function WhatsAppSimulator() {
  const [phone, setPhone] = useState('+91 99800 12345');
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      type: 'text',
      body: '👋 *Welcome to MP MITRA AI Platform!* Send any message to begin our conversation.',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const [selectedState, setSelectedState] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [stateList, setStateList] = useState([]);
  const [districtList, setDistrictList] = useState([]);
  const [blockList, setBlockList] = useState([]);
  const [villageList, setVillageList] = useState([]);

  // API_BASE imported from apiConfig.js

  // Fetch States on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/constituency/states`)
      .then(res => res.json())
      .then(data => {
        if (data.states) setStateList(data.states);
      })
      .catch(err => console.error("Error fetching states:", err));
  }, [API_BASE]);

  // Fetch Districts when selectedState changes
  useEffect(() => {
    if (!selectedState) {
      setDistrictList([]);
      return;
    }
    fetch(`${API_BASE}/api/constituency/districts?state=${encodeURIComponent(selectedState)}`)
      .then(res => res.json())
      .then(data => {
        if (data.districts) setDistrictList(data.districts);
      })
      .catch(err => console.error("Error fetching districts:", err));
  }, [selectedState, API_BASE]);

  // Fetch Blocks and Villages when selectedDistrict changes
  useEffect(() => {
    if (!selectedState || !selectedDistrict) {
      setBlockList([]);
      setVillageList([]);
      return;
    }
    fetch(`${API_BASE}/api/constituency/blocks?state=${encodeURIComponent(selectedState)}&district=${encodeURIComponent(selectedDistrict)}`)
      .then(res => res.json())
      .then(data => {
        if (data.blocks) setBlockList(data.blocks);
      })
      .catch(err => console.error("Error fetching blocks:", err));

    fetch(`${API_BASE}/api/constituency/villages?state=${encodeURIComponent(selectedState)}&district=${encodeURIComponent(selectedDistrict)}`)
      .then(res => res.json())
      .then(data => {
        if (data.villages) setVillageList(data.villages);
      })
      .catch(err => console.error("Error fetching villages:", err));
  }, [selectedState, selectedDistrict, API_BASE]);

  // Helper to determine the current location selection step based on last bot message
  const getGeoStep = () => {
    const botMsgs = messages.filter(m => m.sender === 'bot');
    if (botMsgs.length === 0) return null;
    const lastMsg = botMsgs[botMsgs.length - 1];
    const body = lastMsg.body || '';

    if (body.includes('*State* first') || body.includes('select your *State*')) {
      return 'state';
    }
    if (body.includes('*District* name') || body.includes('enter your *District*')) {
      return 'district';
    }
    if (body.includes('*Block / Taluk* name') || body.includes('enter your *Block*')) {
      return 'taluk';
    }
    if (body.includes('*Village / Town* name') || body.includes('enter your *Village*')) {
      return 'village';
    }
    return null;
  };

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Poll for bot messages
  const startPolling = (targetPhone) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    pollIntervalRef.current = setInterval(() => {
      fetch(`${API_BASE}/api/whatsapp/simulator/messages?phone=${encodeURIComponent(targetPhone)}`)
        .then(res => res.json())
        .then(data => {
          if (data.messages && data.messages.length > 0) {
            setIsTyping(false);
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            const newMsgs = data.messages.map(m => {
              if (m.type === 'typing') {
                setIsTyping(true);
                return null;
              }
              return {
                sender: 'bot',
                type: m.type,
                body: m.body || m.text?.body || '',
                buttons: m.buttons || [],
                sections: m.sections || [],
                media_url: m.media_url || '',
                caption: m.caption || '',
                time: time
              };
            }).filter(Boolean);

            if (newMsgs.length > 0) {
              setMessages(prev => [...prev, ...newMsgs]);
            }
          }
        })
        .catch(err => console.error('[Polling Error]', err));
    }, 1500);
  };

  useEffect(() => {
    startPolling(phone);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [phone]);

  const sendMessage = (type = 'text', content = '', extra = {}) => {
    if (type === 'text' && !content.trim()) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      sender: 'citizen',
      type: type,
      body: type === 'text' ? content : '',
      time: time,
      ...extra
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    // Call backend simulator endpoint
    fetch(`${API_BASE}/api/whatsapp/simulator/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone: phone,
        msg_type: type,
        content: content,
        ...extra
      })
    })
      .then(res => res.json())
      .catch(err => {
        console.error('[Send Error]', err);
        setIsTyping(false);
      });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', height: 'calc(100vh - 64px)', background: '#F0F2F5' }}>
      
      {/* Sidebar - Phone / Simulation Info */}
      <div style={{ background: 'white', borderRight: '1px solid #E9EDEF', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#003B7A', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>📱 WhatsApp Simulator</h3>
        <p style={{ fontSize: '12px', color: '#6B6B6B', lineHeight: 1.5, margin: 0 }}>
          Simulates a live citizen interaction on WhatsApp. Set the phone number to create different sessions.
        </p>

        <div>
          <label style={{ fontSize: '11px', fontWeight: 700, color: '#4A5568', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Citizen Phone Number</label>
          <input
            type="text"
            value={phone}
            onChange={e => {
              setPhone(e.target.value);
              setSelectedState('');
              setSelectedDistrict('');
              setMessages([{ sender: 'bot', type: 'text', body: '👋 Session reset. Send any message to start.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
            }}
            className="gov-input"
            style={{ width: '100%', fontSize: '13px' }}
          />
        </div>

        <div style={{ flex: 1 }} />

        {/* Info Box */}
        <div style={{ background: '#EEF3FA', borderLeft: '3px solid #003B7A', padding: '12px', borderRadius: '4px' }}>
          <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#003B7A', margin: '0 0 6px 0' }}>💡 Demo Guidelines</h4>
          <ul style={{ fontSize: '11px', color: '#4A5568', paddingLeft: '14px', margin: 0, lineHeight: 1.6 }}>
            <li>Send greeting (e.g. <b>Namaste</b>) to trigger flow</li>
            <li>Select Kannada/Hindi to test multilingual AI</li>
            <li>Click <b>📍 Share Live Location</b> to test reverse-geocoding</li>
            <li>Type <b>DONE</b> to submit suggestions</li>
          </ul>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundImage: 'url("https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png")', backgroundRepeat: 'repeat' }}>
        
        {/* Chat Header */}
        <div style={{ background: '#F0F2F5', padding: '10px 16px', display: 'flex', alignItems: 'center', borderBottom: '1px solid #E9EDEF' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#00A884', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 800, fontSize: '16px', marginRight: '12px' }}>
            M
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#111B21' }}>MP MITRA AI Platform</div>
            <div style={{ fontSize: '11px', color: '#667781' }}>{isTyping ? 'typing...' : 'online'}</div>
          </div>
          <div style={{ marginLeft: 'auto', color: '#54656F' }}>
            <MoreVertical size={20} style={{ cursor: 'pointer' }} />
          </div>
        </div>

        {/* Message Log */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {messages.map((m, idx) => {
            const isBot = m.sender === 'bot';
            return (
              <div
                key={idx}
                style={{
                  alignSelf: isBot ? 'flex-start' : 'flex-end',
                  background: isBot ? '#FFFFFF' : '#D9FDD3',
                  borderRadius: '8px',
                  boxShadow: '0 1px 0.5px rgba(11,20,26,.13)',
                  padding: '8px 12px',
                  maxWidth: '65%',
                  minWidth: '80px',
                  position: 'relative'
                }}
              >
                {/* Media rendering */}
                {m.type === 'media' && m.media_url && (
                  <div style={{ marginBottom: '6px', borderRadius: '6px', overflow: 'hidden', border: '1px solid #E9EDEF' }}>
                    {m.media_url.endsWith('.pdf') || m.caption.includes('PDF') ? (
                      <div style={{ background: '#FFF0F0', padding: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '28px' }}>📄</span>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#C62B2B' }}>PDF Document Proposal</div>
                      </div>
                    ) : (
                      <img src={m.media_url} alt="WhatsApp upload" style={{ maxWidth: '100%', maxHeight: '200px', display: 'block' }} />
                    )}
                  </div>
                )}

                {/* Body Text (with bold markdown support) */}
                <div style={{ fontSize: '13.5px', color: '#111B21', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                  {m.body ? m.body.split('**').map((part, i) => i % 2 === 1 ? <strong key={i}>{part}</strong> : part) : m.caption}
                </div>

                {/* Reply Buttons (Meta/Interactive representation) */}
                {isBot && m.type === 'buttons' && m.buttons.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '10px', borderTop: '1px solid #F0F2F5', paddingTop: '8px' }}>
                    {m.buttons.map(b => (
                      <button
                        key={b.id}
                        onClick={() => sendMessage('text', b.title, { content: b.id })}
                        style={{ background: '#00A884', color: 'white', border: 'none', borderRadius: '18px', padding: '8px 14px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', textAlign: 'center', transition: 'opacity 0.2s' }}
                        onMouseOver={e => e.target.style.opacity = 0.9}
                        onMouseOut={e => e.target.style.opacity = 1}
                      >
                        {b.title}
                      </button>
                    ))}
                  </div>
                )}

                {/* List Pickers */}
                {isBot && m.type === 'list' && m.sections.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px', borderTop: '1px solid #F0F2F5', paddingTop: '8px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#8696A0', textTransform: 'uppercase' }}>{m.button_text || 'Options'}</div>
                    {m.sections.map((sec, sIdx) => (
                      <div key={sIdx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ fontSize: '10.5px', color: '#667781', fontWeight: 600 }}>{sec.title}</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {sec.rows.map(r => (
                            <button
                              key={r.id}
                              onClick={() => sendMessage('text', r.title, { content: r.id })}
                              style={{ background: '#EEF3FA', color: '#003B7A', border: '1px solid #BEE3F8', borderRadius: '14px', padding: '6px 12px', fontSize: '11.5px', fontWeight: 600, cursor: 'pointer' }}
                            >
                              {r.title}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Timestamp & Read ticks */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', fontSize: '10px', color: '#667781', marginTop: '4px', gap: '3px' }}>
                  <span>{m.time}</span>
                  {!isBot && <CheckCheck size={14} color="#53bdeb" />}
                </div>
              </div>
            );
          })}

          {isTyping && (
            <div style={{ alignSelf: 'flex-start', background: '#FFFFFF', borderRadius: '8px', padding: '8px 12px', boxShadow: '0 1px 0.5px rgba(11,20,26,.13)' }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center', height: '18px' }}>
                <span className="dot" style={{ width: '6px', height: '6px', background: '#8696A0', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both' }}></span>
                <span className="dot" style={{ width: '6px', height: '6px', background: '#8696A0', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both 0.2s' }}></span>
                <span className="dot" style={{ width: '6px', height: '6px', background: '#8696A0', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both 0.4s' }}></span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{ background: '#F0F2F5', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '10px', borderTop: '1px solid #E9EDEF' }}>
          
          {/* Action Triggers */}
          <div style={{ display: 'flex', gap: '8px', color: '#54656F' }}>
            <Image
              size={22}
              style={{ cursor: 'pointer' }}
              title="Simulate Photo Upload"
              onClick={() => {
                const urls = [
                  'https://images.unsplash.com/photo-1594913785162-e6785b49eed9?w=500', // damaged road
                  'https://images.unsplash.com/photo-1542013936693-8848e5744a9e?w=500'  // leak pipe
                ];
                const selected = urls[Math.floor(Math.random() * urls.length)];
                sendMessage('image', '', { media_url: selected });
              }}
            />
            <MapPin
              size={22}
              style={{ cursor: 'pointer', color: '#C62B2B' }}
              title="Share Live Location"
              onClick={() => sendMessage('location', '', { lat: 12.5218, lon: 76.8951 })}
            />
            <Mic
              size={22}
              style={{ cursor: 'pointer' }}
              title="Simulate Voice Note"
              onClick={() => sendMessage('audio', '', { media_url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3' })}
            />
          </div>

          {/* Text Input / Dropdown Selector */}
          {getGeoStep() ? (
            <SearchableDropdown
              options={
                getGeoStep() === 'state' ? stateList :
                getGeoStep() === 'district' ? districtList :
                getGeoStep() === 'taluk' ? blockList :
                getGeoStep() === 'village' ? villageList : []
              }
              value={inputText}
              onChange={val => {
                setInputText(val);
                if (getGeoStep() === 'state') {
                  const matched = stateList.find(s => s.toLowerCase() === val.toLowerCase());
                  if (matched) setSelectedState(matched);
                } else if (getGeoStep() === 'district') {
                  const matched = districtList.find(d => d.toLowerCase() === val.toLowerCase());
                  if (matched) setSelectedDistrict(matched);
                }
              }}
              placeholder={
                getGeoStep() === 'state' ? 'Type or select State...' :
                getGeoStep() === 'district' ? 'Type or select District...' :
                getGeoStep() === 'taluk' ? 'Type or select Block / Taluk...' :
                'Type or select Village...'
              }
            />
          ) : (
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendMessage('text', inputText); }}
              placeholder="Type a message..."
              style={{ flex: 1, border: 'none', padding: '9px 12px', borderRadius: '8px', background: 'white', outline: 'none', fontSize: '14px', color: '#111B21' }}
            />
          )}

          {/* Send Action */}
          <button
            onClick={() => sendMessage('text', inputText)}
            style={{ background: '#00A884', color: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
          >
            <Send size={18} />
          </button>
        </div>

        {/* Global Keyframe styles for simulated typing indicator */}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
          }
        `}} />

      </div>
    </div>
  );
}

function SearchableDropdown({ options, value, onChange, placeholder }) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter options based on search value
  const filteredOptions = options.filter(opt =>
    opt.toLowerCase().includes((value || '').toLowerCase())
  );

  return (
    <div ref={wrapperRef} style={{ position: 'relative', flex: 1 }}>
      <input
        type="text"
        placeholder={placeholder}
        value={value || ''}
        onFocus={() => setIsOpen(true)}
        onChange={e => {
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onKeyDown={e => {
          // If Enter is pressed, close the dropdown
          if (e.key === 'Enter') {
            setIsOpen(false);
          }
        }}
        style={{
          width: '100%',
          border: 'none',
          padding: '9px 12px',
          borderRadius: '8px',
          background: 'white',
          outline: 'none',
          fontSize: '14px',
          color: '#111B21'
        }}
      />
      {isOpen && filteredOptions.length > 0 && (
        <div style={{
          position: 'absolute',
          bottom: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #E9EDEF',
          borderRadius: '8px',
          boxShadow: '0 -4px 12px rgba(0,0,0,0.1)',
          maxHeight: '200px',
          overflowY: 'auto',
          zIndex: 1000,
          marginBottom: '4px'
        }}>
          {filteredOptions.map((opt, idx) => (
            <div
              key={idx}
              onClick={() => {
                onChange(opt);
                setIsOpen(false);
              }}
              style={{
                padding: '10px 14px',
                fontSize: '13.5px',
                color: '#111B21',
                cursor: 'pointer',
                borderBottom: '1px solid #F0F2F5',
                transition: 'background 0.2s',
                textAlign: 'left'
              }}
              onMouseOver={e => e.target.style.background = '#F0F2F5'}
              onMouseOut={e => e.target.style.background = 'white'}
            >
              {opt}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
