"""This module contains user interface related classes and methods.
"""
import abc
import weakref
import attr

import ueberzug.xutil as xutil
import ueberzug.geometry as geometry
import ueberzug.scaling as scaling
import ueberzug.X as X


def roundup(value, unit):
    return ((value + (unit - 1)) & ~(unit - 1)) >> 3


def get_visual_id(screen, depth: int):
    """Determines the visual id
    for the given screen and - depth.
    """
    try:
        return next(filter(lambda i: i.depth == depth,
                           screen.allowed_depths)) \
               .visuals[0].visual_id
    except StopIteration:
        raise ValueError(
            'Screen does not support depth %d' % depth)


class View:
    """Data class which holds meta data about the screen"""
    def __init__(self):
        self.offset = geometry.Distance()
        self.media = {}


class WindowFactory:
    """Window factory class"""
    def __init__(self, display):
        self.display = display

    @abc.abstractmethod
    def create(self, *window_infos: xutil.TerminalWindowInfo):
        """Creates a child window for each window id."""
        raise NotImplementedError()


class OverlayWindow(X.Window):
    """Ensures unmapping of windows"""

    class Factory(WindowFactory):
        """OverlayWindows factory class"""
        def __init__(self, display, view):
            super().__init__(display)
            self.view = view

        def create(self, *window_infos: xutil.TerminalWindowInfo):
            return [OverlayWindow(self.display, self.view, info)
                    for info in window_infos]

    class Placement:
        @attr.s
        class TransformedImage:
            """Data class which contains the options
            an image was transformed with
            and the image data.
            """
            options = attr.ib(type=tuple)
            data = attr.ib(type=bytes)

        def __init__(self, x: int, y: int, width: int, height: int,
                     scaling_position: geometry.Point,
                     scaler: scaling.ImageScaler,
                     path: str, image, last_modified: int,
                     cache: weakref.WeakKeyDictionary = None):
            # x, y are useful names in this case
            # pylint: disable=invalid-name
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.scaling_position = scaling_position
            self.scaler = scaler
            self.path = path
            self.image = image
            self.last_modified = last_modified
            self.cache = cache or weakref.WeakKeyDictionary()

        def transform_image(self, term_info: xutil.TerminalWindowInfo,
                            width: int, height: int,
                            format_scanline: tuple):
            """Scales to image and calculates
            the width & height needed to display it.

            Returns:
                tuple of (width: int, height: int, image: bytes)
            """
            scanline_pad, scanline_unit = format_scanline
            transformed_image = self.cache.get(term_info)
            final_size = self.scaler.calculate_resolution(
                self.image, width, height)
            options = (self.scaler.get_scaler_name(),
                       self.scaling_position, final_size)

            if (transformed_image is None
                    or transformed_image.options != options):
                image = self.scaler.scale(
                    self.image, self.scaling_position, width, height)
                stride = roundup(image.width * scanline_unit, scanline_pad)
                transformed_image = self.TransformedImage(
                    options, image.tobytes("raw", 'BGRX', stride, 0))
                self.cache[term_info] = transformed_image

            return (*final_size, transformed_image.data)

        def resolve(self, pane_offset: geometry.Distance,
                    term_info: xutil.TerminalWindowInfo,
                    format_scanline):
            """Resolves the position and size of the image
            according to the teminal window information.

            Returns:
                tuple of (x: int, y: int, width: int, height: int,
                          image: PIL.Image)
            """
            # x, y are useful names in this case
            # pylint: disable=invalid-name
            x = int((self.x + pane_offset.left) * term_info.font_width +
                    term_info.padding_horizontal)
            y = int((self.y + pane_offset.top) * term_info.font_height +
                    term_info.padding_vertical)
            width = int((self.width and (self.width * term_info.font_width))
                        or self.image.width)
            height = \
                int((self.height and (self.height * term_info.font_height))
                    or self.image.height)

            return (x, y, *self.transform_image(
                term_info, width, height, format_scanline))

    def __init__(self, display: X.Display,
                 view: View, parent_info: xutil.TerminalWindowInfo):
        """Changes the foreground color of the gc object.

        Args:
            display (Xlib.display.Display): any created instance
            parent_id (int): the X11 window id of the parent window
        """
        super().__init__(display, parent_info.window_id)
        self.parent_info = parent_info
        self._view = view
        # TODO change this to the real values
        self.SCREEN_WIDTH = 2000
        self.SCREEN_HEIGHT = 2000
        self._image = X.Image(
            display,
            self.SCREEN_WIDTH,
            self.SCREEN_HEIGHT)

    def __enter__(self):
        # TODO is this still needed?
        self.draw()
        return self

    def __exit__(self, *args):
        pass

    def draw(self):
        """Draws the window and updates the visibility mask."""
        rectangles = []

        scanline_pad = 32  # TODO add to c module # self.window.display.info.bitmap_format_scanline_pad
        scanline_unit = 32  # TODO add to c module # self.window.display.info.bitmap_format_scanline_unit

        if not self.parent_info.ready:
            self.parent_info.calculate_sizes(
                self.width, self.height)

        for placement in self._view.media.values():
            # x, y are useful names in this case
            # pylint: disable=invalid-name
            x, y, width, height, image = \
                placement.resolve(self._view.offset, self.parent_info,
                                  (scanline_pad, scanline_unit))
            rectangles.append((x, y, width, height))
            self._image.draw(x, y, width, height, image)

        self._image.copy_to(
            self.id,
            0, 0,
            min(self.width, self.SCREEN_WIDTH),
            min(self.height, self.SCREEN_HEIGHT))
        self.set_visibility_mask(rectangles)
        super().draw()

    def reset_terminal_info(self):
        """Resets the terminal information of this window."""
        self.parent_info.reset()
