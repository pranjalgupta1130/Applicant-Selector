const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'interview_questions';

class InterviewQuestion {
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
      interviewId: doc.interviewId || null,
      questionId: doc.questionId || '',
      text: doc.text ? String(doc.text).trim() : '',
      stage: doc.stage || 'ice_breaker',
      competency: doc.competency ? String(doc.competency).trim() : '',
      difficulty: doc.difficulty !== undefined ? Number(doc.difficulty) : 3,
      expectedConcepts: Array.isArray(doc.expectedConcepts) ? doc.expectedConcepts : [],
      relevanceScore: doc.relevanceScore !== undefined ? Number(doc.relevanceScore) : 0,
      sequence: doc.sequence !== undefined ? Number(doc.sequence) : 1,
      generated: doc.generated !== undefined ? Boolean(doc.generated) : true,
      rubric: doc.rubric || null,
      sourceChunkIds: Array.isArray(doc.sourceChunkIds) ? doc.sourceChunkIds : [],
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }
}

module.exports = InterviewQuestion;
