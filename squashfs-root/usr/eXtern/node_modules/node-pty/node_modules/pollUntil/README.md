# poll-until
[![](https://travis-ci.org/SokratisVidros/poll-until.svg?branch=master)](https://travis-ci.org/SokratisVidros/poll-until)
[![](https://badge.fury.io/js/pollUntil.svg)](https://www.npmjs.com/package/pollUntil)

A promised based time bomb poller.

`pollUntil(fn, args = [], timeout = 3000, pollInterval = 200)`

# Usage
Start polling for the provided polling function `fn` using this promised based `pollUntil`.

As soon as the poller starts, a time bomb promise is also triggered. If the polling function is satisfied before the time bomb detonates, `pollUntil` results `true` to the promise chain. Otherwise, it returns `false`.

The library works with Typescript, ES6 and ES5.

## Examples

```
import pollUntil from 'pollUntil';

let counter1 = 0;

const timer = setInterval(() => {
  counter ++
}, 100);

// Polling succeeded before the time bomb
pollUntil((c) => c > 10, counter, 3000, 200)
  .then((result) => {
    clearInterval(timer1);
    // result === true
    // ...
  });

// Time bomb detonated
pollUntil((c) => c > 10, counter, 100, 200)
  .then((result) => {
    clearInterval(timer);
    // result === false
    // ...
  });

```

For more examples, please have a look at project's tests.

# License
The MIT License (MIT)
