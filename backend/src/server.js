const dotenv = require('dotenv');
const app = require('./app');
const connectDB = require('./config/db');

// Load environment variables
dotenv.config();

const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Start HTTP server immediately so health check routes work regardless of DB status
const server = app.listen(PORT, async () => {
  console.log(`==================================================`);
  console.log(` BoardRoom AI Backend Server Started              `);
  console.log(` Port: ${PORT}                                    `);
  console.log(` Environment: ${NODE_ENV}                         `);
  console.log(` Health Check: http://localhost:${PORT}/api/health`);
  console.log(`==================================================`);

  // Attempt async MongoDB connection
  if (process.env.MONGODB_URI) {
    try {
      await connectDB();
    } catch (err) {
      console.warn('[Server Warning] Database connection failed on startup. DB-dependent endpoints will be unavailable until MongoDB is connected.');
    }
  }
});

// Graceful Shutdown Handler
process.on('SIGTERM', () => {
  console.log('[Server] SIGTERM received. Shutting down gracefully...');
  server.close(() => {
    console.log('[Server] Process terminated.');
  });
});
