import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import apiKeys from './config/api_keys.json';

let app;
let auth;
let db;
let googleProvider;

try {
  // Initialize Firebase
  app = initializeApp(apiKeys.firebase);

  // Get Auth and Firestore instances
  auth = getAuth(app);
  db = getFirestore(app);
  googleProvider = new GoogleAuthProvider();

  // Test the connection
  auth.useDeviceLanguage();
} catch (error) {
  console.error('Error initializing Firebase:', error);
}

// Export initialized instances
export { auth, db, googleProvider };
export default app;