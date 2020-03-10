export default function pollUntil(fn, args = [], timeout = 3000, pollInterval = 200) {
  if (typeof fn !== 'function') {
    throw new Error('Polling function argumentmissing');
  }

  if (typeof args === 'number') {
    pollInterval = timeout;
    timeout = args;
    args = [];
  }

  let s1;
  let s2;

  function clearSchedulers() {
    clearTimeout(s1);
    clearTimeout(s2);
  }

  const poller = new Promise((resolve) => {
    (function poll() {
      const result = fn.apply(this, args);
      if (result) {
        resolve(result);
      } else {
        s1 = setTimeout(poll, pollInterval);
      }
    }());
  });

  const timebomb = new Promise((resolve) => {
    s2 = setTimeout(() => {
      resolve(false);
    }, timeout);
  });

  return Promise.race([poller, timebomb])
    .then((res) => {
      clearSchedulers();
      return Promise.resolve(res);
    })
    .catch((err) => {
      clearSchedulers();
      throw new Error(err);
    });
}
