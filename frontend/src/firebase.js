import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { 
  getFirestore, 
  collection, 
  getDocs,
  enableIndexedDbPersistence,
  CACHE_SIZE_UNLIMITED,
  query,
  limit
} from 'firebase/firestore';
import apiKeys from './config/api_keys.json';

let app;
let auth;
let db;
let googleProvider;
let initialized = false;

// Getter function to ensure Firebase is initialized
const getDb = () => {
  if (!initialized) {
    throw new Error('Firebase not initialized');
  }
  return db;
};

const initializeFirebase = async () => {
  try {
    console.log('Initializing Firebase with config:', {
      projectId: apiKeys.firebase.projectId,
      authDomain: apiKeys.firebase.authDomain
    });

    // Initialize Firebase
    app = initializeApp(apiKeys.firebase);

    // Initialize Auth
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
    auth.useDeviceLanguage();

    // Initialize Firestore with settings
    const firestoreSettings = {
      cacheSizeBytes: CACHE_SIZE_UNLIMITED,
      experimentalForceLongPolling: true,
      experimentalAutoDetectLongPolling: true,
      useFetchStreams: false
    };

    db = getFirestore(app);

    // Verify Firestore initialization
    if (!db) {
      throw new Error('Firestore failed to initialize');
    }

    // Test Firestore connection with a simple query
    try {
      const testRef = collection(db, '_connection_test');
      await getDocs(query(testRef, limit(1)));
      console.log('Firestore connection verified');
    } catch (err) {
      console.warn('Firestore connection test failed:', err.message);
      // Don't throw here, as the app might still work with proper permissions
    }

    console.log('Firebase services initialized successfully');
    initialized = true;
    return true;
  } catch (error) {
    console.error('Error during Firebase initialization:', error);
    throw error;
  }
};

// Initialize Firebase
initializeFirebase().catch(error => {
  console.error('Failed to initialize Firebase:', error);
});

// Export initialized instances and getter
export { auth, getDb as db, googleProvider };
export default app;