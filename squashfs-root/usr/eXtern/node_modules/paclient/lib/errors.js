var C = 0;
var D = 0;
module.exports = {
  codes: {
    /* No error */
    PA_OK: C++,
    /* Access failure */
    PA_ERR_ACCESS: C++,
    /* Unknown command */
    PA_ERR_COMMAND: C++,
    /* Invalid argument */
    PA_ERR_INVALID: C++,
    /* Entity exists */
    PA_ERR_EXIST: C++,
    /* No such entity */
    PA_ERR_NOENTITY: C++,
    /* Connection refused */
    PA_ERR_CONNECTIONREFUSED: C++,
    /* Protocol error */
    PA_ERR_PROTOCOL: C++,
    /* Timeout */
    PA_ERR_TIMEOUT: C++,
    /* No authentication key */
    PA_ERR_AUTHKEY: C++,
    /* Internal error */
    PA_ERR_INTERNAL: C++,
    /* Connection terminated */
    PA_ERR_CONNECTIONTERMINATED: C++,
    /* Entity killed */
    PA_ERR_KILLED: C++,
    /* Invalid server */
    PA_ERR_INVALIDSERVER: C++,
    /* Module initialization failed */
    PA_ERR_MODINITFAILED: C++,
    /* Bad state */
    PA_ERR_BADSTATE: C++,
    /* No data */
    PA_ERR_NODATA: C++,
    /* Incompatible protocol version */
    PA_ERR_VERSION: C++,
    /* Data too large */
    PA_ERR_TOOLARGE: C++,
    /* Operation not supported */
    PA_ERR_NOTSUPPORTED: C++,
    /* The error code was unknown to the client */
    PA_ERR_UNKNOWN: C++,
    /* Extension does not exist. */
    PA_ERR_NOEXTENSION: C++,
    /* Obsolete functionality. */
    PA_ERR_OBSOLETE: C++,
    /* Missing implementation. */
    PA_ERR_NOTIMPLEMENTED: C++,
    /* The caller forked without calling execve() and tried to reuse the
       context. */
    PA_ERR_FORKED: C++,
    /* An IO error happened. */
    PA_ERR_IO: C++,
    /* Device or resource busy. */
    PA_ERR_BUSY: C++,
    /* Not really an error but the first invalid error code */
    PA_ERR_MAX: C++
  },
  descriptions: {
    [D++]: 'OK',
    [D++]: 'Access denied',
    [D++]: 'Unknown command',
    [D++]: 'Invalid argument',
    [D++]: 'Entity exists',
    [D++]: 'No such entity',
    [D++]: 'Connection refused',
    [D++]: 'Protocol error',
    [D++]: 'Timeout',
    [D++]: 'No authentication key',
    [D++]: 'Internal error',
    [D++]: 'Connection terminated',
    [D++]: 'Entity killed',
    [D++]: 'Invalid server',
    [D++]: 'Module initialization failed',
    [D++]: 'Bad state',
    [D++]: 'No data',
    [D++]: 'Incompatible protocol version',
    [D++]: 'Too large',
    [D++]: 'Not supported',
    [D++]: 'Unknown error code',
    [D++]: 'No such extension',
    [D++]: 'Obsolete functionality',
    [D++]: 'Missing implementation',
    [D++]: 'Client forked',
    [D++]: 'Input/Output error',
    [D++]: 'Device or resource busy'
  }
};
