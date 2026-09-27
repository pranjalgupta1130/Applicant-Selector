const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');
const Candidate = require('./Candidate');
const Role = require('./Role');
const InterviewQuestion = require('./InterviewQuestion');

const COLLECTION = 'interviews';

const populateInterview = async (interview) => {
  if (!interview) return null;
  const candidateObj = interview.candidateId ? await Candidate.findById(typeof interview.candidateId === 'object' ? interview.candidateId._id : interview.candidateId) : null;
  const roleObj = interview.roleId ? await Role.findById(typeof interview.roleId === 'object' ? interview.roleId._id : interview.roleId) : null;
  const questionObj = interview.currentQuestionId ? await InterviewQuestion.findById(typeof interview.currentQuestionId === 'object' ? interview.currentQuestionId._id : interview.currentQuestionId) : null;

  const populatedRole = roleObj;

  return {
    ...interview,
    candidateId: candidateObj || interview.candidateId,
    roleId: populatedRole || interview.roleId,
    currentQuestionId: questionObj || interview.currentQuestionId,
    save: async function () {
      return await Interview.saveInstance(this);
    }
  };
};

class InterviewQueryHelper {
  constructor(queryPromise) {
    this.queryPromise = queryPromise;
    this.populateFields = [];
  }

  populate(field) {
    this.populateFields.push(field);
    return this;
  }

  async then(resolve, reject) {
    try {
      let result = await this.queryPromise;
      if (result && this.populateFields.length > 0) {
        result = await populateInterview(result);
      }
      resolve(result);
    } catch (err) {
      reject(err);
    }
  }
}

class Interview {
  static findById(id) {
    const promise = (async () => {
      const items = await readCollection(COLLECTION);
      const item = items.find((i) => i._id === id || i.id === id);
      if (!item) return null;
      return {
        ...item,
        save: async function () {
          return await Interview.saveInstance(this);
        }
      };
    })();
    return new InterviewQueryHelper(promise);
  }

  static async create(doc) {
    const items = await readCollection(COLLECTION);
    const now = new Date().toISOString();
    const newItem = {
      _id: generateId(),
      candidateId: typeof doc.candidateId === 'object' ? doc.candidateId._id : doc.candidateId,
      roleId: typeof doc.roleId === 'object' ? doc.roleId._id : doc.roleId,
      targetCompetencies: Array.isArray(doc.targetCompetencies) ? doc.targetCompetencies : [],
      status: doc.status || 'created',
      currentStage: doc.currentStage || 'ice_breaker',
      currentQuestionId: doc.currentQuestionId || null,
      questionSequence: doc.questionSequence !== undefined ? Number(doc.questionSequence) : 0,
      questionsAsked: doc.questionsAsked !== undefined ? Number(doc.questionsAsked) : 0,
      startedAt: doc.startedAt || null,
      completedAt: doc.completedAt || null,
      createdAt: now,
      updatedAt: now
    };
    items.push(newItem);
    await writeCollection(COLLECTION, items);

    return {
      ...newItem,
      save: async function () {
        return await Interview.saveInstance(this);
      }
    };
  }

  static async saveInstance(instance) {
    const items = await readCollection(COLLECTION);
    const index = items.findIndex((i) => i._id === instance._id || i.id === instance._id);

    const now = new Date().toISOString();
    const updatedData = {
      _id: instance._id,
      candidateId: typeof instance.candidateId === 'object' && instance.candidateId ? instance.candidateId._id : instance.candidateId,
      roleId: typeof instance.roleId === 'object' && instance.roleId ? instance.roleId._id : instance.roleId,
      targetCompetencies: instance.targetCompetencies || [],
      status: instance.status,
      currentStage: instance.currentStage,
      currentQuestionId: typeof instance.currentQuestionId === 'object' && instance.currentQuestionId ? instance.currentQuestionId._id : instance.currentQuestionId,
      questionSequence: instance.questionSequence,
      questionsAsked: instance.questionsAsked,
      startedAt: instance.startedAt,
      completedAt: instance.completedAt,
      createdAt: instance.createdAt || now,
      updatedAt: now
    };

    if (index !== -1) {
      items[index] = updatedData;
    } else {
      items.push(updatedData);
    }

    await writeCollection(COLLECTION, items);
    return updatedData;
  }
}

module.exports = Interview;
