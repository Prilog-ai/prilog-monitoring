'use strict';

const runtime = require('./runtime.cjs');

exports.init = runtime.init;
exports.captureException = runtime.captureException;
exports.withSpan = runtime.withSpan;
exports.log = runtime.log;
exports.configuration = runtime.configuration;
