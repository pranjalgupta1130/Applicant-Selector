const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'candidates';

class Candidate {
  static async findByEmail(email) {
    const normalized = String(email || '').trim().toLowerCase();
    if (!normalized) return null;
    const items = await readCollection(COLLECTION);
    return items.find((item) => String(item.email || '').trim().toLowerCase() === normalized) || null;
  }

  static async findById(id) {
    const items = await readCollection(COLLECTION);
    return items.find((item) => item._id === id || item.id === id) || null;
  }

  static async create(doc) {
    const items = await readCollection(COLLECTION);
    const now = new Date().toISOString();
    const newItem = {
      _id: generateId(),
      name: doc.name ? String(doc.name).trim() : '',
      email: doc.email ? String(doc.email).trim() : '',
      resumeUrl: doc.resumeUrl ? String(doc.resumeUrl).trim() : '',
      extractedSkills: Array.isArray(doc.extractedSkills) ? doc.extractedSkills : [],
      experience: doc.experience ? String(doc.experience).trim() : '',
      education: doc.education ? String(doc.education).trim() : '',
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }

  static async findByIdAndUpdate(id, updateData, options = {}) {
    const items = await readCollection(COLLECTION);
    const index = items.findIndex((item) => item._id === id || item.id === id);

    if (index === -1) return null;

    const now = new Date().toISOString();
    items[index] = {
      ...items[index],
      ...updateData,
      updatedAt: now
    };

    await writeCollection(COLLECTION, items);
    return items[index];
  }
}

module.exports = Candidate;
