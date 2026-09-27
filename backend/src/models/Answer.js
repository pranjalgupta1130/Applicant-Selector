const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const COLLECTION = 'answers';

class Answer {
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
      interviewQuestionId: doc.interviewQuestionId || null,
      answerText: doc.answerText ? String(doc.answerText).trim() : '',
      transcript: doc.transcript ? String(doc.transcript).trim() : '',
      submittedAt: doc.submittedAt || now,
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);
    return newItem;
  }
}

module.exports = Answer;
