import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut,
  signInWithPopup,
  setPersistence,
  browserSessionPersistence
} from 'firebase/auth';
import { 
  getFirestore, 
  collection, 
  doc, 
  setDoc, 
  getDoc,
  onSnapshot,
  addDoc,
  query,
  where,
  orderBy,
  serverTimestamp
} from 'firebase/firestore';
import { 
  getStorage, 
  ref, 
  uploadBytes, 
  getDownloadURL 
} from 'firebase/storage';
import { getMessaging } from 'firebase/messaging';

// Centralized configurations securely bound to Vite environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Initialize Firebase App instance
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);

// ── PER-TAB AUTH ISOLATION ───────────────────────────────────────────────────
// Use browserSessionPersistence so each browser tab has its own independent
// Firebase auth session stored in sessionStorage. Logging into a different
// account in Tab B will NOT affect Tab A (and vice-versa). Each tab can hold
// a completely different user (MP, Admin, Citizen, Officer) simultaneously.
setPersistence(auth, browserSessionPersistence).catch(console.error);
// ─────────────────────────────────────────────────────────────────────────────

export const googleProvider = new GoogleAuthProvider();

export const db = getFirestore(app, 'default');
export const storage = getStorage(app);

let messaging = null;
try {
  messaging = getMessaging(app);
} catch (e) {
  console.warn("Firebase Cloud Messaging is not supported or permission is denied in this browser context:", e);
}

export { 
  messaging, 
  collection, 
  doc, 
  setDoc, 
  getDoc, 
  onSnapshot, 
  addDoc, 
  query, 
  where, 
  orderBy, 
  serverTimestamp,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  signInWithPopup,
  setPersistence,
  browserSessionPersistence
};
export default app;
