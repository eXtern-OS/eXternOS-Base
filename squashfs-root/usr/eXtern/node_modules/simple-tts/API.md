# Documentation

















## Module: HTTP_API















## Module: client_API













`Object`
**speak**(text, o, ) *function*

> `String` **text** - text to speak

> `Object` **o**

> `Number` [**o.amplitude**]=`200` - espeak parameter. amplitude ~ volume.

> `Number` [**o.pitch**]=`40` - espeak parameter. voice pitch.

> `Number` [**o.speed**]=`150` - espeak parameter. narration speed.

> `Number` [**o.wordgap**]=`3` - espeak parameter. time between words.

> `Boolean` [**o.autoplay**]=`true` - if trueish, sample is played as soon as it's available

> `Function` [**o.onReady**] - called when playback can start

> `Function` [**o.onDone**] - called when playback ended

> **returns** `Object` - The returned object has the following interface:  









---




## Module: node_API













**speak**(text, o, ) *function*

> `String` **text** - text to speak

> `Object` **o**

> `String` [**o.lang**]=`'en'` - language to use. ex: en, fr, es, pt...

> `String` [**o.format**]=`'mp3'` - format. can be either mp3 or ogg.

> `Number` [**o.amplitude**]=`200` - espeak parameter. amplitude ~ volume.

> `Number` [**o.pitch**]=`40` - espeak parameter. voice pitch.

> `Number` [**o.speed**]=`150` - espeak parameter. narration speed.

> `Number` [**o.wordgap**]=`3` - espeak parameter. time between words.

> `String` [**o.filename**] - filename of file to save the rendering to (mutually exclusive with stream)

> `Stream` [**o.stream**] - stream where to write the rendering to (mutually exclusive with filename)











---






