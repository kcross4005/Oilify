#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# From: https://stackoverflow.com/questions/44430081/how-to-run-python-scripts-using-gimpfu-from-windows-command-line/44435560#44435560
# How to Execute this script:
# gimp -idf --batch-interpreter python-fu-eval -b "import sys;sys.path=['.']+sys.path;import oilify;oilify.run('./images')" -b "pdb.gimp_quit(1)"

import os,glob,sys,time
import Tkinter as tk
from tkFont import Font
from picamera import PiCamera
from time import sleep
from gimpfu import *
from subprocess import call
from functools import partial

camera = PiCamera()
camera.rotation=90
camera.resolution = (1200,900)
camera.preview_fullscreen=False
camera.preview_window=(90,100, 320, 240)
camera.start_preview(alpha=200)
sleep(2)

win=tk.Tk()
win.title("Using tkinter")
myFont=Font(family='Helvetica', size=12, weight='bold')

def process(infile, outfile):
    #start=time.time()
    print "Processing file %s " % infile
    # load the image
    image = pdb.file_jpeg_load(infile,infile)
    drawable = pdb.gimp_image_get_active_layer(image)
    print "File %s loaded OK" % infile
    
    # process the image
    # 2) increas the brightness and contrast by 10
    #pdb.gimp_message("2")
    pdb.gimp_brightness_contrast(drawable, 10, 10)
    
    # 3) Make the colors more intense
    #pdb.gimp_message("3")
    pdb.plug_in_unsharp_mask(image, drawable, 12, 1, 0) #12=radius, 1=amount, 0=threshold)
    
    # 4) Reduce number of colors
    #pdb.gimp_message("4")
    pdb.gimp_posterize(drawable, 12)     # 12=levels
    
    # 5) Add an alpha channel
    pdb.gimp_layer_add_alpha(image.layers[0])
    
    # 6) Copy the current layer, but don't insert it into image yet
    line_layer = pdb.gimp_layer_copy(image.layers[0], TRUE) # TRUE=add_alpha
    pdb.gimp_item_set_name(line_layer, "Line Layer")
 
    # 7) Use the blur filter to make colors merge at edges
    # Filter - Blue - Gaussian Blue Radius 1x, method: RLE
    pdb.plug_in_gauss(image, image.layers[0], 6, 6, 1) # 6=horizontal, 6=vertical, 1=RLE=method)
    
    # 8) use the custom "oilify" gimpressionist preset to apply brushstrokes
    # this preset is:
    # Presets: Feathers
    # Paper: Scale: 1x (x=12)
    #  Brush: defaultbrush.pgm
    # Orientation: Directions:6, Start Angle: 0, Angle Span: 120, Orientation: Adaptive
    # Size: Sizes: 4, Min Size: 3x (36, cause x=12) Max Size: 8x (96, cause x=12), Size: Adaptive
    # Placement: Randonly, Stroke Density: 36
    pdb.plug_in_gimpressionist(image, image.layers[0], "myOilify")

    # 9) Reduce stroke contours
    # Colors - Color to Alpha
    pdb.plug_in_colortoalpha(image, image.layers[0], (186,186,186))
    
    # 10) Create a white layer on the bottom
    white_layer = pdb.gimp_layer_new(image, drawable.width, drawable.height, RGB_IMAGE, "White", 100, NORMAL_MODE)
    pdb.gimp_drawable_fill(white_layer, WHITE_FILL)
    pdb.gimp_image_insert_layer(image, white_layer, image.layers[0].parent, 1) # parent, 1=losition 1 within image
    
    # Now start working on the line layer
    # 11) Put the line layer at the top of the image layer stack
    pdb.gimp_image_insert_layer(image, line_layer, image.layers[0].parent, 0) # parent, 1=losition 1 within image
    #DEBUG-pdb.gimp_xcf_save(0, image, drawable, '/home/pi/Documents/batch/image1.xcf', '/home/pi/Documents/batch/image1.xcf')
    
    # 12) Draw the outlines of the shape
    # Filter - Edge-Detect - Neon
    # Radius: 0.5x, Intensity: 0%
    pdb.plug_in_neon(image, line_layer, 5, 0)   # 6=radius, 0=amount
    
    # 13) Remove colored lines
    # Colors - Desaturate - Shade Average
    pdb.gimp_desaturate_full(line_layer, 2)  # 2=desaturate_mode = AVERAGE

    # 14 Invert the colors
    # Colors - Invert
    #pdb.gimp_message("14")
    pdb.gimp_invert(line_layer)
    
    # 15) Remove grey tones
    # Colors - Threshold
    pdb.gimp_threshold(line_layer, 127, 255) # 127=low, 255=high_threshold
    
    # 16) "It should look like this, now:
    # 17) Skipped. Too long for little effect
    # 18) Remove the white background color
    # Colors - Color to Alpha
    pdb.plug_in_colortoalpha(image, line_layer, (255,255,255))
    
    # 19) Use rubber-tool to remove artefacts - skipped
    # 20) Finish painting by choosing "Overlay" for the line layer
    # Layer Dialog box - select Line Layer, choose Overlay Mode
    pdb.gimp_layer_set_mode(line_layer, 5)   # 5=mode = OVERLAY-MODE
    
    # Add the overlay to image
    overlay_layer = pdb.gimp_file_load_layer(image, '/home/pi/Documents/batch/OverlayWide.png')
    pdb.gimp_image_insert_layer(image, overlay_layer, image.layers[0].parent, 0) # parent, 1=losition 1 within image
    #DEBUG-pdb.gimp_xcf_save(0, image, drawable, '/home/pi/Documents/batch/image2.xcf', '/home/pi/Documents/batch/image2.xcf')
   
    # Flatten all layers into a single layer
    drawable = pdb.gimp_image_flatten(image)
    
    # output processed image
    ##outfile=os.path.join('processed',os.path.basename(infile))
    ##outfile=os.path.join(os.path.dirname(infile),outfile)
    print "Saving to %s" % outfile
    #pdb.file_jpeg_save(image, drawable, outfile, outfile, "0.5",0,1,0,"",0,1,0,0)
    pdb.file_jpeg_save(image, drawable, outfile, outfile, 0.9, 0, 1, 1, "Oiled", 2, 1, 0, 0)
    print "Saved to %s" % outfile
    #DEBUG-pdb.gimp_xcf_save(0, image, drawable, '/home/pi/Documents/batch/image3.xcf', '/home/pi/Documents/batch/image3.xcf')

    # Print the image
    # pdb.file_print_gtk(image)
    
    # Send the image to Dropbox
    #photofile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload " + outfile + " " + os.path.basename(outfile)
    #print "photofile=" + photofile
    #call ([photofile], shell=True)  
    
    #end=time.time()
    #print "It took: %.2f seconds" % (end-start)
    pdb.gimp_image_delete(image)

def takePicture(home):
    start=time.time()
    now = time.strftime("%Y%m%d-%H%M%S")
    infile = home + "/" + now + "-in.jpg"
    outfile = home + "/" + now + "-out.jpg"
    camera.capture(infile)
    process(infile, outfile)
    
    # Send the image to Dropbox
    photofile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload " + outfile + " " + os.path.basename(outfile)
    print "photofile=" + photofile
    call ([photofile], shell=True) 
    
    end=time.time()
    print "It took: %.2f seconds" % (end-start)

def exitProgram():
    pdb.gimp_quit(1)
    sys.exit()
    
def run(home):
    #print "home=" + home
    ledButton=tk.Button(win, text='Take Picture', font=myFont, command=partial(takePicture, home), bg='bisque2', height=8, width=24)
    ledButton.grid(row=0, sticky=tk.NSEW)
    ledButton=tk.Button(win, text='Exit', font=myFont, command=exitProgram, bg='cyan', height=8, width=24)
    ledButton.grid(row=1, sticky=tk.E)
    tk.mainloop()

if __name__ == "__main__":
        print "Running as __main__ with args: %s" % sys.argv