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
      <AutoTranslator lang={lang} />
    </LanguageContext.Provider>
  );
}

// ── AUTOMATIC SITE-WIDE TRANSLATOR ───────────────────────────────────────────
// Translates any visible English text node and input placeholder on the fly
// when a non-English language is selected. Uses localStorage caching for speed.
function AutoTranslator({ lang }) {
  useEffect(() => {
    if (!lang || lang === 'en') return;

    const translateText = async (text) => {
      const trimmed = text.trim();
      if (!trimmed || trimmed.length < 2) return null;
      
      // Skip numbers, percentages, dates, phone numbers, and currencies
      if (/^[0-9\s%/\-+.,:()₹$]+$/.test(trimmed)) return null;

      const cacheKey = `tr::${lang}::${trimmed}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) return cached;

      try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=${lang}&dt=t&q=${encodeURIComponent(trimmed)}`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (data && data[0]) {
            const translated = data[0].map(x => x[0]).join('');
            if (translated && translated.trim()) {
              localStorage.setItem(cacheKey, translated.trim());
              return translated.trim();
            }
          }
        }
      } catch (err) {
        console.warn("[AutoTranslator] Error translating:", trimmed, err);
      }
      return null;
    };

    const handleNode = async (node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const val = node.nodeValue;
        if (val && val.trim().length > 1) {
          const trans = await translateText(val);
          if (trans && node.nodeValue === val) { // Ensure node content hasn't changed since request
            node.nodeValue = val.replace(val.trim(), trans);
          }
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const tag = node.tagName.toLowerCase();
        if (tag === 'script' || tag === 'style' || tag === 'textarea' || tag === 'code') return;
        if (node.closest && (node.closest('.no-translate') || node.closest('.leaflet-container'))) return;

        // Translate placeholders
        if (tag === 'input' || tag === 'textarea') {
          const placeholder = node.getAttribute('placeholder');
          if (placeholder && placeholder.trim().length > 1) {
            const trans = await translateText(placeholder);
            if (trans) node.setAttribute('placeholder', trans);
          }
        }

        // Walk child nodes
        node.childNodes.forEach(handleNode);
      }
    };

    // Initial translation pass
    document.body.childNodes.forEach(handleNode);

    // Dynamic Mutation Observer to catch newly loaded or dynamic content
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach(handleNode);
        
        // Handle text changes in existing text nodes
        if (mutation.type === 'characterData') {
          const node = mutation.target;
          const val = node.nodeValue;
          // Avoid translation loop by verifying if it's already translated
          const cacheKey = `tr::${lang}::${val ? val.trim() : ''}`;
          if (val && val.trim().length > 1 && !localStorage.getItem(cacheKey)) {
            // Ensure we aren't translating a string that's already in the target language
            translateText(val).then(trans => {
              if (trans && node.nodeValue === val) {
                node.nodeValue = val.replace(val.trim(), trans);
              }
            });
          }
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });

    return () => observer.disconnect();
  }, [lang]);

  return null;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used inside <LanguageProvider>');
  return ctx;
}
