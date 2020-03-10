#node-brightness

A node module for changing screen brightness on laptops and other portable devices. This module currently only works on Linux and Windows.
Keep in mind that this does change your current power plan for both AC and battery power modes, so use at your own risk.

## Using the CLI tool
When installed globally with

```shell
npm install -g node-brightness
```
you can use a superuser terminal and run:

```shell
brightness 50
```
to set the screen brightness to 50%, for instance.

## Usage in javascript code

```javascript
var changeBrightness = require(node-brightness);
changeBrightness(brightness[,callback]);
```
Where brightness is a percentage between 0 and 100

## Contributing

If you have something to add, try and follow the code style as closely as possible.

## License

Licensed under the MIT license. See license.txt.
