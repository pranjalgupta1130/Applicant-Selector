const { ensureStorage } = require('../storage/jsonStore');

/**
 * Initialize local JSON data storage repository.
 * Replaces external MongoDB connection with lightweight local JSON storage.
 */
const connectDB = async () => {
  try {
    await ensureStorage();
    console.log('[Database] Local JSON Storage initialized successfully under backend/data/');
    return true;
  } catch (error) {
    console.error('[Database Error] Failed to initialize local JSON storage:', error.message);
    throw error;
  }
};

module.exports = connectDB;
