/**
 * 404 Not Found Middleware for unknown routes.
 */
const notFoundHandler = (req, res, next) => {
  const error = new Error(`Route Not Found - ${req.method} ${req.originalUrl}`);
  res.status(404);
  next(error);
};

/**
 * Centralized JSON Error Handling Middleware.
 * Handles syntax errors (e.g. malformed JSON payloads) and application errors cleanly.
 */
const errorHandler = (err, req, res, next) => {
  // Handle JSON parse errors from body-parser
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({
      error: 'Malformed JSON Payload',
      message: 'The request payload contains invalid JSON syntax.',
      status: 400
    });
  }

  const statusCode = res.statusCode === 200 ? (err.statusCode || 500) : res.statusCode;

  res.status(statusCode).json({
    error: statusCode === 404 ? 'Not Found' : 'Internal Server Error',
    message: err.message || 'An unexpected error occurred.',
    status: statusCode,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
};

module.exports = {
  notFoundHandler,
  errorHandler
};
