const { Role, Competency } = require('../models');
const { isValidId } = require('../storage/jsonStore');

/**
 * Service: Create a new Role
 */
const createRole = async (roleData) => {
  const { title, description, difficulty, competencies } = roleData;

  if (!title || typeof title !== 'string' || !title.trim()) {
    const err = new Error('Role title is required');
    err.statusCode = 400;
    throw err;
  }

  if (!description || typeof description !== 'string' || !description.trim()) {
    const err = new Error('Role description is required');
    err.statusCode = 400;
    throw err;
  }

  if (difficulty !== undefined) {
    const diffNum = Number(difficulty);
    if (isNaN(diffNum) || diffNum < 1 || diffNum > 5) {
      const err = new Error('Role difficulty must be an integer between 1 and 5');
      err.statusCode = 400;
      throw err;
    }
  }

  if (competencies !== undefined && !Array.isArray(competencies)) {
    const err = new Error('Competencies must be an array of competency IDs');
    err.statusCode = 400;
    throw err;
  }

  // Validate competency IDs if provided
  if (competencies && competencies.length > 0) {
    for (const compId of competencies) {
      if (!isValidId(compId)) {
        const err = new Error(`Invalid competency ID format: ${compId}`);
        err.statusCode = 400;
        throw err;
      }
      const compExists = await Competency.exists({ _id: compId });
      if (!compExists) {
        const err = new Error(`Competency with ID ${compId} does not exist`);
        err.statusCode = 400;
        throw err;
      }
    }
  }

  const newRole = await Role.create({
    title: title.trim(),
    description: description.trim(),
    difficulty: difficulty ? Number(difficulty) : 3,
    competencies: competencies || []
  });

  return await newRole.populate('competencies');
};

/**
 * Service: Get Role by ID
 */
const getRoleById = async (id) => {
  if (!isValidId(id)) {
    const err = new Error(`Invalid role ID format: ${id}`);
    err.statusCode = 400;
    throw err;
  }

  const role = await Role.findById(id).populate('competencies');

  if (!role) {
    const err = new Error(`Role not found with ID: ${id}`);
    err.statusCode = 404;
    throw err;
  }

  return role;
};

/**
 * Service: Get All Active Roles
 */
const getAllRoles = async () => {
  return await Role.find({ isActive: true }).populate('competencies');
};

module.exports = {
  createRole,
  getRoleById,
  getAllRoles
};
