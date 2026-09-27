const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'reports';

class Report {
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
    const items = await readCollection(COLLECTION);
    return items.find((item) => {
      for (const key in query) {
        if (item[key] !== query[key]) return false;
      }
      return true;
    }) || null;
  }

  static async create(doc) {
    const items = await readCollection(COLLECTION);
    const now = new Date().toISOString();
    const newItem = {
      _id: generateId(),
      interviewId: doc.interviewId || null,
      overallScore: doc.overallScore !== undefined ? Number(doc.overallScore) : 0,
      competencyScores: Array.isArray(doc.competencyScores) ? doc.competencyScores : [],
      strengths: Array.isArray(doc.strengths) ? doc.strengths : [],
      gaps: Array.isArray(doc.gaps) ? doc.gaps : [],
      recommendations: Array.isArray(doc.recommendations) ? doc.recommendations : [],
      scorecard: doc.scorecard || null,
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }
}

module.exports = Report;
