# PNG-to-Atari-Basic-8-bit-
A Claude generated Python script that will read a curated PNG file and build the Atari Basic code to draw the PNG content in Graphics 10 mode.

# Preparing your PNG file 
Using your imaging software of choice (preferably Photoshop) perform the following:
1. Open the image you wish to convert.
2. Downsize it via "Image Size" using "Bicubic (smooth gradients)" to a final crop size of 320 px wide by 192 px high. 
Your image may not originate at this ratio so you may need to resize to one of the above dimensions and trim off any excess using the Canvas Size command or simply use Photoshop's Crop tool set to these dimensions and using Bicubic sizing.
3. Go to "Image > Mode > Indexed Color" and set Palette to "Local (Perceptual)" and Colors to "9". You can experiment with the Dither settings for varied results.
4. Using "Image Size" set to "Nearest Neighbour (hard edges)" and unlocking the ratio lock, set the width of the image to 80 px.
5. Export this image as an 8 bit PNG file.

The final result will be an 80 px x 192 px 8 bit image using an exclusive palette of 9 colors.
This agrees with Graphics 10 mode which is also limited to 9 colors and has non square pixels of 80 px wide by 192 px high.

# Preparing the Python script
1. After downloading the Python script "png_to_atari_basic.py" place it in your active directory along with your curated PNG file.
2. Open the Python script in a text editor.
3. Edit the quoted text on line 31 so it has the same name as your input PNG file e.g. "my_image.png"
4. Edit the quoted text on line 32 to be the name of the text file the Atari Basic will be written to e.g. "atari_basic.bas" or "atari_basic.txt"
5. Edit the quoted text on line 33 to be the name of the sample PNG file that the Python script will generate which shows what the final rendered Basic should look like.

# Running the Python script
Ensure you have Python 3 installed and open a Terminal window set to your active directory
Enter "python3 png_to_atari_basic.py" and hit enter/return.

A text file and a demonstration PNG file will be generated and saved to your active directory.

# Running the Atari Basic
If you have real Atari 8 Bit hardware with GTIA support you will need to copy the Atari Basic code to media that can be read by your hardware such as an UltraSatan or Fujinet device.
Otherwise you can run this code in an emulator such as Atari800MacX for Mac. Open the Atari Basic text file in a text editor, select all of the code and copy. Paste the code into the emulator using the appropriate Paste command. After the process of pasting is complete simply type "RUN" and hit enter to see your image get rendered line by line.

Note: The Atari has a limited palette of 128 colors and the Python script does its best to find the nearest equivalent color from the Atari palette. After generating the Atari Basic it is possible to modify the colour values. Lines 30, 40 and 50 hold the POKE values of the 9 colors. The POKE values can be in either Decimal or Hex formats.
Included with this Repository is an Excel Spreadsheet that lists all 128 colours, their POKE Hex or POKE Decimal values, approximate colour names, RGB values and actual cell swatch colours. Also within the Spreadsheet is an image with a grid of 128 colours with labelled values to quickly select the POKE Hex values. If you have a good eye for color matching you can use this resource to modify your Basic colors to be closer to your image color values.
