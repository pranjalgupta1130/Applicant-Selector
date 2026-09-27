const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'evaluations';

class Evaluation {
  static async find(query = {}) {
    const items = await readCollection(COLLECTION);
    return items.filter((item) => {
      for (const key in query) {
        if (item[key] !== query[key]) return false;
      }
      return true;
    });
  }

  static async findOne(query = {}) {
    const results = await this.find(query);
    return results[0] || null;
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
      answerId: doc.answerId || null,
      relevance: doc.relevance !== undefined ? Number(doc.relevance) : 0,
      technicalCorrectness: doc.technicalCorrectness !== undefined ? Number(doc.technicalCorrectness) : 0,
      completeness: doc.completeness !== undefined ? Number(doc.completeness) : 0,
      reasoning: doc.reasoning !== undefined ? Number(doc.reasoning) : 0,
      clarity: doc.clarity !== undefined ? Number(doc.clarity) : 0,
      total: doc.total !== undefined ? Number(doc.total) : 0,
      coveredConcepts: Array.isArray(doc.coveredConcepts) ? doc.coveredConcepts : [],
      missingConcepts: Array.isArray(doc.missingConcepts) ? doc.missingConcepts : [],
      feedback: doc.feedback ? String(doc.feedback).trim() : '',
      confidence: doc.confidence !== undefined ? Number(doc.confidence) : 1.0,
      nextQuestionStrategy: doc.nextQuestionStrategy ? String(doc.nextQuestionStrategy).trim() : '',
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }
}

module.exports = Evaluation;
