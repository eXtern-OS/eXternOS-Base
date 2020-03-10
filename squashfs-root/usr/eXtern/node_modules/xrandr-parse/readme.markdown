# xrandr-parse

parse the output of the `xrandr` command

# example

``` js
var parse = require('xrandr-parse');
var exec = require('child_process').exec;

exec('xrandr', function (err, stdout) {
    var query = parse(stdout);
    console.log(JSON.stringify(query, null, 2));
});
```

the `xrandr` command produced this output:

```
Screen 0: minimum 320 x 200, current 1366 x 768, maximum 3360 x 2048
LVDS connected 1366x768+0+0 (normal left inverted right x axis y axis) 256mm x 144mm
   1366x768       60.0*+   50.0  
   1360x768       60.0     50.0  
   1280x768       60.0     50.0  
   1280x720       60.0     50.0  
   1024x768       60.0     50.0  
   1024x600       60.0     50.0  
   800x600        60.0     50.0  
   800x480        60.0     50.0  
   640x480        60.0     50.0  
DFP1 disconnected (normal left inverted right x axis y axis)
CRT1 disconnected (normal left inverted right x axis y axis)
```

and the parsed query was:

```
{
  "LVDS": {
    "connected": true,
    "width": 1366,
    "height": 768,
    "modes": [
      {
        "width": "1366",
        "height": "768",
        "rate": 60
      },
      {
        "width": "1360",
        "height": "768",
        "rate": 60
      },
      {
        "width": "1280",
        "height": "768",
        "rate": 60
      },
      {
        "width": "1280",
        "height": "720",
        "rate": 60
      },
      {
        "width": "1024",
        "height": "768",
        "rate": 60
      },
      {
        "width": "1024",
        "height": "600",
        "rate": 60
      },
      {
        "width": "800",
        "height": "600",
        "rate": 60
      },
      {
        "width": "800",
        "height": "480",
        "rate": 60
      },
      {
        "width": "640",
        "height": "480",
        "rate": 60
      }
    ],
    "index": 0,
    "native": {
      "width": "1366",
      "height": "768",
      "rate": 60
    },
    "current": {
      "width": "1366",
      "height": "768",
      "rate": 60
    }
  },
  "DFP1": {
    "connected": false,
    "modes": [],
    "index": 1
  },
  "CRT1": {
    "connected": false,
    "modes": [],
    "index": 2
  }
}
```

# methods

``` js
var parse = require('xrandr-parse')
```

## parse(xrandrOutput)

Return the parsed output from a string full of the output from `xrandr`,
`xrandrOutput`.

The return object is keyed by each output name.

# install

With [npm](https://npmjs.org) do:

```
npm install xrandr-parse
```

# license

MIT
