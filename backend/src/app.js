const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const dotenv = require('dotenv');
const healthRoutes = require('./routes/health.routes');
const roleRoutes = require('./routes/role.routes');
const candidateRoutes = require('./routes/candidate.routes');
const interviewRoutes = require('./routes/interview.routes');
const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

// Load environment variables
dotenv.config();

const app = express();

// HTTP Request Logging Middleware (morgan 'dev' format logs method, url, status, response-time)
app.use(morgan('dev'));

// CORS Configuration
const corsOrigin = process.env.CORS_ORIGIN || '*';
app.use(cors({
  origin: corsOrigin,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Body Parser Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Mount API Routes
app.use('/api', healthRoutes);
app.use('/api/roles', roleRoutes);
app.use('/api/candidates', candidateRoutes);
app.use('/api/interviews', interviewRoutes);

// 404 Handler for Unmatched Routes
app.use(notFoundHandler);

// Centralized Error Handling Middleware
app.use(errorHandler);

module.exports = app;
