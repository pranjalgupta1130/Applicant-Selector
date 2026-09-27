const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'competencies';

class Competency {
  static async find(query = {}) {
    const items = await readCollection(COLLECTION);
    return items.filter((item) => {
      for (const key in query) {
        if (item[key] !== query[key]) return false;
      }
      return true;
    });
  }

  static async findById(id) {
    const items = await readCollection(COLLECTION);
    return items.find((item) => item._id === id || item.id === id) || null;
  }

  static async findOne(query = {}) {
    const results = await this.find(query);
    return results[0] || null;
  }

  static async exists(query = {}) {
    const item = await this.findOne(query);
    return !!item;
  }

  static async create(doc) {
    const items = await readCollection(COLLECTION);
    const now = new Date().toISOString();
    const newItem = {
      _id: generateId(),
      name: doc.name ? String(doc.name).trim() : '',
      description: doc.description ? String(doc.description).trim() : '',
      category: doc.category ? String(doc.category).trim() : 'technical',
      weight: doc.weight !== undefined ? Number(doc.weight) : 1.0,
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }

  static async findOneAndUpdate(query, updateData, options = {}) {
    const items = await readCollection(COLLECTION);
    const index = items.findIndex((item) => {
      for (const key in query) {
        if (item[key] !== query[key]) return false;
      }
      return true;
    });

    const now = new Date().toISOString();

    if (index !== -1) {
      items[index] = {
        ...items[index],
        ...updateData,
        updatedAt: now
      };
      await writeCollection(COLLECTION, items);
      return items[index];
    } else if (options.upsert) {
      const newItem = {
        _id: generateId(),
        name: updateData.name || query.name || '',
        description: updateData.description || '',
        category: updateData.category || 'technical',
        weight: updateData.weight !== undefined ? Number(updateData.weight) : 1.0,
        createdAt: now,
        updatedAt: now,
        ...updateData
      };
      items.push(newItem);
      await writeCollection(COLLECTION, items);
      return newItem;
    }

    return null;
  }
}

module.exports = Competency;
