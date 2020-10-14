import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog as tkfd

from PIL import Image, ImageChops, ImageFilter, ImageTk

from rect import Rect

PROGNAME = 'Cropper-Tk'
VERSION = '0.20200509'

thumbsize = 896, 608
thumboffset = 16


class Cropper(tk.Tk):

    def __init__(self, master=None):
        tk.Tk.__init__(self, master)
        self.initCanvas()
        self.grid()
        self.utilButtons()

        # crop area
        self.croprect_start = None
        self.croprect_end = None

        # various rectangles
        self.canvas_rects = []  # drawn rects on image
        self.crop_rects = []  # crop areas
        self.region_rect = []  # zoom windows
        self.current_rect = None

        # just some mode trackers
        self.zoommode = False  # ??
        self.countour = False  # ??
        self.acbwmode = False  # black/white
        self.zooming = False  # ??

        # properties used for cropping
        self.w = 1
        self.h = 1
        self.x0 = 0
        self.y0 = 0
        self.n = 0

        # file loading
        self.getFile()
        self.loadimage()

    #############
    ## BUTTONS ##
    #############

    def utilButtons(self):
        self.countourButton = tk.Checkbutton(
            self, text='X', command=self.countour_mode)

        self.workFrame = tk.LabelFrame(self)

        self.zoomFrame = tk.LabelFrame(self.workFrame, text='Zooming')

        self.zoomButton = tk.Checkbutton(self.zoomFrame, text='Zoom',
                                         command=self.zoom_mode)

        self.unzoomButton = tk.Button(self.zoomFrame, text='<-|->',
                                      activebackground='#00F', command=self.unzoom_image)

        self.zoomButton.grid(row=0, column=0)
        self.unzoomButton.grid(row=0, column=1)

        self.autoFrame = tk.LabelFrame(self.workFrame, text='AutoCrop')

        self.autoButton = tk.Button(
            self.autoFrame, text='Auto', command=self.autocrop)

        self.acbwButton = tk.Checkbutton(self.autoFrame, text='BW',
                                         command=self.ac_bw_mode)

        self.autoButton.grid(row=0, column=0)
        self.acbwButton.grid(row=0, column=1)

        self.plusButton = tk.Button(
            self.workFrame, text='+', command=self.plus_box)

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

    def autocrop(self):
        border = 255
        rr = (self.region_rect.left, self.region_rect.top,
              self.region_rect.right, self.region_rect.bottom)
        imp = self.image.crop(rr)
        if self.acbwmode:
            bw = imp.convert('1')
        else:
            bw = imp.convert('L')
        bw = bw.filter(ImageFilter.MedianFilter)
        bg = Image.new('1', imp.size, border)
        diff = ImageChops.difference(bw, bg)
        bbox = diff.getbbox()
        brect = Rect((self.x0 + bbox[0], self.y0 + bbox[1]),
                     (self.x0 + bbox[2], self.y0 + bbox[3]))
        brect = brect.valid_rect(self.w, self.h)
        self.crop_rects.append(brect)
        self.n = self.n + 1
        self.canvas.delete(tk.ALL)
        self.displayimage()

    def set_button_state(self):
        if self.n > 0:
            self.plusButton.config(state='active')
            self.undoButton.config(state='normal')
            self.goButton.config(state='normal')
        else:
            self.plusButton.config(state='disabled')
            self.undoButton.config(state='disabled')
            self.goButton.config(state='disabled')
        if self.zooming:
            self.unzoomButton.config(state='normal')
        else:
            self.unzoomButton.config(state='disabled')

    ############
    # canvas ###
    ############

    def initCanvas(self):
        self.canvas = tk.Canvas(
            self, height=500, width=500, relief=tk.SUNKEN)
        self.canvas.bind('<Button-1>', self.canvas_mouse1_callback)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_mouseup1_callback)
        self.canvas.bind('<B1-Motion>', self.canvas_mouseb1move_callback)
        self.canvas.pack()

    def canvas_mouse1_callback(self, event):
        # print(event.x, event.y)
        self.croprect_start = (event.x, event.y)

    def canvas_mouseb1move_callback(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        x1 = self.croprect_start[0]
        y1 = self.croprect_start[1]
        x2 = event.x
        y2 = event.y
        print(x2, ", ", y2)
        bbox = (x1, y1, x2, y2)
        cr = self.canvas.create_rectangle(bbox)
        self.current_rect = cr

    def canvas_mouseup1_callback(self, event):
        self.croprect_end = (event.x, event.y)
        self.set_crop_area()
        print("END!")
        self.canvas.delete(self.current_rect)
        self.current_rect = None

    def ac_bw_mode(self):
        if self.acbwmode:
            self.acbwmode = False
        else:
            self.acbwmode = True

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

    def undo_last(self):
        if (self.n > 0):
            if self.canvas_rects:
                r = self.canvas_rects.pop()
                self.canvas.delete(r)
            if self.crop_rects:
                self.crop_rects.pop()
            self.n = self.n - 1
        self.set_button_state()

    def start_cropping(self):
        cropcount = 0

        newdir = Path.mkdir(Path.cwd() / ('crops_' + self.filename))

        for croparea in self.crop_rects:
            cropcount += 1
            f = self.newfilename(cropcount)
            print(f, croparea)
            self.crop(croparea, f)
        self.quit()

    #############
    ## FILES  ###
    #############

    def getFile(self):  # should return image
        self.file = tkfd.askopenfile(mode='rb', filetypes=[
            ('Image Files', '.jpg .JPG .jpeg .JPEG .png .PNG .tif .TIF .tiff .TIFF'),
            ('TIFF Image Files', '.tif .TIF .tiff .TIFF')
        ])
        self.image = Image.open(self.file)
        self.filename = self.file.name

    def loadimage(self):
        self.image_rect = Rect(self.image.size)
        self.w = self.image_rect.w
        self.h = self.image_rect.h
        self.region_rect = Rect((0, 0), (self.w, self.h))
        self.displayimage()

    def displayimage(self):
        rr = (self.region_rect.left, self.region_rect.top,
              self.region_rect.right, self.region_rect.bottom)
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

    def newfilename(self, filenum):
        f, e = os.path.splitext(self.filename)
        return '%s__crop__%s%s' % (f, filenum, e)

    #################
    ### countour ####
    #################

    def countour_mode(self):
        if self.countour:
            self.countour = False
        else:
            self.countour = True
        self.displayimage()

    ###############
    ### RECT  ####
    ###############

    def redraw_rect(self):
        for croparea in self.crop_rects:
            self.drawrect(croparea.rescale_rect(self.scale, self.x0, self.y0))

    def drawrect(self, rect):
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        cr = self.canvas.create_rectangle(
            bbox, activefill='', fill='red', stipple='gray25')
        self.canvas_rects.append(cr)

    ###############
    ### CROP ####
    ###############

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

    def crop(self, croparea, filename):
        ca = (croparea.left, croparea.top, croparea.right, croparea.bottom)
        newimg = self.image.crop(ca)
        newimg.save(filename)

    ###############
    ###  ####
    ###############

    ###############
    ###  ####
    ###############

    ###############
    ###  ####
    ###############

    # reset

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


def main():
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    # else:
        # print ("Need a filename")
        # return

    app = Cropper(filename=filename)
    app.master.title(PROGNAME)
    app.mainloop()


if __name__ == '__main__':
    main()
