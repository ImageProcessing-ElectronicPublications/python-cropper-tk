#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
photo_spliter.py - Provides a simple method to split a single image containing
multiple images into individual files.

Created by zvezdochiot
2017.12.30


Note the following packages are required:
 python-tk
 python-imaging
 python-imaging-tk
 python-reportlab
'''


import os
import sys
import re
from PIL import Image, ImageTk, ImageFilter, ImageChops
from reportlab.pdfgen.canvas import Canvas

py_version = sys.version

if py_version[0] == "2":
    # for Python2
    import Tkinter as tk
    import tkFileDialog as tkfd

elif py_version[0] == "3":
    # for Python3
    import tkinter as tk
    from tkinter import filedialog as tkfd

else:
    pass

PROGNAME = 'CropperTktoPDF'
VERSION = '0.20200424'

thumbsize = 896, 608
thumboffset = 16
default_dpi = 300
default_mindpi = 36
default_cleanmargin = 0
default_format = 'png'
default_div = 1

class Application(tk.Frame):
    def __init__(self, master=None, filename=None):

        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.croprect_start = None
        self.croprect_end = None
        self.crop_count = 0
        self.canvas_rects = []
        self.crop_rects = []
        self.region_rect = []
        self.current_rect = None
        self.zoommode = False
        self.countour = False
        self.w = 1
        self.h = 1
        self.x0 = 0
        self.y0 = 0
        self.dpi = default_dpi
        self.ext = default_format
        self.div = default_div
        self.cleanmargin = default_cleanmargin
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
            self.outfile = self.filename + '.pdf'
            self.loadimage()

    def createWidgets(self):
        self.canvas = tk.Canvas(
            self, height=1, width=1, relief=tk.SUNKEN)
        self.canvas.bind('<Button-1>', self.canvas_mouse1_callback)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_mouseup1_callback)
        self.canvas.bind('<B1-Motion>', self.canvas_mouseb1move_callback)

        self.resetButton = tk.Button(self, text='Reset',
                                          activebackground='#F00', command=self.reset)

        self.dpiLabel = tk.Label(self, text='DPI')
        self.dpiBox = tk.Text(self, height=1, width=4)
        self.dpiBox.insert(1.0, str(default_dpi))

        self.formatLabel = tk.Label(self, text='F')
        self.formatBox = tk.Text(self, height=1, width=4)
        self.formatBox.insert(1.0, default_format)

        self.divLabel = tk.Label(self, text='div')
        self.divBox = tk.Text(self, height=1, width=2)
        self.divBox.insert(1.0, str(default_div))

        self.undoButton = tk.Button(self, text='Undo',
                                         activebackground='#FF0', command=self.undo_last)

        self.countourButton = tk.Checkbutton(self, text='X',
                                              command=self.countour_mode)

        self.zoomButton = tk.Checkbutton(self, text='Zoom',
                                              command=self.zoom_mode)

        self.unzoomButton = tk.Button(self, text='<-|->',
                                           activebackground='#00F', command=self.unzoom_image)

        self.plusButton = tk.Button(self, text='+', command=self.plus_box)

        self.autoButton = tk.Button(self, text='Auto', command=self.autocrop)

        self.cleanmarginLabel = tk.Label(self, text='[]')
        self.cleanmarginBox = tk.Text(self, height=1, width=2)
        self.cleanmarginBox.insert(1.0, str(default_cleanmargin))

        self.goButton = tk.Button(self, text='Crops',
                                       activebackground='#0F0', command=self.start_cropping)

        self.quitButton = tk.Button(self, text='Quit',
                                         activebackground='#F00', command=self.quit)

        self.canvas.grid(row=0, columnspan=17)
        self.resetButton.grid(row=1, column=0)
        self.countourButton.grid(row=1, column=1)
        self.dpiLabel.grid(row=1, column=2)
        self.dpiBox.grid(row=1, column=3)
        self.formatLabel.grid(row=1, column=4)
        self.formatBox.grid(row=1, column=5)
        self.divLabel.grid(row=1, column=6)
        self.divBox.grid(row=1, column=7)
        self.undoButton.grid(row=1, column=8)
        self.zoomButton.grid(row=1, column=9)
        self.unzoomButton.grid(row=1, column=10)
        self.plusButton.grid(row=1, column=11)
        self.autoButton.grid(row=1, column=12)
        self.cleanmarginLabel.grid(row=1, column=13)
        self.cleanmarginBox.grid(row=1, column=14)
        self.goButton.grid(row=1, column=15)
        self.quitButton.grid(row=1, column=16)

    def verify_params(self):
        self.dpi = int(self.dpiBox.get('1.0', tk.END))
        self.ext = self.formatBox.get('1.0', tk.END)
        self.ext = re.sub(r'\n', '', self.ext)
        self.div = int(self.divBox.get('1.0', tk.END))
        self.cleanmargin = int(self.cleanmarginBox.get('1.0', tk.END))
        if self.dpi < default_mindpi:
            self.dpi = default_dpi
        if ((self.ext != 'png') and
            (self.ext != 'jpg') and
            (self.ext != 'jpeg') and
            (self.ext != 'tif') and
                (self.ext != 'tiff')):
            self.ext = default_format
        if self.div < 1:
            self.div = default_div
        if self.cleanmargin < 0:
            self.cleanmargin = default_cleanmargin
        self.dpiBox.delete('1.0', tk.END)
        self.dpiBox.insert('1.0', str(self.dpi))
        self.formatBox.delete('1.0', tk.END)
        self.formatBox.insert('1.0', self.ext)
        self.divBox.delete('1.0', tk.END)
        self.divBox.insert('1.0', str(self.div))
        self.cleanmarginBox.delete('1.0', tk.END)
        self.cleanmarginBox.insert('1.0', str(self.cleanmargin))

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
        cr = self.canvas.create_rectangle(bbox)
        self.current_rect = cr

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
        if min(r.h, r.w) < 3:
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
        else:
            self.drawrect(r)
            self.crop_rects.append(ra)
            self.n = self.n + 1
        self.verify_params()

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
        if self.canvas_rects:
            r = self.canvas_rects.pop()
            self.canvas.delete(r)
        if self.crop_rects:
            self.crop_rects.pop()
            self.n = self.n - 1

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

    def reset(self):
        self.canvas.delete(tk.ALL)
        self.zoommode = False
        self.zoomButton.deselect()
        self.countour = False
        self.countourButton.deselect()
        self.canvas_rects = []
        self.crop_rects = []
        self.n = 0
        self.region_rect = Rect((0, 0), (self.w, self.h))
        self.x0 = 0
        self.y0 = 0

        self.displayimage()
        self.verify_params()

    def autocrop(self):
        border = 255
        rr = (self.region_rect.left, self.region_rect.top, self.region_rect.right, self.region_rect.bottom)
        imp = self.image.crop(rr)
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
        self.verify_params()

    def newfilename(self, filenum):
        f, e = os.path.splitext(self.filename)
        return '%s__crop__%s.%s' % (f, filenum, self.ext)

    def start_cropping(self):
        cropcount = 0
        self.verify_params()
        pdf = Canvas(self.outfile, pageCompression=1)
        width = round(self.w * 72.0 / self.dpi, 3)
        height = round(self.h * 72.0 / self.dpi, 3)
        pdf.setPageSize((width, height))
        for croparea in self.crop_rects:
            cropcount += 1
            f = self.newfilename(cropcount)
            print (f, croparea)
            self.crop(croparea, f)
            wt = round(croparea.w * 72.0 / self.dpi, 3)
            ht = round(croparea.h * 72.0 / self.dpi, 3)
            x = round(croparea.left * 72.0 / self.dpi, 3)
            y = height - round(croparea.bottom * 72.0 / self.dpi, 3)
            pdf.drawImage(f, x, y, width=wt, height=ht)
        pdf.showPage()
        pdf.save()
        for croparea in self.crop_rects:
            self.clean_rect(croparea)
        f = self.newfilename(0)
        self.image.save(f)
        self.quit()

    def crop(self, croparea, filename):
        ca = (croparea.left, croparea.top, croparea.right, croparea.bottom)
        newimg = self.image.crop(ca)
        divd = int(self.div / 2)
        divw = int((croparea.w + divd) / self.div)
        divh = int((croparea.h + divd) / self.div)
        divsize = divw, divh
        newimg.thumbnail(divsize, Image.ANTIALIAS)
        newimg.save(filename)

    def clean_rect(self, croparea):
        cab = croparea
        cab = cab.addmargin_rect(self.cleanmargin, self.w, self.h)
        ca = (cab.left, cab.top, cab.right, cab.bottom)
        width = cab.w
        height = cab.h
        if self.image.mode == 'RGB':
            newimg = Image.new('RGB', (width, height), (255, 255, 255))
        else:
            newimg = Image.new('L', (width, height), 255)
        self.image.paste(newimg, ca)


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

    def addmargin_rect(self, margin, width, height):
        r = Rect()
        r.top = self.top - margin
        r.bottom = self.bottom + margin
        r.right = self.right + margin
        r.left = self.left - margin
        r = r.valid_rect(width, height)
        r._update_dims()

        return r

    def __repr__(self):
        return '(%d,%d)-(%d,%d)' % (self.left,
                                    self.top, self.right, self.bottom)

def main():
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    # else:
        # print ("Need a filename")
        # return

    app = Application(filename=filename)
    app.master.title(PROGNAME)
    app.mainloop()


if __name__ == '__main__':
    main()
