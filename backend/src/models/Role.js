const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');
const Competency = require('./Competency');

const COLLECTION = 'roles';

const populateRole = async (role) => {
  if (!role) return null;
  const competencies = [];
  if (Array.isArray(role.competencies)) {
    for (const compId of role.competencies) {
      if (typeof compId === 'object' && compId !== null) {
        competencies.push(compId);
      } else {
        const comp = await Competency.findById(compId);
        if (comp) competencies.push(comp);
      }
    }
  }
  return {
    ...role,
    competencies
  };
};

class RoleQueryHelper {
  constructor(queryPromise) {
    this.queryPromise = queryPromise;
    this.shouldPopulate = false;
  }

  populate(field) {
    if (field === 'competencies') {
      this.shouldPopulate = true;
    }
    return this;
  }

  sort(sortObj) {
    // Keep chainable interface
    return this;
  }

  async then(resolve, reject) {
    try {
      let result = await this.queryPromise;
      if (this.shouldPopulate) {
        if (Array.isArray(result)) {
          result = await Promise.all(result.map(populateRole));
        } else if (result) {
          result = await populateRole(result);
        }
      }
      resolve(result);
    } catch (err) {
      reject(err);
    }
  }
}

class Role {
  static find(query = {}) {
    const promise = (async () => {
      const items = await readCollection(COLLECTION);
      return items.filter((item) => {
        for (const key in query) {
          if (item[key] !== query[key]) return false;
        }
        return true;
      });
    })();
    return new RoleQueryHelper(promise);
  }

  static findById(id) {
    const promise = (async () => {
      const items = await readCollection(COLLECTION);
      return items.find((item) => item._id === id || item.id === id) || null;
    })();
    return new RoleQueryHelper(promise);
  }

  static async create(doc) {
    const items = await readCollection(COLLECTION);
    const now = new Date().toISOString();
    const newItem = {
      _id: generateId(),
      title: doc.title ? String(doc.title).trim() : '',
      description: doc.description ? String(doc.description).trim() : '',
      difficulty: doc.difficulty !== undefined ? Number(doc.difficulty) : 3,
      competencies: Array.isArray(doc.competencies) ? doc.competencies : [],
      isActive: doc.isActive !== undefined ? Boolean(doc.isActive) : true,
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    
    return {
      ...newItem,
      populate: async (field) => {
        if (field === 'competencies') return await populateRole(newItem);
        return newItem;
      }
    };
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
        title: updateData.title || query.title || '',
        description: updateData.description || '',
        difficulty: updateData.difficulty !== undefined ? Number(updateData.difficulty) : 3,
        competencies: Array.isArray(updateData.competencies) ? updateData.competencies : [],
        isActive: updateData.isActive !== undefined ? Boolean(updateData.isActive) : true,
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

module.exports = Role;
