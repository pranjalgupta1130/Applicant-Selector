const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

const DATA_DIR = path.join(__dirname, '../../data');

/**
 * Generate a valid 24-character hexadecimal ID string (compatible with MongoDB ObjectId formats)
 */
const generateId = () => {
  return crypto.randomBytes(12).toString('hex');
};

/**
 * Validate whether a given string is a valid 24-character hexadecimal ID
 */
const isValidId = (id) => {
  if (typeof id !== 'string') return false;
  return /^[0-9a-fA-F]{24}$/.test(id);
};

// Simple async lock mechanism to handle concurrent write operations
const fileLocks = {};

const acquireLock = async (filePath) => {
  while (fileLocks[filePath]) {
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  fileLocks[filePath] = true;
};

const releaseLock = (filePath) => {
  delete fileLocks[filePath];
};

/**
 * Ensure storage directory and JSON files exist
 */
const ensureStorage = async () => {
  try {
    await fs.mkdir(DATA_DIR, { recursive: true });
  } catch (err) {
    if (err.code !== 'EEXIST') throw err;
  }
};

/**
 * Read collection data asynchronously
 */
const readCollection = async (collectionName) => {
  await ensureStorage();
  const filePath = path.join(DATA_DIR, `${collectionName}.json`);
  
  await acquireLock(filePath);
  try {
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (err) {
    if (err.code === 'ENOENT') {
      await fs.writeFile(filePath, JSON.stringify([]), 'utf8');
      return [];
    }
    throw err;
  } finally {
    releaseLock(filePath);
  }
};

/**
 * Write collection data asynchronously (atomic write)
 */
const writeCollection = async (collectionName, items) => {
  await ensureStorage();
  const filePath = path.join(DATA_DIR, `${collectionName}.json`);
  const tempPath = path.join(DATA_DIR, `${collectionName}.tmp.${Date.now()}`);

  await acquireLock(filePath);
  try {
    await fs.writeFile(tempPath, JSON.stringify(items, null, 2), 'utf8');
    await fs.rename(tempPath, filePath);
  } finally {
    releaseLock(filePath);
  }
};

module.exports = {
  generateId,
  isValidId,
  ensureStorage,
  readCollection,
  writeCollection
};
