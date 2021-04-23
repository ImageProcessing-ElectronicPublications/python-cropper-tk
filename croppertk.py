#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
photo_spliter.py - Provides a simple method to split a single image containing
multiple images into individual files.

Created by Greg Lavino
03.16.2010


Note the following packages are required:
 python-tk
 python-imaging
 python-imaging-tk
'''

PROGNAME = 'Cropper-Tk'
VERSION = '0.20210423'

import os
import sys
import argparse
from PIL import Image, ImageTk, ImageFilter, ImageChops

py_version = sys.version

if py_version[0] == "2":
    # for Python2
    reload(sys)
    sysenc = sys.stdout.encoding
    if sysenc:
        sys.setdefaultencoding(sysenc)

    import Tkinter as tk
    import tkFileDialog as tkfd

elif py_version[0] == "3":
    # for Python3
    import tkinter as tk
    from tkinter import filedialog as tkfd

else:
    pass

thumbsize = 896, 608
thumboffset = 16

class Application(tk.Frame):
    def __init__(self, master=None, filename=None):

        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.croprect_start = None
        self.croprect_end = None
        self.canvas_rects = []
        self.crop_rects = []
        self.region_rect = []
        self.current_rect = None
        self.zoommode = False
        self.countour = False
        self.acbwmode = False
        self.zooming = False
        self.w = 1
        self.h = 1
        self.x0 = 0
        self.y0 = 0
        self.scale = None
        self.n = 0

        if not(filename):
            filenames = tkfd.askopenfilenames(master=self,
                          defaultextension='.jpg', multiple=1, parent=self,
                          filetypes=(
                              (('Image Files'),
                               '.jpg .JPG .jpeg .JPEG .png .PNG .tif .TIF .tiff .TIFF'),
                              (('JPEG Image Files'),
                               '.jpg .JPG .jpeg .JPEG'),
                              (('PNG Image Files'),
                               '.png .PNG'),
                              (('TIFF Image Files'),
                               '.tif .TIF .tiff .TIFF'),
                              (('All files'), '*'),
                          ),
                          title=('Select images to crop'))
            if filenames:
                filename = filenames[0]

        if filename:
            self.filename = filename
            self.loadimage()

    def createWidgets(self):
        self.canvas = tk.Canvas(
            self, height=1, width=1, relief=tk.SUNKEN)
        self.canvas.bind('<Button-1>', self.canvas_mouse1_callback)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_mouseup1_callback)
        self.canvas.bind('<B1-Motion>', self.canvas_mouseb1move_callback)

        self.sizeLabel = tk.Label(self, text="0x0")

        self.countourButton = tk.Checkbutton(self, text='X',
                                              command=self.countour_mode)

        self.workFrame = tk.LabelFrame(self)

        self.zoomFrame = tk.LabelFrame(self.workFrame, text='Zooming')

        self.zoomButton = tk.Checkbutton(self.zoomFrame, text='Zoom',
                                              command=self.zoom_mode)

        self.unzoomButton = tk.Button(self.zoomFrame, text='<-|->',
                                           activebackground='#00F', command=self.unzoom_image)

        self.zoomButton.grid(row=0, column=0)
        self.unzoomButton.grid(row=0, column=1)

        self.autoFrame = tk.LabelFrame(self.workFrame, text='AutoCrop')

        self.autoButton = tk.Button(self.autoFrame, text='Auto', command=self.autocrop)

        self.acbwButton = tk.Checkbutton(self.autoFrame, text='BW',
                                              command=self.ac_bw_mode)

        self.autoButton.grid(row=0, column=0)
        self.acbwButton.grid(row=0, column=1)

        self.plusButton = tk.Button(self.workFrame, text='+', command=self.plus_box)

        self.zoomFrame.grid(row=0, column=0, padx=5)
        self.autoFrame.grid(row=0, column=1, padx=5)
        self.plusButton.grid(row=0, column=2, padx=5)

        self.ActionFrame = tk.LabelFrame(self, text='Action')

        self.resetButton = tk.Button(self.ActionFrame, text='Reset',
                                          activebackground='#F00', command=self.reset)

        self.undoButton = tk.Button(self.ActionFrame, text='Undo',
                                         activebackground='#FF0', command=self.undo_last)

        self.goButton = tk.Button(self.ActionFrame, text='Crops',
                                       activebackground='#0F0', command=self.start_cropping)

        self.quitButton = tk.Button(self.ActionFrame, text='Quit',
                                         activebackground='#F00', command=self.quit)

        self.resetButton.grid(row=0, column=0)
        self.undoButton.grid(row=0, column=1)
        self.goButton.grid(row=0, column=2)
        self.quitButton.grid(row=0, column=3)

        self.canvas.grid(row=0, columnspan=3)
        self.countourButton.grid(row=1, column=0)
        self.workFrame.grid(row=1, column=1)
        self.ActionFrame.grid(row=1, column=2)
        self.sizeLabel.grid(row=2, column=0, columnspan=3)

    def set_button_state(self):
        if self.n > 0:
            self.plusButton.config(state = 'normal')
            self.undoButton.config(state = 'normal')
            self.goButton.config(state = 'normal')
        else:
            self.plusButton.config(state = 'disabled')
            self.undoButton.config(state = 'disabled')
            self.goButton.config(state = 'disabled')
        if self.zooming:
            self.unzoomButton.config(state = 'normal')
        else:
            self.unzoomButton.config(state = 'disabled')

    def canvas_mouse1_callback(self, event):
        self.croprect_start = (event.x, event.y)

    def canvas_mouseb1move_callback(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        x1 = self.croprect_start[0]
        y1 = self.croprect_start[1]
        x2 = event.x
        y2 = event.y
        bbox = (x1, y1, x2, y2)
        dx = int((x2 - x1) * self.scale[0] * 10 + 0.5) * 0.1
        dy = int((y2 - y1) * self.scale[1] * 10 + 0.5) * 0.1
        dt = str(dx) + "x" + str(dy)
        cr = self.canvas.create_rectangle(bbox)
        self.current_rect = cr
        self.sizeLabel.configure(text=dt)

    def canvas_mouseup1_callback(self, event):
        self.croprect_end = (event.x, event.y)
        self.set_crop_area()
        self.canvas.delete(self.current_rect)
        self.current_rect = None

    def set_crop_area(self):
        r = Rect(self.croprect_start, self.croprect_end)

        # adjust dimensions
        r.clip_to(self.image_thumb_rect)

        # ignore rects smaller than this size
        if min(r.h, r.w) < 10:
            return

        ra = r
        ra = ra.scale_rect(self.scale)
        ra = ra.move_rect(self.x0, self.y0)
        ra = ra.valid_rect(self.w, self.h)
        if self.zoommode:
            self.canvas.delete(tk.ALL)
            self.x0 = ra.left
            self.y0 = ra.top
            self.region_rect = ra
            self.displayimage()
            self.zoommode = False
            self.zoomButton.deselect()
            self.zooming = True
        else:
            self.drawrect(r)
            self.crop_rects.append(ra)
            self.n = self.n + 1
        self.set_button_state()

    def countour_mode(self):
        if self.countour:
            self.countour = False
        else:
            self.countour = True
        self.displayimage()

    def zoom_mode(self):
        if self.zoommode:
            self.zoommode = False
        else:
            self.zoommode = True

    def unzoom_image(self):
        self.canvas.delete(tk.ALL)
        self.zoommode = False
        self.zoomButton.deselect()
        self.x0 = 0
        self.y0 = 0
        self.region_rect = Rect((0, 0), (self.w, self.h))
        self.zooming = False
        self.displayimage()

    def plus_box(self):
        if self.n > 1:
            self.canvas.delete(tk.ALL)
            if self.crop_rects:
                ra = self.crop_rects[self.n - 1]
                self.crop_rects.pop()
                self.n = self.n - 1
                ra0 = self.crop_rects[self.n - 1]
                ra0 = ra0.plus_rect(ra)
                self.crop_rects[self.n - 1] = ra0
                self.displayimage()
                self.zoommode = False
                self.zoomButton.deselect()

    def redraw_rect(self):
        for croparea in self.crop_rects:
            self.drawrect(croparea.rescale_rect(self.scale, self.x0, self.y0))

    def undo_last(self):
        if (self.n > 0):
            if self.canvas_rects:
                r = self.canvas_rects.pop()
                self.canvas.delete(r)
            if self.crop_rects:
                self.crop_rects.pop()
            self.n = self.n - 1
        self.set_button_state()

    def drawrect(self, rect):
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        cr = self.canvas.create_rectangle(
            bbox, activefill='', fill='red', stipple='gray25')
        self.canvas_rects.append(cr)

    def displayimage(self):
        rr = (self.region_rect.left, self.region_rect.top, self.region_rect.right, self.region_rect.bottom)
        self.image_thumb = self.image.crop(rr)
        self.image_thumb.thumbnail(thumbsize, Image.ANTIALIAS)
        if self.countour:
            self.image_thumb = self.image_thumb.filter(ImageFilter.CONTOUR)

        self.image_thumb_rect = Rect(self.image_thumb.size)

        self.photoimage = ImageTk.PhotoImage(self.image_thumb)
        w, h = self.image_thumb.size
        self.canvas.configure(
            width=(w + 2 * thumboffset),
            height=(h + 2 * thumboffset))

        self.canvas.create_image(
            thumboffset,
            thumboffset,
            anchor=tk.NW,
            image=self.photoimage)

        x_scale = float(self.region_rect.w) / self.image_thumb_rect.w
        y_scale = float(self.region_rect.h) / self.image_thumb_rect.h
        self.scale = (x_scale, y_scale)
        self.redraw_rect()
        self.set_button_state()

    def reset(self):
        self.canvas.delete(tk.ALL)
        self.zoommode = False
        self.zoomButton.deselect()
        self.zooming = False
        self.countour = False
        self.countourButton.deselect()
        self.acbwmode = False
        self.acbwButton.deselect()
        self.canvas_rects = []
        self.crop_rects = []
        self.region_rect = Rect((0, 0), (self.w, self.h))
        self.n = 0
        self.x0 = 0
        self.y0 = 0

        self.displayimage()

    def ac_bw_mode(self):
        if self.acbwmode:
            self.acbwmode = False
        else:
            self.acbwmode = True

    def autocrop(self):
        border = 255
        rr = (self.region_rect.left, self.region_rect.top, self.region_rect.right, self.region_rect.bottom)
        imp = self.image.crop(rr)
        if self.acbwmode:
            bw = imp.convert('1')
        else:
            bw = imp.convert('L')
        bw = bw.filter(ImageFilter.MedianFilter)
        bg = Image.new('1', imp.size, border)
        diff = ImageChops.difference(bw, bg)
        bbox = diff.getbbox()
        brect = Rect((self.x0 + bbox[0], self.y0 + bbox[1]), (self.x0 + bbox[2], self.y0 + bbox[3]))
        brect = brect.valid_rect(self.w, self.h)
        self.crop_rects.append(brect)
        self.n = self.n + 1
        self.canvas.delete(tk.ALL)
        self.displayimage()

    def loadimage(self):
        self.image = Image.open(self.filename)
        print (self.image.size)
        self.image_rect = Rect(self.image.size)
        self.w = self.image_rect.w
        self.h = self.image_rect.h
        self.region_rect = Rect((0, 0), (self.w, self.h))

        self.displayimage()

    def newfilename(self, filenum):
        f, e = os.path.splitext(self.filename)
        return '%s__crop__%s%s' % (f, filenum, e)

    def start_cropping(self):
        cropcount = 0
        for croparea in self.crop_rects:
            cropcount += 1
            f = self.newfilename(cropcount)
            print (f, croparea)
            self.crop(croparea, f)
        self.quit()

    def crop(self, croparea, filename):
        ca = (croparea.left, croparea.top, croparea.right, croparea.bottom)
        newimg = self.image.crop(ca)
        newimg.save(filename)


class Rect(object):
    def __init__(self, *args):
        self.set_points(*args)

    def set_points(self, *args):
        if len(args) == 2:
            pt1 = args[0]
            pt2 = args[1]
        elif len(args) == 1:
            pt1 = (0, 0)
            pt2 = args[0]
        elif len(args) == 0:
            pt1 = (0, 0)
            pt2 = (0, 0)

        x1, y1 = pt1
        x2, y2 = pt2

        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)

        self._update_dims()

    def clip_to(self, containing_rect):
        cr = containing_rect
        self.top = max(self.top, cr.top + thumboffset)
        self.bottom = min(self.bottom, cr.bottom + thumboffset)
        self.left = max(self.left, cr.left + thumboffset)
        self.right = min(self.right, cr.right + thumboffset)
        self._update_dims()

    def _update_dims(self):
        """added to provide w and h dimensions."""

        self.w = self.right - self.left
        self.h = self.bottom - self.top

    def scale_rect(self, scale):
        x_scale = scale[0]
        y_scale = scale[1]

        r = Rect()
        r.top = int((self.top - thumboffset) * y_scale + 0.5)
        r.bottom = int((self.bottom - thumboffset) * y_scale + 0.5)
        r.right = int((self.right - thumboffset) * x_scale + 0.5)
        r.left = int((self.left - thumboffset) * x_scale + 0.5)
        r._update_dims()

        return r

    def move_rect(self, x0, y0):
        r = Rect()
        r.top = int(self.top + y0)
        r.bottom = int(self.bottom + y0)
        r.right = int(self.right + x0)
        r.left = int(self.left + x0)
        r._update_dims()

        return r

    def rescale_rect(self, scale, x0, y0):
        x_scale = scale[0]
        y_scale = scale[1]

        r = Rect()
        r.top = int((self.top - y0) / y_scale + thumboffset)
        r.bottom = int((self.bottom - y0) / y_scale + thumboffset)
        r.right = int((self.right - x0) / x_scale + thumboffset)
        r.left = int((self.left - x0) / x_scale + thumboffset)
        r._update_dims()

        return r

    def plus_rect(self, r0):
        r = Rect()
        r.top = min(self.top, r0.top)
        r.bottom = max(self.bottom, r0.bottom)
        r.right = max(self.right, r0.right)
        r.left = min(self.left, r0.left)
        r._update_dims()

        return r

    def valid_rect(self, w, h):
        r = Rect()
        r.top = self.top
        if r.top < 0:
            r.top = 0
        if r.top > h - 1:
            r.top = h - 1
        r.bottom = self.bottom
        if r.bottom < 1:
            r.bottom = 1
        if r.bottom > h:
            r.bottom = h
        r.right = self.right
        if r.right < 1:
            r.right = 1
        if r.right > w:
            r.right = w
        r.left = self.left
        if r.left < 0:
            r.left = 0
        if r.left > w - 1:
            r.left = w - 1
        r._update_dims()

        return r

    def __repr__(self):
        return '(%d,%d)-(%d,%d)' % (self.left,
                                    self.top, self.right, self.bottom)


def main(filename):
    app = Application(filename=filename)
    app.master.title(PROGNAME)
    app.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Cropper Image')
    parser.add_argument('filename', nargs='?', default=None, help='image file name')
    args = parser.parse_args()
    main(args.filename)
