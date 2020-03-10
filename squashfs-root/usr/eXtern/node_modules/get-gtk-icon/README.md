# Retrieve GTK3 icons from Node.JS [![Build Status](https://travis-ci.org/jGleitz/get-gtk-icon.svg?branch=master)](https://travis-ci.org/jGleitz/get-gtk-icon)

Allows to query icons from the user’s GTK3 theme from Node JS.

The package will return icons on 64bit Linux with GTK3 installed. It offers functions to check whether icons can be queried on the current system.

## API

### getIconPath(name, size, callback?)

Returns a promise for the path of the icon called `name` in the current user’s icon theme. The icon will be selected based on the desired `size`.
Will provide the result to the node-style `callback`, if provided.

Calling this function will return in a rejected promise (or an error to the callback) if `canQueryIcons` returns `false` or no icon could be found for the given name and size.

### getIconPathSync(name, size)

Synchronous version of `getIconPath`.

### canQueryIcons(callback?)

Returns a promise that is resolved with a boolean indicating whether calling `getIconPath` can possibly return results. Will provide the result to the node-style `callback`, if provided.


### canQueryIconSync()

Synchronous version of `canQueryIcons`.
