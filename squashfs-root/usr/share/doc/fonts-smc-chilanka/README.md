Chilanka Font
============

Chilanka is Malayalam handwriting style font designed by Santhosh Thottingal. Chilanka follows the common style one can see in everyday handwriting of Malayalam. It has a comprehensive Malayalam glyph set that contains most of the unique Malayalam conjuncts.

The glyph strokes are of uniform width with round ends giving the impression of written with either a thin felt-tip pen, or a ball-point pen. Sharp corners are completely avoided and gives the fine touch of beautiful curves of Malayalam script. The style is not the handwriting style of designer, but is based on many handwriting samples he observed. A uniform set was selected from them for the font. Even though the style is handwriting, the glyphs follow the horizontal baseline and can be used for body text too.

The font was released in 2014 and nowadays used widely in comic strips, inviitation letters etc. In 2016, latin glyphs were added matching the style of Malayalam glyphs. This is one of the popular fonts released by Swathanthra Malayam Computing project. Chilanka is developed using Inkscape and Fontforge. The souce code including the SVG drawings can be found at https://gitlab.com/smc/chilanka

![Sample text rendering](http://smc.org.in/downloads/fonts/chilanka/samples/sample1.png "Sample text rendering")

Latest version: [download](https://smc.org.in/downloads/fonts/chilanka/Chilanka-Regular.ttf)

Announcement: (http://blog.smc.org.in/new-handwriting-style-font-for-malayalam-chilanka/)

License: OFL 1.1

Building from source
--------------------
1. Install fontforge and python-fontforge
2. Install the python libraries required for build script:
    ```
    pip install -r tools/requirements.txt
    ```
3. Build the ttf, woff, woff2 files: 
   ``` 
   make
   ```