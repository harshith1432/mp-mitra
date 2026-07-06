import React, { useState } from 'react';
import {
  auth, db, signInWithEmailAndPassword, createUserWithEmailAndPassword,
  signInWithPopup, googleProvider, doc, setDoc, getDoc
} from '../firebase';
import { Mail, Lock, User, RefreshCw, ArrowLeft, ChevronRight } from 'lucide-react';

export default function AuthScreen({ portal, onAuthSuccess, onBackToPortals }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const portalConfig = {
    citizen:  { title: 'Citizen Services Portal',  subtitle: 'Submit Development Suggestions & Track Resolutions', color: '#003B7A', bgColor: '#EEF3FA',  emoji: '👥', role: 'Citizen' },
    official: { title: 'MP Dashboard Portal',       subtitle: 'Constituency Digital Twin & AI Budget Planning',    color: '#FF6B1A', bgColor: '#FFF3EC',  emoji: '🏛️', role: 'MP' },
    officer:  { title: 'Officer Execution Portal',  subtitle: 'Project Compliance & Field Reporting Console',     color: '#138808', bgColor: '#EAF6EA',  emoji: '⚙️', role: 'Officer' },
    admin:    { title: 'Admin System Console',      subtitle: 'Dataset Ingestion & AI Pipeline Management',      color: '#C62B2B', bgColor: '#FDECEA',  emoji: '🛡️', role: 'Admin' },
  }[portal] || { title: 'MP Mitra Portal', subtitle: 'Government AI Platform', color: '#003B7A', bgColor: '#EEF3FA', emoji: '🇮🇳', role: 'Citizen' };

  const handleAuth = async (e) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true); setError('');
    try {
      let userCredential;
      if (isRegister) {
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          uid: userCredential.user.uid, email, displayName: displayName || email.split('@')[0],
          role: portalConfig.role, portal, createdAt: new Date().toISOString()
        });
      } else {
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      }
      const snap = await getDoc(doc(db, 'users', userCredential.user.uid));
      const userData = snap.exists() ? snap.data() : { uid: userCredential.user.uid, email, displayName: displayName || email.split('@')[0], role: portalConfig.role };
      onAuthSuccess(userData);
    } catch (err) {
      const msgs = {
        'auth/user-not-found': 'No account found with this email. Please register.',
        'auth/wrong-password': 'Incorrect password. Please try again.',
        'auth/email-already-in-use': 'An account with this email already exists.',
        'auth/weak-password': 'Password must be at least 6 characters.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/invalid-credential': 'Invalid credentials. Please check and try again.',
      };
      setError(msgs[err.code] || err.message);
    }
    setLoading(false);
  };

  const handleGoogle = async () => {
    setLoading(true); setError('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      const snap = await getDoc(doc(db, 'users', user.uid));
      if (!snap.exists()) {
        await setDoc(doc(db, 'users', user.uid), {
          uid: user.uid, email: user.email, displayName: user.displayName || user.email.split('@')[0],
          role: portalConfig.role, portal, createdAt: new Date().toISOString()
        });
      }
      const finalSnap = await getDoc(doc(db, 'users', user.uid));
      onAuthSuccess(finalSnap.exists() ? finalSnap.data() : { uid: user.uid, email: user.email, displayName: user.displayName, role: portalConfig.role });
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#F5F7FA', display: 'flex', flexDirection: 'column', fontFamily: 'Inter, sans-serif' }}>
      {/* Government Header */}
      <header style={{ background: '#003B7A' }}>
        <div className="gov-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 40px', height: '64px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', background: 'white', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>🇮🇳</div>
            <div>
              <div style={{ color: 'white', fontWeight: 800, fontSize: '18px', lineHeight: 1 }}>MP MITRA</div>
              <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.07em' }}>National AI Governance Intelligence Platform</div>
            </div>
          </div>
          <button onClick={onBackToPortals} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: 'white', padding: '8px 14px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
            <ArrowLeft size={14} /> Back to Portals
          </button>
        </div>
        <div style={{ display: 'flex', height: '3px' }}>
          <div style={{ flex: 1, background: '#FF6B1A' }} />
          <div style={{ flex: 1, background: '#FFFFFF' }} />
          <div style={{ flex: 1, background: '#138808' }} />
        </div>
      </header>

      {/* Breadcrumb */}
      <div className="gov-breadcrumb" style={{ background: 'white', borderBottom: '1px solid #DDE1E7', padding: '12px 40px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#6B6B6B' }}>
        <span style={{ color: '#003B7A', cursor: 'pointer' }} onClick={onBackToPortals}>Home</span>
        <ChevronRight size={12} />
        <span style={{ color: '#003B7A', cursor: 'pointer' }} onClick={onBackToPortals}>Portal Selection</span>
        <ChevronRight size={12} />
        <span style={{ fontWeight: 600, color: '#1a1a1a' }}>{portalConfig.title}</span>
      </div>

      {/* Main auth form */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 20px' }}>
        <div style={{ width: '100%', maxWidth: '440px' }}>
          {/* Portal badge */}
          <div style={{ background: 'white', border: `1.5px solid ${portalConfig.color}30`, borderRadius: '12px', padding: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '14px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', borderTop: `3px solid ${portalConfig.color}` }}>
            <div style={{ width: '48px', height: '48px', background: portalConfig.bgColor, borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', flexShrink: 0 }}>{portalConfig.emoji}</div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#1a1a1a', lineHeight: 1, fontFamily: 'Space Grotesk, sans-serif' }}>{portalConfig.title}</div>
              <div style={{ fontSize: '11px', color: '#6B6B6B', marginTop: '4px', lineHeight: 1.4 }}>{portalConfig.subtitle}</div>
            </div>
          </div>

          {/* Auth Card */}
          <div style={{ background: 'white', border: '1px solid #DDE1E7', borderRadius: '12px', padding: '32px', boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#1a1a1a', margin: '0 0 4px', fontFamily: 'Space Grotesk, sans-serif' }}>
              {isRegister ? 'Create Account' : 'Sign In'}
            </h2>
            <p style={{ fontSize: '13px', color: '#6B6B6B', margin: '0 0 24px' }}>
              {isRegister ? 'Register your credentials to access the portal.' : 'Enter your credentials to access your portal.'}
            </p>

            {error && (
              <div style={{ background: '#FDECEA', border: '1px solid #F5C0BD', borderRadius: '6px', padding: '12px 14px', marginBottom: '16px', fontSize: '13px', color: '#C62B2B', fontWeight: 500 }}>
                ⚠️ {error}
              </div>
            )}

            <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {isRegister && (
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6B6B6B', marginBottom: '6px' }}>Full Name</label>
                  <div style={{ position: 'relative' }}>
                    <User size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#999' }} />
                    <input type="text" value={displayName} onChange={e=>setDisplayName(e.target.value)} placeholder="Your full name" style={{ display: 'block', width: '100%', padding: '10px 14px 10px 36px', background: 'white', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', color: '#1a1a1a', fontFamily: 'Inter, sans-serif', outline: 'none', boxSizing: 'border-box' }} onFocus={e=>e.target.style.borderColor='#003B7A'} onBlur={e=>e.target.style.borderColor='#DDE1E7'} />
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6B6B6B', marginBottom: '6px' }}>Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#999' }} />
                  <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="your@email.com" style={{ display: 'block', width: '100%', padding: '10px 14px 10px 36px', background: 'white', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', color: '#1a1a1a', fontFamily: 'Inter, sans-serif', outline: 'none', boxSizing: 'border-box' }} onFocus={e=>e.target.style.borderColor='#003B7A'} onBlur={e=>e.target.style.borderColor='#DDE1E7'} />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6B6B6B', marginBottom: '6px' }}>Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#999' }} />
                  <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" style={{ display: 'block', width: '100%', padding: '10px 14px 10px 36px', background: 'white', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', color: '#1a1a1a', fontFamily: 'Inter, sans-serif', outline: 'none', boxSizing: 'border-box' }} onFocus={e=>e.target.style.borderColor='#003B7A'} onBlur={e=>e.target.style.borderColor='#DDE1E7'} />
                </div>
              </div>

              <button type="submit" disabled={loading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', width: '100%', padding: '12px', background: portalConfig.color, color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 700, cursor: 'pointer', fontFamily: 'Inter, sans-serif', opacity: loading ? 0.7 : 1, transition: 'opacity 0.2s' }}>
                {loading ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Processing...</> : (isRegister ? 'Create Account' : 'Sign In →')}
              </button>
            </form>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
              <div style={{ flex: 1, height: '1px', background: '#DDE1E7' }} />
              <span style={{ fontSize: '11px', color: '#999', fontWeight: 500 }}>OR</span>
              <div style={{ flex: 1, height: '1px', background: '#DDE1E7' }} />
            </div>

            <button onClick={handleGoogle} disabled={loading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', width: '100%', padding: '11px', background: 'white', color: '#1a1a1a', border: '1.5px solid #DDE1E7', borderRadius: '6px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif', transition: 'border-color 0.2s' }} onMouseEnter={e=>e.target.style.borderColor='#003B7A'} onMouseLeave={e=>e.target.style.borderColor='#DDE1E7'}>
              <svg width="18" height="18" viewBox="0 0 18 18"><path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/><path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"/><path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/><path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/></svg>
              Continue with Google
            </button>

            <p style={{ textAlign: 'center', fontSize: '13px', color: '#6B6B6B', marginTop: '20px' }}>
              {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button onClick={()=>{setIsRegister(!isRegister);setError('');}} style={{ color: portalConfig.color, background: 'none', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '13px', fontFamily: 'Inter, sans-serif' }}>
                {isRegister ? 'Sign In' : 'Register'}
              </button>
            </p>
          </div>

          {/* Security note */}
          <div style={{ marginTop: '16px', padding: '12px 16px', background: 'white', border: '1px solid #DDE1E7', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '16px' }}>🔒</span>
            <span style={{ fontSize: '11px', color: '#6B6B6B', lineHeight: 1.5 }}>Your login is secured by <strong style={{ color: '#003B7A' }}>Firebase Authentication</strong>. MP Mitra is a Government of India Digital India initiative.</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="gov-footer" style={{ background: '#003B7A', padding: '16px 40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px' }}>© 2026 MP Mitra — Government of India Initiative</div>
          <div style={{ display: 'flex', gap: '20px' }}>
            {['Help','Privacy Policy','Contact'].map(l=><span key={l} style={{ color: 'rgba(255,255,255,0.6)', fontSize: '11px', cursor: 'pointer' }}>{l}</span>)}
          </div>
        </div>
      </footer>
    </div>
  );
}
