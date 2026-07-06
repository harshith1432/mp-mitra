/**
 * MP Mitra — Language Context
 * ============================
 * Provides a global t() translation function to all components.
 * Language selection is persisted in localStorage.
 * Supports all 22 official Indian languages + English.
 */
import React, { createContext, useContext, useState, useEffect } from 'react';

// Import all translation files
import en from '../translations/en.json';
import hi from '../translations/hi.json';
import kn from '../translations/kn.json';
import te from '../translations/te.json';
import ta from '../translations/ta.json';
import ml from '../translations/ml.json';
import mr from '../translations/mr.json';
import gu from '../translations/gu.json';
import bn from '../translations/bn.json';
import pa from '../translations/pa.json';
import ur from '../translations/ur.json';
import or_ from '../translations/or.json';
import as_ from '../translations/as.json';
import ne from '../translations/ne.json';
import sa from '../translations/sa.json';
import mai from '../translations/mai.json';
import doi from '../translations/doi.json';
import sd from '../translations/sd.json';
import kok from '../translations/kok.json';
import brx from '../translations/brx.json';
import mni from '../translations/mni.json';
import ks from '../translations/ks.json';
import sat from '../translations/sat.json';

const TRANSLATIONS = { en, hi, kn, te, ta, ml, mr, gu, bn, pa, ur, or: or_, as: as_, ne, sa, mai, doi, sd, kok, brx, mni, ks, sat };

export const SUPPORTED_LANGUAGES = [
  { code: 'en',  name: 'English',        english: 'English',     region: 'English',    rtl: false },
  // South India
  { code: 'kn',  name: 'ಕನ್ನಡ',          english: 'Kannada',     region: 'South India', rtl: false },
  { code: 'te',  name: 'తెలుగు',         english: 'Telugu',      region: 'South India', rtl: false },
  { code: 'ta',  name: 'தமிழ்',          english: 'Tamil',       region: 'South India', rtl: false },
  { code: 'ml',  name: 'മലയാളം',         english: 'Malayalam',   region: 'South India', rtl: false },
  { code: 'kok', name: 'कोंकणी',         english: 'Konkani',     region: 'South India', rtl: false },
  // North India
  { code: 'hi',  name: 'हिंदी',          english: 'Hindi',       region: 'North India', rtl: false },
  { code: 'pa',  name: 'ਪੰਜਾਬੀ',         english: 'Punjabi',     region: 'North India', rtl: false },
  { code: 'ur',  name: 'اردو',           english: 'Urdu',        region: 'North India', rtl: true  },
  { code: 'ks',  name: 'कॉशुर',          english: 'Kashmiri',    region: 'North India', rtl: true  },
  { code: 'doi', name: 'डोगरी',          english: 'Dogri',       region: 'North India', rtl: false },
  { code: 'sa',  name: 'संस्कृतम्',      english: 'Sanskrit',    region: 'North India', rtl: false },
  { code: 'ne',  name: 'नेपाली',         english: 'Nepali',      region: 'North India', rtl: false },
  { code: 'mai', name: 'मैथिली',         english: 'Maithili',    region: 'North India', rtl: false },
  { code: 'sd',  name: 'सिन्धी',         english: 'Sindhi',      region: 'North India', rtl: false },
  // West India
  { code: 'mr',  name: 'मराठी',          english: 'Marathi',     region: 'West India',  rtl: false },
  { code: 'gu',  name: 'ગુજરાતી',        english: 'Gujarati',    region: 'West India',  rtl: false },
  // East India
  { code: 'bn',  name: 'বাংলা',          english: 'Bengali',     region: 'East India',  rtl: false },
  { code: 'or',  name: 'ଓଡ଼ିଆ',          english: 'Odia',        region: 'East India',  rtl: false },
  { code: 'as',  name: 'অসমীয়া',        english: 'Assamese',    region: 'East India',  rtl: false },
  { code: 'sat', name: 'ᱥᱟᱱᱛᱟᱲᱤ',       english: 'Santali',     region: 'East India',  rtl: false },
  { code: 'mni', name: 'মৈতৈলোন্',       english: 'Manipuri',    region: 'East India',  rtl: false },
  { code: 'brx', name: 'बड़ो',           english: 'Bodo',        region: 'East India',  rtl: false },
];

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('mp_ui_lang') || 'en');

  useEffect(() => {
    const langDef = SUPPORTED_LANGUAGES.find(l => l.code === lang);
    document.documentElement.setAttribute('dir', langDef?.rtl ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
  }, [lang]);

  const changeLanguage = (code) => {
    setLang(code);
    localStorage.setItem('mp_ui_lang', code);
  };

  const t = (key, params = {}) => {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS['en'];
    let text = dict?.[key] ?? TRANSLATIONS['en']?.[key] ?? key;
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(new RegExp(`{{${k}}}`, 'g'), String(v));
    });
    return text;
  };

  const currentLangDef = SUPPORTED_LANGUAGES.find(l => l.code === lang) || SUPPORTED_LANGUAGES[0];

  return (
    <LanguageContext.Provider value={{ lang, changeLanguage, t, currentLangDef, SUPPORTED_LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used inside <LanguageProvider>');
  return ctx;
}
