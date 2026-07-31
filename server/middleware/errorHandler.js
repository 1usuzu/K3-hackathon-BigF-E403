/**
 * Global Error Handling Middleware for Express
 */
function errorHandler(err, req, res, next) {
    console.error('[ServerError]', err.stack || err.message || err);
    
    const statusCode = res.statusCode !== 200 ? res.statusCode : 500;
    res.status(statusCode).json({
        success: false,
        error: err.message || 'Internal Server Error',
        stack: process.env.NODE_ENV === 'production' ? null : err.stack
    });
}

module.exports = errorHandler;
