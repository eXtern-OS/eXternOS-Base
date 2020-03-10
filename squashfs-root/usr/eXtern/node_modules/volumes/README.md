# Installing

sudo npm i volumes --save

# Usage

```
var volumes = require('volumes');

volumes.set(0).then(function(response) {
  console.log(response);
});

volumes.increase(5).then(function(response) {
  console.log(response);
});

volumes.increase(5).then(function(response) {
  console.log(response);
});
volumes.increase(50).then(function(response) {
  console.log(response);
});

volumes.decrease(60).then(function(response) {
  console.log(response);
});
``
