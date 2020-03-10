## When passing an image base64 as first argument to the function, it returns the base64 of the resized image. maxWidth and maxHeight are optional.

#### Note: This is a font-end package. This package will not work on the server side.  Consider installing browsify or webpack to  


####  What is it for?
`If you have a base64 image and you would like to resize it, this function will return a base64 image resizes to your height and width specifications.`


#### How do I install it?
`npm install resize-base64  --save`



##### For npm 
```
var resizebase64 = require('resize-base64');  

var  img = resizebase64(base64, maxWidth, maxHeight); 

```


