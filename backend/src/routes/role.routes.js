const express = require('express');
const router = express.Router();
const roleController = require('../controllers/role.controller');

/**
 * @route   POST /api/roles
 * @desc    Create a new target job role
 * @access  Public
 */
router.post('/', roleController.createRole);

/**
 * @route   GET /api/roles
 * @desc    Fetch all active target job roles
 * @access  Public
 */
router.get('/', roleController.getAllRoles);

/**
 * @route   GET /api/roles/:id
 * @desc    Fetch single role details and populated competencies
 * @access  Public
 */
router.get('/:id', roleController.getRoleById);

module.exports = router;
