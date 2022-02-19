from .. import fcp
import importlib
import os
import sys
import pandas as pd
import pdb
import scipy.stats
import datetime
import time
import numpy as np
import copy
import decimal
import math
from .. colors import *
from .. utilities import RepeatedList
from .. import utilities as utl
from distutils.version import LooseVersion
from random import randint
from collections import defaultdict
from . layout import *
import warnings
import matplotlib as mpl
import matplotlib.pyplot as mplp
import matplotlib.ticker as ticker
import matplotlib.patches as patches
import matplotlib.dates as mdates
import matplotlib.font_manager as font_manager
from matplotlib.ticker import AutoMinorLocator, LogLocator, MaxNLocator, NullFormatter
import matplotlib.transforms as mtransforms
from matplotlib.patches import FancyBboxPatch
from matplotlib.collections import PatchCollection
import matplotlib.mlab as mlab
import warnings
from natsort import natsorted
warnings.filterwarnings('ignore', category=UserWarning)


def custom_formatwarning(msg, *args, **kwargs):
    # ignore everything except the message
    return 'Warning: ' + str(msg) + '\n'


warnings.formatwarning = custom_formatwarning
# weird error in boxplot with no groups
warnings.filterwarnings(
    "ignore", "invalid value encountered in double_scalars")

db = pdb.set_trace


def cbar_ticks(cbar, zmin, zmax):
    """
    Format cbar ticks and labels

    Args:
        cbar (colorbar obj)
        zmin (float): min z-value
        zmax (float): max z-value

    Returns:
        new tick labels
    """

    num_ticks = len(cbar.get_ticks())
    new_ticks = np.linspace(zmin, zmax, num_ticks)
    decimals = [utl.get_decimals(f) for f in new_ticks]
    decimals = [f - 1 if f > 0 else f for f in decimals]
    for it, nt in enumerate(new_ticks[0:-1]):
        new_ticks[it] = '{num:.{width}f}'.format(num=nt, width=decimals[it])
    return new_ticks


def iterticks(ax, minor=False):
    # this is deprecated in later versions of mpl but used in fcp so just
    # copying it here to avoid warnings or future removal
    if LooseVersion(mpl.__version__) >= LooseVersion('3.1'):
        major_locs = ax.get_majorticklocs()
        major_labels = ax.major.formatter.format_ticks(major_locs)
        major_ticks = ax.get_major_ticks(len(major_locs))
        yield from zip(major_ticks, major_locs, major_labels)
        # the minor ticks are a major slow down so only do when needed
        if minor:
            minor_locs = ax.get_minorticklocs()
            minor_labels = ax.minor.formatter.format_ticks(minor_locs)
            minor_ticks = ax.get_minor_ticks(len(minor_locs))
            yield from zip(minor_ticks, minor_locs, minor_labels)
    else:
        yield from getattr(ax, 'iter_ticks')()


def mplc_to_hex(color, alpha=True):
    """
    Convert mpl color to hex

    Args:
        color (tuple): matplotlib style color code
        alpha (boolean): include or exclude the alpha value
    """

    hexc = '#'
    for ic, cc in enumerate(color):
        if not alpha and ic == 3:
            continue
        hexc += '%s' % hex(int(cc * 255))[2:].zfill(2)

    return hexc


def mpl_get_ticks(ax, xon=True, yon=True, minor=False):
    """
    Divine a bunch of tick and label parameters for mpl layouts

    Args:
        ax (mpl.axes)

    Returns:
        dict of x and y ax tick parameters

    """

    tp = {}
    xy = []
    if xon:
        xy += ['x']
    if yon:
        xy += ['y']

    for vv in xy:
        tp[vv] = {}
        lim = getattr(ax, 'get_%slim' % vv)()
        tp[vv]['min'] = min(lim)
        tp[vv]['max'] = max(lim)
        tp[vv]['ticks'] = getattr(ax, 'get_%sticks' % vv)()
        tp[vv]['labels'] = [f for f in iterticks(
            getattr(ax, '%saxis' % vv), minor)]
        tp[vv]['label_vals'] = [f[1] for f in tp[vv]['labels']]
        tp[vv]['label_text'] = [f[2] for f in tp[vv]['labels']]
        try:
            tp[vv]['first'] = [i for i, f in enumerate(tp[vv]['labels'])
                               if f[1] >= tp[vv]['min'] and f[2] != ''][0]
        except:
            tp[vv]['first'] = -999
        try:
            tp[vv]['last'] = [i for i, f in enumerate(tp[vv]['labels'])
                              if f[1] <= tp[vv]['max'] and f[2] != ''][-1]
        except:
            tp[vv]['last'] = -999

    missing = [f for f in ['x', 'y'] if f not in tp.keys()]
    for mm in missing:
        tp[mm] = {}
        tp[mm]['ticks'] = []
        tp[mm]['labels'] = []
        tp[mm]['label_text'] = []
        tp[mm]['first'] = -999
        tp[mm]['last'] = -999

    return tp


class Layout(BaseLayout):

    def __init__(self, data, **kwargs):
        """
        Layout attributes and methods for matplotlib Figure

        Args:
            data (Data class): data values
            **kwargs: input args from user
        """

        global ENGINE
        ENGINE = 'mpl'

        self.rc_orig = mpl.rcParams.copy()

        if kwargs.get('tick_cleanup', True):
            mplp.style.use('classic')
        else:
            mplp.style.use('default')
        # Unless specified, close previous plots
        if not kwargs.get('hold', False):
            mplp.close('all')

        # Inherit the base layout properties
        BaseLayout.__init__(self, data, **kwargs)

        # Initialize other class variables
        self.label_col_height = 0
        self.label_row_left = 0
        self.label_row_width = 0
        self.title_wrap_bottom = 0

        # Weird spacing defaults out of our control
        self.fig_right_border = 6  # extra border on right side that shows up by default
        # this is differnt for inline; do we need to toggle on/off with show?
        self.legend_top_offset = 8
        self.legend_border = 3
        self.fig_legend_border = 5
        self.x_tick_xs = 0

        # Other
        self.set_colormap(data)

        # Update kwargs
        if not kwargs.get('save_ext'):
            kwargs['save_ext'] = '.png'
        self.kwargs = kwargs

    @property
    def bottom(self):
        """
        Height of the space to the bottom of the axes object
        """

        return 0

    @property
    def labtick_x(self):
        """
        Height of the x label + x tick labels + related whitespace
        """

        val = self.label_x.size[1] \
            + self.ws_label_tick * self.label_x.on \
            + self.tick_x

        return val

    @property
    def labtick_x2(self):
        """
        Height of the secondary x label + x tick labels + related
        whitespace
        """

        val = (self.label_x2.size[1]
               + self.ws_label_tick + 2*self.ws_ticks_ax
               + max(self.tick_labels_major_x2.size[1],
                     self.tick_labels_minor_x2.size[1])) * self.axes.twin_y

        return val

    @property
    def labtick_y(self):
        """
        Width of the y label + y tick labels + related whitespace
        """

        if self.pie.on:
            return 0

        val = self.label_y.size[0] \
            + self.ws_label_tick \
            + self.tick_y

        return val

    @property
    def labtick_y2(self):
        """
        Width of the secondary y label + y tick labels + related whitespace
        """

        val = (self.label_y2.size[0]
               + self.ws_label_tick
               + self.ws_ticks_ax
               + max(self.tick_labels_major_y2.size[0],
                     self.tick_labels_minor_y2.size[0])) * self.axes.twin_x

        return val

    @property
    def labtick_z(self):
        """
        Width of the z label + z tick labels + related whitespace
        """

        val = self.ws_label_tick * self.label_z.on \
            + self.tick_labels_major_z.size[0]

        return val

    @property
    def left(self):
        """
        Width of the space to the left of the axes object
        """

        left = self.ws_fig_label + self.labtick_y
        title_xs_left = self.title.size[0] / 2 \
            - (left
               + (self.axes.size[0] * self.ncol
                  + self.ws_col * (self.ncol - 1)) / 2)
        if title_xs_left < 0:
            title_xs_left = 0
        left += title_xs_left

        # pie labels
        left += self.pie.xs_left

        return left

    @property
    def legx(self):
        """
        Legend whitespace x is location == 0
        """

        if self.legend.location == 0 and self.legend._on:
            return self.legend.size[0] + self.ws_ax_leg + self.ws_leg_fig + \
                self.fig_legend_border + self.legend.edge_width
        else:
            return 0

    @property
    def legy(self):
        """
        Legend whitespace y is location == 11
        """

        if self.legend.location == 11 and self.legend._on:
            return self.legend.size[1]
        else:
            return 0

    @property
    def rc_label(self):
        """
        Width of an rc label with whitespace
        """

        return (self.label_row.size[0] + self.ws_label_row +
                2 * self.label_row.edge_width) * self.label_row.on

    @property
    def right(self):
        """
        Width of the space to the right of the axes object
        """

        # axis to fig right side ws with or without legend
        ws_ax_fig = (
            self.ws_ax_fig if not self.legend._on or self.legend.location != 0 else 0)

        # sum all parts
        right = ws_ax_fig \
            + self.labtick_y2 \
            + self.rc_label \
            + self.labtick_z \
            + self.x_tick_xs \
            + self.label_y2.size[0] \
            + (self.label_z.size[0] *
               (self.ncol if self.separate_labels else 1) +
               self.ws_ticks_ax * self.label_z.on) \

        # box title excess
        btitle_xs_right = 0
        if self.box_group_title.on:
            btitle_xs_right = (self.ws_ax_box_title + self.box_title) - \
                right - self.legx + \
                self.ws_ax_fig  # self.ws_ax_fig if not self.legend._on or self.legend.location != 0 else 0)
            if btitle_xs_right > 0:
                right += btitle_xs_right

        # Main figure title excess size
        title_xs_right = self.title.size[0] / 2 \
            - (right
               + (self.axes.size[0] * self.ncol
                  + self.ws_col * (self.ncol - 1)) / 2)
        if title_xs_right < 0:
            title_xs_right = 0
        right += title_xs_right

        # pie labels
        right += self.pie.xs_right

        return right

    @property
    def tick_x(self):
        """
        Height of the primary x ticks and whitespace
        """

        val = max(self.tick_labels_major_x.size[1],
                  self.tick_labels_minor_x.size[1]) \
            + self.ws_ticks_ax * self.tick_labels_major_x.on

        return val

    @property
    def tick_y(self):
        """
        Width of the primary y ticks and whitespace
        """

        val = max(self.tick_labels_major_y.size[0],
                  self.tick_labels_minor_y.size[0]) \
            + self.ws_ticks_ax

        return val

    @property
    def top(self):
        """
        Height of the space to the right of the axes object
        """

        return 0

    def add_box_labels(self, ir: int, ic: int, data):
        """
        Add box group labels and titles (JMP style)

        Args:
            ir: current axes row index
            ic: current axes column index
            data: fcp.data obj

        """

        num_cols = len(data.changes.columns)

        # Set up the label/title arrays to reflect the groups
        max_labels = data.changes.sum().max()
        self.box_group_label.obj[ir, ic] = np.array(
            [[None] * max_labels] * num_cols)
        self.box_group_label.obj_bg[ir, ic] = np.array(
            [[None] * max_labels] * num_cols)
        self.box_group_title.obj[ir, ic] = np.array([[None]] * num_cols)
        self.box_group_title.obj_bg[ir, ic] = np.array([[None]] * num_cols)

        # Create the labels
        for i in range(0, num_cols):
            k = num_cols-1-i
            sub = data.changes[num_cols-1-i][data.changes[num_cols-1-i] == 1]
            if len(sub) == 0:
                sub = data.changes[num_cols-1-i]

            # Group labels
            if self.box_group_label.on:
                # This array structure just makes one big list of all the labels
                # can we use it with multiple groups or do we need to reshape??
                # Probably need a 2D but that will mess up size_all indexing
                for j in range(0, len(sub)):

                    # set the width now since it is a factor of the axis size
                    if j == len(sub) - 1:
                        width = len(data.changes) - sub.index[j]
                    else:
                        width = sub.index[j+1] - sub.index[j]
                    width = width * self.axes.size[0] / len(data.changes)
                    label = data.indices.loc[sub.index[j], num_cols-1-i]
                    self.box_group_label.obj[ir, ic][i, j], \
                        self.box_group_label.obj_bg[ir, ic][i, j] = \
                        self.add_label(ir, ic, label,
                                       (sub.index[j] /
                                        len(data.changes), 0, 0, 0),
                                       rotation=0, size=[width, 20], offset=True,
                                       **self.make_kwargs(self.box_group_label,
                                                          ['size', 'rotation', 'position']))

            # Group titles
            if self.box_group_title.on and ic == data.ncol - 1:
                self.box_group_title.obj[ir, ic][i, 0], \
                    self.box_group_title.obj_bg[ir, ic][i, 0] = \
                    self.add_label(ir, ic, data.groups[k],
                                   # + self.ws_ax_box_title / self.axes.size[0],
                                   (1, 0, 0, 0),
                                   # 0, 0, 0),
                                   # (bottom - height/2 - 2 -
                                   #     self.box_group_title.size[k][1]/2) /
                                   #     self.axes.size[1]),
                                   # self.box_group_title.size[k],
                                   size=[0, 20],
                                   **self.make_kwargs(self.box_group_title,
                                                      ['position', 'size']))

    def add_box_points(self, ir, ic, x, y):
        """
        Plot x y points with or without jitter
        """

        if self.box_points.jitter:
            x = np.random.normal(x+1, 0.04, size=len(y))
        else:
            x = np.array([x+1]*len(y))
        if len(x) > 0 and len(y) > 0:
            pts = self.axes[ir, ic].plot(
                x, y,
                color=self.box_marker.fill_color,
                markersize=self.box_marker.size,
                marker=self.box_marker.type,
                markeredgecolor=self.box_points.edge_color,
                markerfacecolor='none',
                markeredgewidth=self.box_marker.edge_width,
                linestyle='none',
                zorder=2)
            return pts

    def add_cbar(self, ax, contour):
        """
        Add a color bar
        """

        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        size = '%s%%' % (100*self.cbar.size[0]/self.axes.size[0])
        pad = self.ws_ax_cbar/100
        cax = divider.append_axes('right', size=size, pad=pad)

        # Add the colorbar
        cbar = mplp.colorbar(contour, cax=cax)
        cbar.outline.set_edgecolor(self.cbar.edge_color[0])
        cbar.outline.set_linewidth(self.cbar.edge_width)

        # Style tick labels
        ticks_font = \
            font_manager.FontProperties(family=getattr(self, 'tick_labels_major_z').font,
                                        size=getattr(
                                            self, 'tick_labels_major_z').font_size,
                                        style=getattr(
                                            self, 'tick_labels_major_z').font_style,
                                        weight=getattr(self, 'tick_labels_major_z').font_weight)

        for text in cax.get_yticklabels():
            if getattr(self, 'tick_labels_major_z').rotation != 0:
                text.set_rotation(
                    getattr(self, 'tick_labels_major_z').rotation)
            text.set_fontproperties(ticks_font)
            text.set_bbox(dict(edgecolor=getattr(self, 'tick_labels_major_z').edge_color[0],
                               facecolor=getattr(
                                   self, 'tick_labels_major_z').fill_color[0],
                               linewidth=getattr(self, 'tick_labels_major_z').edge_width))

        # cbar.dividers.set_color('white')  # could enable
        # cbar.dividers.set_linewidth(2)

        return cbar

    def add_hvlines(self, ir, ic, df=None):
        """
        Add axhlines and axvlines

        Args:
            ir (int): subplot row index
            ic (int): subplot col index
            df (pd.DataFrame): current data
        """

        # Set default line attributes
        for axline in ['ax_hlines', 'ax_vlines', 'ax2_hlines', 'ax2_vlines']:
            ll = getattr(self, axline)
            func = self.axes.obj[ir, ic].axhline if 'hline' in axline \
                else self.axes.obj[ir, ic].axvline
            if ll.on:
                if hasattr(ll, 'by_plot') and ll.by_plot:
                    ival = utl.plot_num(ir, ic, self.ncol) - 1
                    if ival < len(ll.values):
                        line = func(ll.values[ival], color=ll.color[ival],
                                    linestyle=ll.style[ival],
                                    linewidth=ll.width[ival],
                                    zorder=ll.zorder)
                        if type(ll.text) is list and ll.text[ival] is not None:
                            self.legend.add_value(
                                ll.text[ival], [line], 'ref_line')

                else:
                    for ival, val in enumerate(ll.values):
                        if type(val) is str and type(df) is pd.DataFrame:
                            val = df[val].iloc[0]
                        line = func(val, color=ll.color[ival],
                                    linestyle=ll.style[ival],
                                    linewidth=ll.width[ival],
                                    zorder=ll.zorder)
                        if type(ll.text) is list and ll.text[ival] is not None:
                            self.legend.add_value(
                                ll.text[ival], [line], 'ref_line')

    def add_label(self, ir, ic, text='', position=None, rotation=0, size=None,
                  fill_color='#ffffff', edge_color='#aaaaaa', edge_width=1,
                  font='sans-serif', font_weight='normal', font_style='normal',
                  font_color='#666666', font_size=14, offset=False, **kwargs):
        """ Add a label to the plot
        This function can be used for title labels or for group labels applied
        to rows and columns when plotting facet grid style plots.
        Args:
            text (str):  label text
            position (tuple): label position tuple of form (left, right, top, bottom)
            rotation (int):  degrees of rotation
            fillcolor (str):  hex color code for label fill (default='#ffffff')
            edgecolor (str):  hex color code for label edge (default='#aaaaaa')
            color (str):  hex color code for label text (default='#666666')
            weight (str):  label font weight (use standard mpl weights like 'bold')
            font_size (int):  label font size (default=14)
        """

        # Set slight text offset
        if rotation == 270 and offset:
            offsetx = -2/self.axes.size[0]  # -font_size/self.axes.size[0]/4
        else:
            offsetx = 0
        if rotation == 0 and offset:
            offsety = -2/self.axes.size[1]  # -font_size/self.axes.size[1]/4
        else:
            offsety = 0

        # Define the label background
        rect = patches.Rectangle((position[0], position[3]),
                                 size[0] / self.axes.size[0],
                                 size[1]/self.axes.size[1],
                                 fill=True,
                                 transform=self.axes.obj[ir, ic].transAxes,
                                 facecolor=fill_color if type(fill_color) is str
                                 else fill_color[utl.plot_num(ir, ic, self.ncol)],
                                 edgecolor=edge_color if type(edge_color) is str
                                 else edge_color[utl.plot_num(ir, ic, self.ncol)],
                                 lw=edge_width if type(
                                     edge_width) is int else 1,
                                 clip_on=False, zorder=1)
        self.axes.obj[ir, ic].add_patch(rect)

        # Add the label text
        text = self.axes.obj[ir, ic].text(
            position[0] + offsetx,
            position[3] + offsety,
            text,
            transform=self.axes.obj[ir, ic].transAxes,
            horizontalalignment='center',  # backgroundcolor='#ff0000',
            verticalalignment='center', rotation=rotation,
            color=font_color, fontname=font, style=font_style,
            weight=font_weight, size=font_size)

        return text, rect

    def add_legend(self):
        """
        Add a figure legend
            TODO: add separate_label support?

        """

        def format_legend(self, leg):
            for itext, text in enumerate(leg.get_texts()):
                text.set_color(self.legend.font_color)
                if self.name not in ['hist', 'bar', 'pie', 'gantt']:
                    leg.legendHandles[itext]. \
                        _legmarker.set_markersize(self.legend.marker_size)
                    if self.legend.marker_alpha is not None:
                        leg.legendHandles[itext]. \
                            _legmarker.set_alpha(self.legend.marker_alpha)

            leg.get_title().set_fontsize(self.legend.font_size)
            leg.get_frame().set_facecolor(self.legend.fill_color[0])
            leg.get_frame().set_alpha(self.legend.fill_alpha)
            leg.get_frame().set_edgecolor(self.legend.edge_color[0])
            leg.get_frame().set_linewidth(self.legend.edge_width)

        if self.legend.on and len(self.legend.values) > 0:

            # Sort the legend keys
            if 'NaN' in self.legend.values['Key'].values:
                self.legend.del_value('NaN')

            # Set the font properties
            fontp = {}
            fontp['family'] = self.legend.font
            fontp['size'] = self.legend.font_size
            fontp['style'] = self.legend.font_style
            fontp['weight'] = self.legend.font_weight

            keys = list(self.legend.values['Key'])
            lines = list(self.legend.values['Curve'])

            if self.legend.location == 0:
                self.legend.obj = \
                    self.fig.obj.legend(lines, keys, loc='upper right',
                                        title=self.legend.text if self.legend is not True else '',
                                        bbox_to_anchor=(self.legend.position[1],
                                                        self.legend.position[2]),
                                        numpoints=self.legend.points,
                                        prop=fontp)
                format_legend(self, self.legend.obj)
            elif self.legend.location == 11:
                self.legend.obj = \
                    self.fig.obj.legend(lines, keys, loc='lower center',
                                        title=self.legend.text if self.legend is not True else '',
                                        bbox_to_anchor=(self.legend.position[0],
                                                        self.legend.position[2]),
                                        numpoints=self.legend.points,
                                        prop=fontp)
                format_legend(self, self.legend.obj)
            else:
                for irow, row in enumerate(self.axes.obj):
                    for icol, col in enumerate(row):
                        if self.legend.nleg == 1 and \
                                not(irow == 0 and icol == self.ncol - 1):
                            continue
                        self.legend.obj = \
                            col.legend(lines, keys, loc=self.legend.location,
                                       title=self.legend.text if self.legend is not True else '',
                                       numpoints=self.legend.points,
                                       prop=fontp)
                        self.legend.obj.set_zorder(102)
                        format_legend(self, self.legend.obj)

    def add_text(self, ir, ic, text=None, element=None, offsetx=0, offsety=0,
                 **kwargs):
        """
        Add a text box
        """

        # Shortcuts
        ax = self.axes.obj[ir, ic]
        if element is None:
            obj = self.text
        else:
            obj = getattr(self, element)
        text = text if text is not None else obj.text.values
        if type(text) is str:
            text = [text]

        # Set the coordinate so text is anchored to figure, axes, or the current
        #    data range
        coord = None if not hasattr(obj, 'coordinate') \
            else self.text.coordinate.lower()
        if coord == 'figure':
            transform = self.fig.obj.transFigure
        elif coord == 'data':
            transform = ax.transData
        else:
            transform = ax.transAxes
        units = 'pixel' if not hasattr(obj, 'units') else getattr(obj, 'units')

        # Add each text box
        for itext, txt in enumerate(text):
            kw = {}

            # Set style attributes
            attrs = ['rotation', 'font_color', 'font', 'fill_color', 'edge_color',
                     'font_style', 'font_weight', 'font_size']
            for attr in attrs:
                if attr in kwargs.keys():
                    kw[attr] = kwargs[attr]
                elif hasattr(obj, attr) and \
                        type(getattr(obj, attr)) is RepeatedList:
                    kw[attr] = getattr(obj, attr)[itext]
                elif hasattr(obj, attr):
                    kw[attr] = getattr(obj, attr)

            # Get position
            if 'position' in kwargs.keys():
                position = copy.copy(kwargs['position'])
            elif hasattr(obj, 'position') and \
                    type(getattr(obj, 'position')) is RepeatedList:
                position = copy.copy(getattr(obj, 'position')[itext])
            elif hasattr(obj, 'position'):
                position = copy.copy(getattr(obj, 'position'))

            # Convert position to correct units
            if units == 'pixel' and coord == 'figure':
                position[0] /= self.fig.size[0]
                offsetx /= self.fig.size[0]
                position[1] /= self.fig.size[1]
                offsety /= self.fig.size[1]
            elif units == 'pixel' and coord != 'data':
                position[0] /= self.axes.size[0]
                offsetx /= self.axes.size[0]
                position[1] /= self.axes.size[1]
                offsety /= self.axes.size[1]

            # Something goes weird with x = 0 so we need to adjust slightly
            if position[0] == 0:
                position[0] = 0.01

            # Add the text
            ax.text(position[0] + offsetx,
                    position[1] + offsety,
                    txt, transform=transform,
                    rotation=kw['rotation'],
                    color=kw['font_color'],
                    fontname=kw['font'],
                    style=kw['font_style'],
                    weight=kw['font_weight'],
                    size=kw['font_size'],
                    bbox=dict(facecolor=kw['fill_color'],
                              edgecolor=kw['edge_color']),
                    zorder=45)

    def close(self):
        """
        Close existing plot windows
        """

        mplp.close('all')

    def fill_between_lines(self, ir, ic, iline, x, lcl, ucl, obj, twin=False):
        """
        Shade a region between two curves

        Args:

        """

        if twin:
            ax = self.axes2.obj[ir, ic]
        else:
            ax = self.axes.obj[ir, ic]
        obj = getattr(self, obj)
        fc = obj.fill_color
        ec = obj.edge_color
        ax.fill_between(x, lcl, ucl,
                        facecolor=fc[iline] if type(
                            fc) is RepeatedList else fc,
                        edgecolor=ec[iline] if type(ec) is RepeatedList else ec)

    def get_axes_label_position(self):
        """
        Get the position of the axes labels
            self.label_@.position --> [left, right, top, bottom]
        """

        self.label_x.position[0] = 0.5
        self.label_x.position[3] = \
            (self.label_x.size[1]/2 - self.labtick_x) / self.axes.size[1]

        self.label_x2.position[0] = 0.5
        self.label_x2.position[3] = \
            1 + (self.labtick_x2 - self.label_x2.size[1] / 2) \
            / self.axes.size[1]

        self.label_y.position[0] = \
            (self.label_y.size[0]/2 - self.labtick_y) / self.axes.size[0]
        self.label_y.position[3] = 0.5

        self.label_y2.position[0] = 1 + self.labtick_y2 / self.axes.size[0]
        self.label_y2.position[3] = 0.5

        self.label_z.position[0] = 1 + (self.ws_ax_cbar + self.cbar.size[0] +
                                        self.tick_labels_major_z.size[0] + 2 * self.ws_label_tick) \
            / self.axes.size[0]
        self.label_z.position[3] = 0.5

    def get_element_sizes(self, data):
        """
        Calculate the actual rendered size of select elements by pre-plotting
        them.  This is needed to correctly adjust the figure dimensions

        Args:
            data (obj): data class object
        """

        # Render the figure to extract true dimensions of various elements
        saved = False
        self.fig.obj.canvas.draw()

        # labels
        for label in ['x', 'x2', 'y', 'y2', 'z', 'row', 'col', 'wrap']:
            lab = getattr(self, f'label_{label}')
            if not lab.on or lab.obj is None:
                continue
            #width, height = 0, 0
            for ir, ic in np.ndindex(lab.obj.shape):
                if lab.obj[ir, ic] is None:
                    continue

                # text label size
                bbox = lab.obj[ir, ic].get_window_extent()
                lab.size_all = (ir, ic, 0, 0, bbox.width, bbox.height, bbox.x0,
                                bbox.x1, bbox.y0, bbox.y1)

                # text label rect background size
                bbox = lab.obj_bg[ir, ic].get_window_extent()
                lab.size_all_bg = (ir, ic, 0, 0, bbox.width, bbox.height, bbox.x0,
                                   bbox.x1, bbox.y0, bbox.y1)

            # set max size
            width = lab.size_all.width.max()
            height = lab.size_all.height.max()
            if label in ['row', 'col', 'wrap']:
                width_bg, height_bg = lab.size
            else:
                width_bg = lab.size_all_bg.width.max()
                height_bg = lab.size_all_bg.height.max()

            lab.size = (max(width, width_bg), max(height, height_bg))

        # titles
        if self.title.on and type(self.title.text) is str:
            self.title.size = self.title.obj.get_window_extent().width, \
                self.title.obj.get_window_extent().height

        # legend
        if self.legend.on and self.legend.location in [0, 11]:
            self.legend.size = \
                [self.legend.obj.get_window_extent().width + self.legend_border,
                 self.legend.obj.get_window_extent().height + self.legend_border]

        # tick labels
        self.get_tick_label_sizes()

        if self.cbar.on:
            self.get_tick_label_size(self.cbar, 'z', '', 'major')

        # box labels and titles
        if self.box_group_label.on:
            lab = self.box_group_label
            for ir, ic in np.ndindex(lab.obj.shape):
                data.df_rc = data.subset(ir, ic)
                data.get_box_index_changes()
                divider = self.axes.size[0] / len(data.changes)
                if lab.obj[ir, ic] is None:
                    continue
                for ii, jj in np.ndindex(lab.obj[ir, ic].shape):
                    # get the available length for a label in units of box groups
                    changes = data.changes[len(data.changes.columns) - ii - 1].append(
                        pd.Series([1], index=[len(data.changes)]))
                    lens = np.diff(changes[changes == 1].index)

                    # text label size
                    if lab.obj[ir, ic][ii, jj] is None:
                        continue
                    bbox = lab.obj[ir, ic][ii, jj].get_window_extent()
                    label_max_width = lens[ii] * divider
                    if bbox.width > label_max_width:
                        # rotate labels that are longer than the box axis size
                        lab.obj[ir, ic][ii, jj].set_rotation(90)
                        bbox = lab.obj[ir, ic][ii, jj].get_window_extent()
                    lab.size_all = (ir, ic, ii, jj, bbox.width, bbox.height, bbox.x0,
                                    bbox.x1, bbox.y0, bbox.y1)

                    # text label bg size
                    if lab.obj[ir, ic][ii, jj].get_rotation() != 0:
                        # if we rotate the label, use the label size
                        # this will cause an issue if someone tries to color the
                        # rectangle behind the text but rotating the rectange itself
                        # doesn't work b/c the label may be longer than the
                        # rectangle itself
                        bbox = lab.obj[ir, ic][ii, 0].get_window_extent()
                    else:
                        bbox = lab.obj_bg[ir, ic][ii, 0].get_window_extent()
                    lab.size_all_bg = (ir, ic, ii, jj, bbox.width, bbox.height, bbox.x0,
                                       bbox.x1, bbox.y0, bbox.y1)

            # set max size
            width = lab.size_all.width.max()
            height = lab.size_all.height.max()
            width_bg = lab.size_all_bg.width.max()  # do we want this?
            height_bg = lab.size_all_bg.height.max()
            lab.size = (max(width, width_bg), max(height, height_bg))

        if self.box_group_title.on:
            lab = self.box_group_title
            for ir, ic in np.ndindex(lab.obj.shape):
                if lab.obj[ir, ic] is None:
                    continue
                for ii in range(0, len(lab.obj[ir, ic])):
                    # text label size
                    if lab.obj[ir, ic][ii, 0] is None:
                        continue
                    bbox = lab.obj[ir, ic][ii, 0].get_window_extent()
                    lab.size_all = (ir, ic, ii, 0, bbox.width, bbox.height, bbox.x0,
                                    bbox.x1, bbox.y0, bbox.y1)

                    # text label rect background size
                    bbox = lab.obj_bg[ir, ic][ii, 0].get_window_extent()
                    lab.size_all_bg = (ir, ic, ii, 0, bbox.width, bbox.height, bbox.x0,
                                       bbox.x1, bbox.y0, bbox.y1)

            # set max size
            width = lab.size_all.width.max()
            height = lab.size_all.height.max()
            width_bg = lab.size_all_bg.width.max()
            height_bg = lab.size_all_bg.height.max()

            lab.size = (max(width, width_bg), max(height, height_bg))

        # pie labels
        if self.pie.on:
            for ir, ic in np.ndindex(lab.obj.shape):
                bboxes = [f.get_window_extent() for f in self.pie.obj[1]]
                ax_bbox = self.axes.obj[ir, ic].get_window_extent()
                for ibox, bbox in enumerate(bboxes):
                    if self.pie.obj[1][ibox].get_text() == '':
                        continue
                    self.pie.size_all = (ir, ic, ibox, 0, bbox.width, bbox.height,
                                         bbox.x0, bbox.x1, bbox.y0, bbox.y1)

                if len(self.pie.size_all) > 0:
                    left = self.pie.size_all['x0'].min() - ax_bbox.x0
                    self.pie.xs_left = max(-left if left <
                                           0 else 0, self.pie.xs_left)

                    right = self.pie.size_all['x1'].max() - ax_bbox.x1
                    self.pie.xs_right = max(
                        right if right > 0 else 0, self.pie.xs_right)

                    bottom = self.pie.size_all['y0'].min() - ax_bbox.y0
                    self.pie.xs_bottom = max(-bottom if bottom <
                                             0 else 0, self.pie.xs_bottom)

                    top = self.pie.size_all['y1'].max() - ax_bbox.y1
                    self.pie.xs_top = max(
                        top if top > 0 else 0, self.pie.xs_top)

                if self.pie.explode:
                    for iwedge, wedge in enumerate(self.pie.explode):
                        if wedge == 0:
                            continue
                        # this is a bit of a hack and may not hold for all cases
                        # and ignores the orientation of the wedge that is
                        # exploding
                        self.pie.xs_left += wedge * self.axes.size[0] / 4
                        self.pie.xs_right += wedge * self.axes.size[0] / 4
                        self.pie.xs_top += wedge * self.axes.size[0] / 4
                        self.pie.xs_bottom += wedge * self.axes.size[0] / 4

            # # someday move labels to edge and draw a line from wedges to label
            # theta1 = self.pie.obj[0][0].theta1
            # theta2 = self.pie.obj[0][0].theta2
            # r = self.pie.obj[0][0].r
            # delta = (theta2 - theta1) / 2
            # x1, y1 = -1., 1.
            # x2 = -0.95 * r * np.sin(np.pi / 180 * delta)
            # y2 = 0.95 * r * np.cos(np.pi / 180 * delta)
            # self.axes.obj[0, 0].plot([x1, x2], [y1, y2], ".")
            # self.axes.obj[0, 0].annotate("",
            #             xy=(x1, y1), xycoords='data',
            #             xytext=(x2, y2), textcoords='data',
            #             arrowprops=dict(arrowstyle="-", color="0.5",
            #                             shrinkA=5, shrinkB=5,
            #                             patchA=None, patchB=None,
            #                             connectionstyle="arc,angleA=-90,angleB=0,armA=0,armB=40,rad=0",
            #                             ),
            #             )

        # if saved:
        #     os.remove(filename + '.png')

        return data

    def get_figure_size(self, data, **kwargs):
        """
        Determine the size of the mpl figure canvas in pixels and inches
        """

        debug = kwargs.get('debug_size', False)

        # Set some values for convenience
        self.ws_ax_leg = max(
            0, self.ws_ax_leg - self.labtick_y2) if self.legend.location == 0 else 0
        self.ws_leg_fig = self.ws_leg_fig if self.legend.location == 0 else 0
        if self.legend.location == 0 and self.legend.on:
            self.ws_ax_fig = 0
        self.fig_legend_border = self.fig_legend_border if self.legend.location == 0 else 0
        self.box_labels = 0
        if self.box_group_label.on and self.box_group_label.size != [0, 0]:
            heights = \
                self.box_group_label.size_all_bg.groupby('ii').max()['height']
            heights *= (1 + 2 * self.box_group_label.padding / 100)
            self.box_labels = heights.sum()
        self.box_title = 0
        if self.box_group_title.on and self.legend.size[1] > self.axes.size[1]:
            self.box_title = self.box_group_title.size[0]
        elif self.box_group_title.on and self.box_group_title.size != [0, 0] and \
                self.box_group_title.size[0] > self.legend.size[0]:
            self.box_title = self.box_group_title.size[0] - self.legend.size[0]

        # Adjust the column and row whitespace
        if self.box_group_label.on and self.label_wrap.on and 'ws_row' not in kwargs.keys():
            self.ws_row = self.box_labels + self.title_wrap.size[1]
        else:
            self.ws_row += self.box_labels

        if self.title.on:
            self.ws_title = self.ws_fig_title + \
                self.title.size[1] + self.ws_title_ax
        else:
            self.ws_title = self.ws_fig_ax

        if self.cbar.on and utl.kwget(kwargs, self.fcpp, 'ws_col', -999) == -999:
            self.ws_col = self.labtick_z

        # separate ticks and labels
        if (self.separate_ticks or self.axes.share_y == False) and not self.cbar.on:
            self.ws_col = max(self.tick_y + self.ws_ax_fig, self.ws_col_def)
        elif (self.separate_ticks or self.axes.share_y == False) and self.cbar.on:
            self.ws_col += self.tick_y
        if self.separate_ticks or \
                (self.axes.share_x == False and self.box.on == False):
            self.ws_row += max(self.tick_labels_major_x.size[1],
                               self.tick_labels_minor_x.size[1]) + \
                self.ws_ticks_ax
        if self.separate_labels and not self.separate_ticks:
            self.ws_col += self.label_y.size[0] + \
                self.ws_label_tick + self.ws_fig_label
            self.ws_row += self.label_x.size[1] + \
                self.ws_label_tick + self.ws_fig_label
        elif self.separate_labels:
            self.ws_col += self.labtick_y - self.tick_y + self.ws_ax_label_xs
            if self.cbar.on:
                self.ws_col += self.ws_label_tick

        if self.name == 'heatmap' and \
                self.heatmap.cell_size is not None and \
                data.num_x is not None:
            self.axes.size = [self.heatmap.cell_size * data.num_x,
                              self.heatmap.cell_size * data.num_y]
            self.label_col.size[0] = self.axes.size[0]
            self.label_row.size[1] = self.axes.size[1]

        # imshow ax adjustment
        if self.name == 'imshow':
            if data.wh_ratio >= 1:
                self.axes.size[1] = self.axes.size[0] / data.wh_ratio
            else:
                self.axes.size[0] = self.axes.size[1] * data.wh_ratio

        # Set figure width
        self.fig.size[0] = self.left + self.axes.size[0] * self.ncol + \
            self.right + self.legx + self.ws_col * (self.ncol - 1) - \
            (self.fig_legend_border if self.legend._on else 0) + \
            (self.cbar.size[0] + self.ws_ax_cbar) * self.ncol

        # Figure height
        self.fig.size[1] = int(
            self.ws_title +
            (self.label_col.size[1] + self.ws_label_col) * self.label_col.on +
            self.title_wrap.size[1] + self.label_wrap.size[1] +
            self.labtick_x2 +
            self.axes.size[1]*self.nrow +
            self.labtick_x +
            self.ws_fig_label +
            self.ws_row * (self.nrow - 1) +
            self.box_labels) + \
            self.legy + \
            self.pie.xs_top + self.pie.xs_bottom

        # Debug output
        if debug:
            print('self.fig.size[0] = %s' % self.fig.size[0])
            vals = ['ws_fig_label', 'label_y', 'ws_label_tick', 'tick_labels_major_y',
                    'tick_labels_minor_y', 'ws_ticks_ax', 'axes', 'cbar', 'ws_ax_cbar',
                    'ws_col', 'ws_ax_leg', 'legend', 'ws_leg_fig', 'label_y2',
                    'ws_label_tick', 'ws_ticks_ax', 'tick_labels_major_y2', 'label_row',
                    'ws_label_row', 'label_z', 'tick_labels_major_z', 'box_title',
                    'ncol', 'labtick_y', 'labtick_y2', 'labtick_z']
            for val in vals:
                if isinstance(getattr(self, val), Element):
                    print('   %s.size[0] = %s' %
                          (val, getattr(self, val).size[0]))
                else:
                    print('   %s = %s' % (val, getattr(self, val)))
            print('self.fig.size[1] = %s' % self.fig.size[1])
            vals = ['ws_fig_title', 'title', 'ws_title_ax', 'ws_fig_ax',
                    'label_col', 'ws_label_col', 'title_wrap',
                    'label_wrap', 'label_x2', 'ws_ticks_ax', 'tick_labels_major_x2',
                    'axes', 'label_x', 'ws_label_tick', 'tick_labels_major_x', 'ws_ticks_ax',
                    'ws_fig_label', 'ws_row', 'box_labels',
                    'nrow', 'labtick_x', 'labtick_x2', 'ws_title']
            for val in vals:
                if isinstance(getattr(self, val), Element):
                    print('   %s.size[1] = %s' %
                          (val, getattr(self, val).size[1]))
                else:
                    print('   %s = %s' % (val, getattr(self, val)))

        # Account for legends longer than the figure
        header = self.ws_title + \
            (self.label_col.size[1] + self.ws_label_col) * self.label_col.on + \
            self.title_wrap.size[1] + self.label_wrap.size[1] + \
            self.labtick_x2

        if self.legend.size[1] + header > self.fig.size[1]:
            self.legend.overflow = self.legend.size[1] + \
                header - self.fig.size[1]
        self.fig.size[1] += self.legend.overflow

    def get_legend_position(self):
        """
        Get legend position
        """

        offset_box = 0
        if self.legend.location == 0:
            if self.box_group_title.on and self.legend.size[1] > self.axes.size[1]:
                offset_box = max(self.box_group_title.size)[0]
                self.legend.position[1] = 1 + \
                    (self.fig_legend_border -
                     self.ws_leg_fig) / self.fig.size[0]
            else:
                self.legend.position[1] = 1 + \
                    (self.fig_legend_border -
                     self.ws_leg_fig) / self.fig.size[0]
            self.legend.position[2] = \
                self.axes.position[2] + self.legend_top_offset/self.fig.size[1]
        if self.legend.location == 11:
            self.legend.position[1] = 0.5
            self.legend.position[2] = 0

    def get_rc_label_position(self):
        """
        Get option group label positions
            self.label.position --> [left, right, top, bottom]
        """

        self.label_row.position[0] = \
            (self.axes.size[0] + self.labtick_y2 + self.ws_label_row +
             self.label_row.edge_width +
             (self.ws_ax_cbar if self.cbar.on else 0) + self.cbar.size[0] +
             self.labtick_z + self.label_z.size[0])/self.axes.size[0]

        self.label_col.position[3] = (self.axes.size[1] + self.ws_label_col +
                                      self.labtick_x2)/self.axes.size[1]

        self.label_wrap.position[3] = 1

        # # there is some incredible weirdness with cbars on imshow.  Here is a stupid hack
        # # the hack is moved to set_figure_final_layout and may not be needed here
        # hack = 0
        # if self.name in ['imshow']:
        #     hack += 1 * (self.ncol - 1) if self.cbar.on else 0
        #     if not self.cbar.on and self.ncol == 1:
        #         self.label_wrap.size[0] += 1
        #         hack += 1 * (self.ncol)
        #     elif self.cbar.on and self.ncol > 1:
        #         hack += 2

        # self.title_wrap.size[0] = self.ncol * self.title_wrap.size[0] + \
        #     (self.ncol - 1) * self.ws_col + hack + \
        #     ((self.cbar.size[0] + self.ws_ax_cbar)
        #      * self.ncol if self.cbar.on else 0)

        self.title_wrap.position[3] = 1 + \
            self.label_wrap.size[1] / self.axes.size[1]

    def get_subplots_adjust(self):
        """
        Calculate the subplots_adjust parameters for the axes
            self.axes.position --> [left, right, top, bottom]
        """

        self.axes.position[0] = int(self.left) / self.fig.size[0]

        # note: if using cbar, self.axes.position[1] = 1 means the edge of the
        # cbar is at the edge of the figure (+2 is a fudge to get the right image size)
        self.axes.position[1] = \
            self.axes.position[0] + \
            int(self.axes.size[0] * self.ncol +
                self.ws_col * (self.ncol - 1) +
                self.cbar.on * (self.cbar.size[0] + self.ws_ax_cbar + 2) * (self.ncol) +
                (self.label_z.size[0] * (self.ncol - 1) if self.separate_labels else 0)) \
            / self.fig.size[0]

        self.axes.position[2] = \
            1 - (self.ws_title + self.title_wrap.size[1] +
                 (self.label_col.size[1] + self.ws_label_col) * self.label_col.on +
                 self.label_wrap.size[1] + self.labtick_x2 + self.pie.xs_top) / self.fig.size[1]

        self.axes.position[3] = \
            (self.labtick_x + self.ws_fig_label + self.box_labels +
             self.legend.overflow + self.pie.xs_bottom +
             (self.legend.size[1] if self.legend.location == 11 else 0)) / self.fig.size[1]

    def get_tick_label_size(self, ax, tick: str, tick_num: str, which: str,
                            alias: str = ''):
        """
        Get the size of the tick labels (plot must be rendered)

        Args:
            ax: the axes object for the labels of interest
            tick: name of the tick axes
            tick_num: '' or '2' for secondary
            which: 'major' or 'minor'

        """

        if tick == 'x':  # what about z??
            idx = 0
        else:
            idx = 1

        for ir, ic in np.ndindex(ax.obj.shape):
            # Get the tick label Element
            minor = True if which == 'minor' else False
            tt = getattr(self, f'tick_labels_{which}_{tick}{tick_num}')
            # or tt.obj[ir, ic] == None: # this doesn't work!
            if tt.obj is None:
                continue
            if not tt.on:
                return

            # Get the VISIBLE tick labels and add references to the Element object
            if tick == 'z':
                tlabs = getattr(
                    ax.obj[ir, ic].ax, f'get_yticklabels')(minor=minor)
                vmin, vmax = getattr(ax.obj[ir, ic].ax, f'get_ylim')()
            else:
                tlabs = getattr(
                    ax.obj[ir, ic], f'get_{tick}ticklabels')(minor=minor)
                vmin, vmax = getattr(ax.obj[ir, ic], f'get_{tick}lim')()
            tt.limits = [vmin, vmax]
            tlabs = [f for f in tlabs if min(vmin, vmax) <=
                     f.get_position()[idx] <= max(vmin, vmax)]
            tt.obj[ir, ic] = tlabs

            # Get the label sizes and store sizes as 2D array
            bboxes = [t.get_window_extent() for t in tlabs]
            tt.size_all = ([ir for f in bboxes],
                           [ic for f in bboxes],
                           [0 for f in bboxes],
                           [0 for f in bboxes],
                           [f.width for f in bboxes],
                           [f.height for f in bboxes],
                           [f.x0 for f in bboxes],
                           [f.x1 for f in bboxes],
                           [f.y0 for f in bboxes],
                           [f.y1 for f in bboxes],
                           )

        if len(tt.size_all) == 0:
            return

        tt.size = [tt.size_all.width.max(), tt.size_all.height.max()]

    def get_tick_label_sizes(self):
        """
        Get the tick label sizes
        """

        for tick in ['x', 'y']:
            getattr(self, f'tick_labels_major_{tick}').size_all_reset()
            getattr(self, f'tick_labels_minor_{tick}').size_all_reset()

            # primary axes
            self.get_tick_label_size(self.axes, tick, '', 'major')
            self.get_tick_label_size(self.axes, tick, '', 'minor')

            # secondary axes
            if self.axes2.on:
                self.get_tick_label_size(self.axes2, tick, '2', 'major')
                self.get_tick_label_size(self.axes2, tick, '2', 'minor')

    def get_tick_overlaps(self):
        """
        Deal with overlapping and out of range ticks
        """

        if not self.tick_cleanup:
            return

        xticks = self.tick_labels_major_x
        yticks = self.tick_labels_major_y
        sf = 1.5  # scale factor for tick font size

        # TODO:: minor overlaps
        # TODO:: self.axes2

        for ir, ic in np.ndindex(self.axes.obj.shape):
            # size_all by idx:
            #   ir, ic, width, height, x0, x1, y0, y1
            if len(xticks.size_all) > 0:
                xticks_size_all = \
                    xticks.size_all[(xticks.size_all.ir == ir) &
                                    (xticks.size_all.ic == ic)]
                xticks_size_all = np.array(xticks_size_all)
            else:
                xticks_size_all = []
            if len(yticks.size_all) > 0:
                yticks_size_all = \
                    yticks.size_all[(yticks.size_all.ir == ir) &
                                    (yticks.size_all.ic == ic)]
                yticks_size_all = np.array(yticks_size_all)
            else:
                yticks_size_all = []

            # Prevent single tick label axis
            if len(xticks_size_all) == 1:
                self.add_text(ir, ic, str(xticks.limits[1]),
                              position=[self.axes.size[0] -
                                        xticks.size_all.loc[0,
                                                            'width'] / 2 / sf,
                                        -xticks.size_all.loc[0, 'height']],
                              font_size=xticks.font_size / sf)

            # Overlapping x-y origin
            if len(xticks_size_all) > 0 and len(yticks_size_all) > 0:
                idx = xticks.size_cols.index('width')
                xw, xh, xx0, xx1, xy0, xy1 = xticks_size_all[0][idx:]
                xc = (xx0 + (xx1 - xx0) / 2, xy0 + (xy0 - xy1) / 2)
                yw, yh, yx0, yx1, yy0, yy1 = yticks_size_all[0][idx:]
                yc = (yx0 + (yx1 - yx0) / 2, yy0 + (yy0 - yy1) / 2)
                if utl.rectangle_overlap((xw, xh, xc), (yw, yh, yc)):
                    if self.tick_cleanup == 'remove':
                        yticks.obj[ir, ic][0].set_visible(False)
                    else:
                        xticks.obj[ir, ic][0].set_size(xticks.font_size / sf)
                        yticks.obj[ir, ic][0].set_size(yticks.font_size / sf)

            # Overlapping grid plot at x-origin
            if ic > 0 and len(xticks_size_all) > 0:
                idx = xticks.size_cols.index('x0')
                ax_x0 = self.axes.obj[ir, ic].get_window_extent().x0
                tick_x0 = xticks_size_all[0][idx]
                if ax_x0 - tick_x0 > self.ws_col:
                    slop = xticks.obj[ir, ic][0].get_window_extent().width / 2
                    if self.tick_cleanup == 'remove' or \
                            slop / sf > self.ws_col:
                        xticks.obj[ir, ic][0].set_visible(False)
                    else:
                        xticks.obj[ir, ic][0].set_size(xticks.font_size / sf)

            # TODO: Overlapping grid plot at y-origin

            # Overlapping ticks on same axis
            if len(xticks_size_all) > 0:
                idx = xticks.size_cols.index('x0')
                xbbox = xticks_size_all[:, idx:idx+2]
                ol = (xbbox[1:, 0] - xbbox[0:-1, 1]) < 0
                # pad to account for last tick
                ol = np.concatenate([ol, [True]])
                if any(ol):
                    for iol, ool in enumerate(ol[:-1]):
                        if ool and ol[iol + 1] and \
                                xticks.obj[ir, ic][iol+1].get_visible():
                            xticks.obj[ir, ic][iol+1].set_visible(False)
                            ol[iol+1] = False

            if len(yticks_size_all) > 0:
                ybbox = yticks_size_all[:, -2:]
                # don't think this matters
                # if ybbox[0:2, 0].argmax() == 1:
                #     # ascending ticks
                #     ol = (ybbox[1:, 0] - ybbox[0:-1, 1]) < 0
                # else:
                #     # descending ticks
                #     ol = (ybbox[0:-1, 0] - ybbox[1:, 1]) < 0
                ol = (ybbox[1:, 0] - ybbox[0:-1, 1]) < 0
                # pad to account for last tick
                ol = np.concatenate([ol, [True]])
                if any(ol):
                    for iol, ool in enumerate(ol[:-1]):
                        if ool and ol[iol + 1] and \
                                yticks.obj[ir, ic][iol+1].get_visible():
                            yticks.obj[ir, ic][iol+1].set_visible(False)
                            ol[iol+1] = False

    def get_tick_xs(self):

        # Ticks at the edge of the plot

        xticks = self.tick_labels_major_x
        yticks = self.tick_labels_major_y
        sf = 1.5  # scale factor for tick font size

        # TODO:: minor overlaps
        # TODO:: self.axes2

        for ir, ic in np.ndindex(self.axes.obj.shape):
            # size_all by idx:
            #   ir, ic, width, height, x0, x1, y0, y1
            if len(xticks.size_all) > 0:
                xticks_size_all = \
                    xticks.size_all[(xticks.size_all.ir == ir) &
                                    (xticks.size_all.ic == ic)]
                xticks_size_all = np.array(xticks_size_all)
            else:
                xticks_size_all = []
            if len(yticks.size_all) > 0:
                yticks_size_all = \
                    yticks.size_all[(yticks.size_all.ir == ir) &
                                    (yticks.size_all.ic == ic)]
                yticks_size_all = np.array(yticks_size_all)
            else:
                yticks_size_all = []

            if len(xticks_size_all) > 0:
                idx = xticks.size_cols.index('x1')
                xxs = self.axes.obj[ir, ic].get_window_extent().x1 \
                    + self.right \
                    - xticks_size_all[-1][idx]
                if xxs < 0:
                    self.x_tick_xs = -int(np.floor(xxs)) + 1
            if len(yticks_size_all) > 0:
                idx = xticks.size_cols.index('y0')
                yxs = self.axes.obj[ir, ic].get_window_extent().y1 \
                    + self.top \
                    - yticks_size_all[-1][idx]
                if yxs < 0:
                    self.y_tick_xs = -int(np.floor(yxs)) + \
                        1  # not currently used

    def get_title_position(self):
        """
        Calculate the title position
            self.title.position --> [left, right, top, bottom]
        """

        col_label = (self.label_col.size[1] +
                     self.ws_label_col * self.label_col.on) + \
                    (self.label_wrap.size[1] +
                     self.ws_label_col * self.label_wrap.on)
        self.title.position[0] = self.ncol / 2
        if self.label_wrap.size[1] > 0:
            title_height = 0
        else:
            # this is an offset from somewhere I don't know
            title_height = self.title.size[1] / 2 - 2
        self.title.position[3] = 1+(self.ws_title_ax +
                                    col_label + title_height +
                                    self.label_wrap.size[1]) / self.axes.size[1]
        self.title.position[2] = self.title.position[3] + (self.ws_title_ax +
                                                           self.title.size[1])/self.axes.size[1]

    def make_figure(self, data, **kwargs):
        """
        Make the figure and axes objects
        """

        # Create the subplots
        #   Note we don't have the actual element sizes until rendereing
        #   so we use an approximate size based upon what is known
        self.get_figure_size(data, **kwargs)
        self.fig.obj, self.axes.obj = \
            mplp.subplots(data.nrow, data.ncol,
                          figsize=[self.fig.size_inches[0],
                                   self.fig.size_inches[1]],
                          sharex=self.axes.share_x,
                          sharey=self.axes.share_y,
                          dpi=self.fig.dpi,
                          facecolor=self.fig.fill_color[0],
                          edgecolor=self.fig.edge_color[0],
                          linewidth=self.fig.edge_width,
                          )

        # Set default axes visibility
        self.axes.visible = np.array([[True]*self.ncol]*self.nrow)

        # Reformat the axes variable if it is only one plot
        if not type(self.axes.obj) is np.ndarray:
            self.axes.obj = np.array([self.axes.obj])
        if len(self.axes.obj.shape) == 1:
            if data.nrow == 1:
                self.axes.obj = np.reshape(self.axes.obj, (1, -1))
            else:
                self.axes.obj = np.reshape(self.axes.obj, (-1, 1))

        # Twinning
        self.axes2.obj = self.obj_array
        if self.axes.twin_x:
            for ir, ic in np.ndindex(self.axes2.obj.shape):
                self.axes2.obj[ir, ic] = self.axes.obj[ir, ic].twinx()
        elif self.axes.twin_y:
            for ir, ic in np.ndindex(self.axes2.obj.shape):
                self.axes2.obj[ir, ic] = self.axes.obj[ir, ic].twiny()

        return data

    def plot_bar(self, ir, ic, iline, df, x, y, leg_name, data, stacked, std,
                 ngroups, xvals, inst, total):
        """
        Plot bar graph
        """

        ax = self.axes.obj[ir, ic]
        idx = np.where(np.isin(xvals, df.index))[0]
        ixvals = list(range(0, len(xvals)))
        kwargs = {}

        # Orientation
        if self.bar.horizontal:
            bar = ax.barh
            axx = 'y'
            if self.bar.stacked:
                kwargs['height'] = self.bar.width
                if iline > 0:
                    if type(stacked) is pd.Series:
                        stacked = stacked.loc[xvals[idx]].values
                    kwargs['bottom'] = stacked
            else:
                #kwargs['height'] = self.bar.width / ngroups
                #idx = [f + iline * (kwargs['height']) for f in idx]
                kwargs['height'] = self.bar.width / ngroups
                width_offset = self.bar.width / total.values
                idx = [f + inst[i] * kwargs['height']
                       for i, f in enumerate(idx)]
                init_off = (total - 1) / 2 * kwargs['height']
                idx = list((idx - init_off).values)
        else:
            bar = ax.bar
            axx = 'x'
            if self.bar.stacked:
                kwargs['width'] = self.bar.width
                if iline > 0:
                    if type(stacked) is pd.Series:
                        stacked = stacked.loc[xvals[idx]].values
                    kwargs['bottom'] = stacked
            else:
                kwargs['width'] = self.bar.width / ngroups
                width_offset = self.bar.width / total.values
                idx = [f + inst[i] * kwargs['width']
                       for i, f in enumerate(idx)]
                init_off = (total - 1) / 2 * kwargs['width']
                idx = list((idx - init_off).values)

        if self.bar.color_by_bar:
            edgecolor = [self.bar.edge_color[i]
                         for i, f in enumerate(df.index)]
            fillcolor = [self.bar.fill_color[i]
                         for i, f in enumerate(df.index)]
        else:
            edgecolor = self.bar.edge_color[(iline, leg_name)]
            fillcolor = self.bar.fill_color[(iline, leg_name)]

        # Error bars
        if std is not None and self.bar.horizontal:
            kwargs['xerr'] = std
        elif std is not None:
            kwargs['yerr'] = std

        # Plot
        bb = bar(idx, df.values, align=self.bar.align,
                 linewidth=self.bar.edge_width,
                 edgecolor=edgecolor, color=fillcolor,
                 ecolor=self.bar.error_color, **kwargs)

        # Set ticks
        getattr(ax, 'set_%sticks' % axx)(ixvals)
        getattr(ax, 'set_%sticklabels' % axx)(xvals)
        if iline == 0:
            # Update ranges
            new_ticks = getattr(ax, 'get_%sticks' % axx)()
            tick_off = [f for f in new_ticks if f >= 0][0]
            if self.bar.horizontal:
                axx = 'y'
                data.ranges[ir, ic]['xmin'] = data.ranges[ir, ic]['ymin']
                data.ranges[ir, ic]['xmax'] = data.ranges[ir, ic]['ymax']
                data.ranges[ir, ic]['ymin'] = None
                data.ranges[ir, ic]['ymax'] = None
            else:
                axx = 'x'
            xoff = 3 * self.bar.width / 4
            if data.ranges[ir, ic]['%smin' % axx] is None:
                data.ranges[ir, ic]['%smin' % axx] = -xoff + tick_off
            else:
                data.ranges[ir, ic]['%smin' % axx] += tick_off
            if data.ranges[ir, ic]['%smax' % axx] is None:
                data.ranges[ir, ic]['%smax' % axx] = len(
                    xvals) - 1 + xoff + tick_off
            else:
                data.ranges[ir, ic]['%smax' % axx] += tick_off

        # Legend
        if leg_name is not None:
            handle = [patches.Rectangle((0, 0), 1, 1,
                      color=self.bar.fill_color[(iline, leg_name)])]
            self.legend.add_value(leg_name, handle, 'lines')

        return data

    def plot_box(self, ir, ic, data, **kwargs):
        """ Plot boxplot data

        Args:
            ir (int): subplot row index
            ic (int): subplot column index
            data (pd.DataFrame): data to plot

        Keyword Args:
            any kwargs allowed by the plotter function selected

        Returns:
            return the box plot object
        """

        bp = None

        if self.violin.on:
            bp = self.axes.obj[ir, ic].violinplot(data,
                                                  showmeans=False,
                                                  showextrema=False,
                                                  showmedians=False,
                                                  )
            for ipatch, patch in enumerate(bp['bodies']):
                patch.set_facecolor(self.violin.fill_color[ipatch])
                patch.set_edgecolor(self.violin.edge_color[ipatch])
                patch.set_alpha(self.violin.fill_alpha)
                patch.set_zorder(2)
                patch.set_lw(self.violin.edge_width)
                if self.violin.box_on:
                    q25 = np.percentile(data[ipatch], 25)
                    med = np.percentile(data[ipatch], 50)
                    q75 = np.percentile(data[ipatch], 75)
                    iqr = q75 - q25
                    offset = 0.05 * len(data) / 7
                    bb = mtransforms.Bbox([[1 + ipatch - offset, q25],
                                           [1 + ipatch + offset, q75]])
                    p_bbox = FancyBboxPatch((bb.xmin, bb.ymin),
                                            abs(bb.width), abs(bb.height),
                                            boxstyle="round,pad=0, rounding_size=0.05",
                                            ec="none", fc=self.violin.box_color, zorder=12)
                    self.axes.obj[ir, ic].add_patch(p_bbox)
                    whisker_max = min(max(data[ipatch]), q75 + 1.5 * iqr)
                    whisker_min = max(min(data[ipatch]), q25 - 1.5 * iqr)
                    self.axes.obj[ir, ic].plot([ipatch + 1, ipatch + 1],
                                               [whisker_min, whisker_max],
                                               linestyle=self.violin.whisker_style,
                                               color=self.violin.whisker_color,
                                               linewidth=self.violin.whisker_width)
                    self.axes.obj[ir, ic].plot([ipatch + 1], [med],
                                               marker=self.violin.median_marker,
                                               color=self.violin.median_color,
                                               markersize=self.violin.median_size,
                                               markeredgecolor=self.violin.median_color,
                                               zorder=13)

        elif self.box.on and not self.violin.on:
            bp = self.axes.obj[ir, ic].boxplot(data,
                                               labels=[''] * len(data),
                                               showfliers=False,
                                               medianprops={
                                                   'color': self.box.median_color},
                                               notch=self.box.notch,
                                               patch_artist=True,
                                               zorder=3)  # ,
            # widths=self.box.width.values[0]
            #      if len(self.box.width.values) == 1
            #     else self.box.width.values)
            for ipatch, patch in enumerate(bp['boxes']):
                patch.set_edgecolor(self.box.edge_color[ipatch])
                patch.set_facecolor(self.box.fill_color[ipatch])
                patch.set_alpha(self.box.fill_alpha)
                patch.set_lw(self.box.edge_width)
                patch.set_ls(self.box.style[ipatch])
            for ipatch, patch in enumerate(bp['whiskers']):
                patch.set_color(self.box_whisker.color[int(ipatch/2)])
                patch.set_lw(1)  # self.box_whisker.width[ipatch])
                patch.set_ls(self.box_whisker.style[ipatch])
            for ipatch, patch in enumerate(bp['caps']):
                patch.set_color(self.box_whisker.color[int(ipatch/2)])
                patch.set_lw(self.box_whisker.width[ipatch])
                patch.set_ls(self.box_whisker.style[ipatch])

        ll = ['' for f in self.axes.obj[ir, ic].get_xticklabels()]
        self.axes.obj[ir, ic].set_xticklabels(ll)
        self.axes.obj[ir, ic].set_xlim(0.5, len(data) + 0.5)

        return bp

    def plot_contour(self, ir, ic, ax, df, x, y, z, ranges):
        """
        Plot a contour plot
        """

        # Convert data type
        xx = np.array(df[x])
        yy = np.array(df[y])
        zz = np.array(df[z])

        # Make the grid
        xi = np.linspace(min(xx), max(xx))
        yi = np.linspace(min(yy), max(yy))
        if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
            zi = mlab.griddata(xx, yy, zz, xi, yi, interp=self.contour.interp)
        else:
            zi = scipy.interpolate.griddata((xx, yy), zz,
                                            (xi[None, :], yi[:, None]),
                                            method=self.contour.interp)

        # Deal with out of range values
        zi[zi >= ranges['zmax']] = ranges['zmax']
        zi[zi <= ranges['zmin']] = ranges['zmin']

        # Set the contours
        levels = np.linspace(ranges['zmin']*0.999, ranges['zmax']*1.001,
                             self.contour.levels)

        # Plot
        if self.contour.filled:
            cc = ax.contourf(xi, yi, zi, levels, cmap=self.cmap, zorder=2)
        else:
            cc = ax.contour(xi, yi, zi, levels,
                            linewidths=self.contour.width.values,
                            cmap=self.cmap, zorder=2)

        # Add a colorbar
        if self.cbar.on:
            self.cbar.obj[ir, ic] = self.add_cbar(ax, cc)
            new_ticks = cbar_ticks(
                self.cbar.obj[ir, ic], ranges['zmin'], ranges['zmax'])
            self.cbar.obj[ir, ic].set_ticks(new_ticks)

        # Show points
        if self.contour.show_points:
            ax.scatter(xx, yy, marker=self.markers.type[0],
                       c=self.markers.fill_color[0]
                       if self.markers.filled else 'none',
                       edgecolors=self.markers.edge_color[0],
                       linewidths=self.markers.edge_width[0],
                       s=self.markers.size[0],
                       zorder=40)

        return cc, self.cbar.obj

    def plot_gantt(self, ir, ic, df, x, y, iline, leg_name, ranges, yvals, ngroups):
        """
        Plot gantt graph
        """

        ax = self.axes.obj[ir, ic]
        bar = ax.broken_barh

        # Set the color values
        if self.gantt.color_by_bar:
            edgecolor = [self.gantt.edge_color[i]
                         for i, f in enumerate(df.index)]
            fillcolor = [self.gantt.fill_color[i]
                         for i, f in enumerate(df.index)]
        else:
            edgecolor = [self.gantt.edge_color[(iline, leg_name)]
                         for i, f in enumerate(df.index)]
            fillcolor = [self.gantt.fill_color[(iline, leg_name)]
                         for i, f in enumerate(df.index)]

        # Plot the bars
        for ii, (irow, row) in enumerate(df.iterrows()):
            if leg_name is not None:
                yi = yvals.index((row[y], leg_name))
            else:
                yi = yvals.index((row[y],))
            # offset = ((ranges['ymax'] - ranges['ymin']) - len(yvals)) / \
            #         (ranges['ymax'] - ranges['ymin'])
            bar([(row[x[0]], row[x[1]] - row[x[0]])],
                (yi - self.gantt.height/2, self.gantt.height),
                facecolor=fillcolor[ii],
                edgecolor=edgecolor[ii],
                linewidth=self.gantt.edge_width)

        # Adjust the yticklabels
        if iline + 1 == ngroups:
            tp = mpl_get_ticks(ax)
            new_yticks = tp['y']['ticks'].astype(str)
            yvals = [f[0] for f in yvals]
            ax.set_yticks(range(-1, len(yvals)))
            ax.set_yticklabels([''] + list(yvals))

        # Legend
        if leg_name is not None:
            handle = [patches.Rectangle((0, 0), 1, 1,
                      color=self.gantt.fill_color[(iline, leg_name)])]
            self.legend.add_value(leg_name, handle, 'lines')

        return df

    def plot_heatmap(self, ax, df, ir, ic, x, y, z, ranges):
        """
        Plot a heatmap

        Args:
            ax (mpl.axes): current axes obj
            df (pd.DataFrame):  data to plot
            x (str): x-column name
            y (str): y-column name
            z (str): z-column name
            range (dict):  ax limits

        """

        # Make the heatmap
        im = ax.imshow(df, self.cmap, vmin=ranges['zmin'],
                       vmax=ranges['zmax'],
                       interpolation=self.heatmap.interp)
        im.set_clim(ranges['zmin'], ranges['zmax'])

        # Adjust the axes and rc label size based on the number of groups
        cols = len(df.columns)
        rows = len(df)
        map_sq = min(self.axes.size[0] / cols, self.axes.size[1] / rows)
        self.axes.size = [map_sq * cols, map_sq * rows]
        if self.label_row.on:
            self.label_row.size[1] = self.axes.size[1]
        if self.label_col.on:
            self.label_col.size[0] = self.axes.size[0]

        # Set the axes
        dtypes = [int, np.int32, np.int64]
        if df.index.dtype not in dtypes:
            ax.set_yticks(np.arange(len(df)))
            ax.set_yticklabels(df.index)
            ax.set_yticks(np.arange(df.shape[0]+1)-.5, minor=True)
        if df.columns.dtype not in dtypes:
            ax.set_xticks(np.arange(len(df.columns)))
            ax.set_xticklabels(df.columns)
            ax.set_xticks(np.arange(df.shape[1]+1)-.5, minor=True)
        if df.index.dtype not in dtypes or df.columns.dtype not in dtypes:
            ax.grid(which="minor", color=self.heatmap.edge_color[0],
                    linestyle='-', linewidth=self.heatmap.edge_width)
            ax.tick_params(which="minor", bottom=False, left=False)
        if ranges['xmin'] is not None and ranges['xmin'] > 0:
            xticks = ax.get_xticks()
            ax.set_xticklabels([int(f + ranges['xmin']) for f in xticks])

        # Add the cbar
        if self.cbar.on:
            self.cbar.obj[ir, ic] = self.add_cbar(ax, im)

        # Loop over data dimensions and create text annotations
        if self.heatmap.text:
            for iy, yy in enumerate(df.index):
                for ix, xx in enumerate(df.columns):
                    if type(df.loc[yy, xx]) in [float, np.float32, np.float64] and \
                            np.isnan(df.loc[yy, xx]):
                        continue
                    text = ax.text(ix, iy, df.loc[yy, xx],
                                   ha="center", va="center",
                                   color=self.heatmap.font_color,
                                   fontsize=self.heatmap.font_size)

        return im

    def plot_hist(self, ir, ic, iline, df, x, y, leg_name, data, zorder=1,
                  line_type=None, marker_disable=False):

        if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
            hist = self.axes.obj[ir, ic].hist(df[x], bins=self.hist.bins,
                                              color=self.hist.fill_color[iline],
                                              ec=self.hist.edge_color[iline],
                                              lw=self.hist.edge_width,
                                              zorder=3, align=self.hist.align,
                                              cumulative=self.hist.cumulative,
                                              normed=self.hist.normalize,
                                              rwidth=self.hist.rwidth,
                                              stacked=self.hist.stacked,
                                              # type=self.hist.type,
                                              orientation='vertical' if not self.hist.horizontal else 'horizontal',
                                              )
        else:
            # if self.hist.horizontal:
            #     xx = y
            # else:
            #     xx = x
            hist = self.axes.obj[ir, ic].hist(df[x], bins=self.hist.bins,
                                              color=self.hist.fill_color[iline],
                                              ec=self.hist.edge_color[iline],
                                              lw=self.hist.edge_width,
                                              zorder=3, align=self.hist.align,
                                              cumulative=self.hist.cumulative,
                                              density=self.hist.normalize,
                                              rwidth=self.hist.rwidth,
                                              stacked=self.hist.stacked,
                                              # type=self.hist.type,
                                              orientation='vertical' if not self.hist.horizontal else 'horizontal',
                                              )

        # Add a reference to the line to self.lines
        if leg_name is not None:
            handle = [patches.Rectangle(
                (0, 0), 1, 1, color=self.hist.fill_color[iline])]
            self.legend.add_value(leg_name, handle, 'lines')

        # Add a kde
        if self.kde.on:
            kde = scipy.stats.gaussian_kde(df[x])
            if not self.hist.horizontal:
                x0 = np.linspace(data.ranges[ir, ic]['xmin'],
                                 data.ranges[ir, ic]['xmax'], 1000)
                y0 = kde(x0)
            else:
                y0 = np.linspace(data.ranges[ir, ic]['ymin'],
                                 data.ranges[ir, ic]['ymax'], 1000)
                x0 = kde(y0)
            kwargs = self.make_kwargs(self.kde)
            kwargs['color'] = RepeatedList(kwargs['color'][iline], 'color')
            kde = self.plot_line(ir, ic, x0, y0, **kwargs)

        return hist, data

    def plot_imshow(self, ir, ic, ax, df, x, y, z, ranges):
        """
        Plot a image

        Args:
            ax (mpl.axes): current axes obj
            df (pd.DataFrame):  data to plot
            x (str): x-column name
            y (str): y-column name
            z (str): z-column name
            range (dict):  ax limits

        """

        # Make the heatmap (maybe pull these kwargs out to an imshow obj?)
        im = ax.imshow(df.dropna(axis=1, how='all'), self.cmap,
                       vmin=ranges['zmin'], vmax=ranges['zmax'],
                       interpolation=self.imshow.interp)
        im.set_clim(ranges['zmin'], ranges['zmax'])

        # Add a cmap
        if self.cbar.on:  # and (self.separate_ticks or ic == self.ncol - 1):
            self.cbar.obj[ir, ic] = self.add_cbar(ax, im)

        return im

    def plot_line(self, ir, ic, x0, y0, x1=None, y1=None, **kwargs):
        """
        Plot a simple line

        Args:
            ir (int): subplot row index
            ic (int): subplot column index
            x0 (float): min x coordinate of line
            x1 (float): max x coordinate of line
            y0 (float): min y coordinate of line
            y1 (float): max y coordinate of line
            kwargs: keyword args
        """

        if x1 is not None:
            x0 = [x0, x1]
        if y1 is not None:
            y0 = [y0, y1]

        if 'color' not in kwargs.keys():
            kwargs['color'] = RepeatedList('#000000', 'temp')
        if 'style' not in kwargs.keys():
            kwargs['style'] = RepeatedList('-', 'temp')
        if 'width' not in kwargs.keys():
            kwargs['width'] = RepeatedList('-', 'temp')

        line = self.axes.obj[ir, ic].plot(x0, y0,
                                          linestyle=kwargs['style'][0],
                                          linewidth=kwargs['width'][0],
                                          color=kwargs['color'][0],
                                          zorder=kwargs.get('zorder', 1))
        return line

    def plot_pie(self, ir, ic, df, x, y, data, kwargs):
        """
        Plot a pie chart

        Args:
            ax (mpl.axes): current axes obj
            df (pd.DataFrame):  data to plot
            x (str): x-column name with label data
            y (str): y-column name with values
            kwargs (dict):  options

        """

        wedgeprops = {'linewidth': self.pie.edge_width,
                      'alpha': self.pie.alpha,
                      'linestyle': self.pie.edge_style,
                      'edgecolor': self.pie.edge_color[0],
                      'width': self.pie.inner_radius,
                      }
        textprops = {'fontsize': self.pie.font_size,
                     'weight': self.pie.font_weight,
                     'style': self.pie.font_style,
                     'color': self.pie.font_color,
                     }

        if self.pie.explode is not None:
            if self.pie.explode[0] == 'all':
                self.pie.explode = tuple([self.pie.explode[1] for f in y])
            elif len(self.pie.explode) < len(y):
                self.pie.explode = list(self.pie.explode)
                self.pie.explode += [0 for f in range(
                    0, len(y) - len(self.pie.explode))]

        if data.legend is not None:
            xx = [f for f in x]
            x = ['' for f in x]

        self.pie.obj = self.axes.obj[ir, ic].pie(
            y, labels=x, explode=self.pie.explode,  # center=[40,40],
            colors=self.pie.colors, autopct=self.pie.autopct,
            counterclock=self.pie.counterclock,
            labeldistance=self.pie.labeldistance,
            pctdistance=self.pie.pctdistance, radius=self.pie.radius,
            rotatelabels=self.pie.rotatelabels, shadow=self.pie.shadow,
            startangle=self.pie.startangle, wedgeprops=wedgeprops,
            textprops=textprops)

        # change percent font style
        if self.pie.autopct is not None:
            for lab in self.pie.obj[2]:
                lab.set_fontsize(self.pie.pct_font_size)
                lab.set_color(self.pie.pct_font_color)
                lab.set_fontweight(self.pie.pct_font_weight)

        self.axes.obj[ir, ic].set_xlim(left=-1)
        self.axes.obj[ir, ic].set_xlim(right=1)
        self.axes.obj[ir, ic].set_ylim(bottom=-1)
        self.axes.obj[ir, ic].set_ylim(top=1)

        if data.legend is not None:
            for i, val in enumerate(x):
                if xx[i] in self.legend.values['Key'].values:
                    continue
                handle = [patches.Rectangle(
                    (0, 0), 1, 1, color=self.pie.colors[i])]
                self.legend.add_value(xx[i], handle, 'lines')

        return self.pie.obj

    def plot_polygon(self, ir, ic, points, **kwargs):
        """
        Plot a polygon

        Args:
            ir (int): subplot row index
            ic (int): subplot column index
            points (list of float): points on the polygon
            kwargs: keyword args
        """

        if kwargs['fill_color'] is None:
            fill_color = 'none'
        else:
            fill_color = kwargs['fill_color'][0]

        polygon = [patches.Polygon(points, facecolor=fill_color,
                                   edgecolor=kwargs['edge_color'][0],
                                   linewidth=kwargs['edge_width'],
                                   linestyle=kwargs['edge_style'],
                                   alpha=kwargs['alpha'],
                                   )]
        p = PatchCollection(polygon, match_original=True,
                            zorder=kwargs['zorder'])

        self.axes.obj[ir, ic].add_collection(p)

    def plot_xy(self, ir, ic, iline, df, x, y, leg_name, twin, zorder=1,
                line_type=None, marker_disable=False):
        """ Plot xy data

        Args:
            x (np.array):  x data to plot
            y (np.array):  y data to plot
            color (str):  hex color code for line color (default='#000000')
            marker (str):  marker char string (default='o')
            points (bool):  toggle points on|off (default=False)
            line (bool):  toggle plot lines on|off (default=True)

        Keyword Args:
            any kwargs allowed by the plotter function selected

        Returns:
            return the line plot object
        """

        def format_marker(marker):
            """
            Format the marker string to mathtext
            """

            if marker in ['o', '+', 's', 'x', 'd', '^']:
                return marker
            elif marker is None:
                return 'None'
            else:
                return r'$%s$' % marker

        df = df.copy()

        if not line_type:
            line_type = self.lines
            line_type_name = 'lines'
        else:
            line_type_name = line_type
            line_type = getattr(self, line_type)

        # Select the axes
        if twin:
            ax = self.axes2.obj[ir, ic]
        else:
            ax = self.axes.obj[ir, ic]

        # Make the points
        if x is None:
            dfx = df[utl.df_int_cols(df)].values
        else:
            dfx = df[x]

        points = None
        if self.markers.on and not marker_disable:
            if self.markers.jitter:
                df[x] = np.random.normal(df[x], 0.03, size=len(df[y]))
            marker = format_marker(self.markers.type[iline])
            if marker != 'None':
                points = ax.plot(dfx, df[y],
                                 marker=marker,
                                 markerfacecolor=self.markers.fill_color[(
                                     iline, leg_name)]
                                 if self.markers.filled else 'none',
                                 markeredgecolor=self.markers.edge_color[(
                                     iline, leg_name)],
                                 markeredgewidth=self.markers.edge_width[(
                                     iline, leg_name)],
                                 linewidth=0,
                                 markersize=self.markers.size[iline],
                                 zorder=40)
            else:
                points = ax.plot(dfx, df[y],
                                 marker=marker,
                                 color=line_type.color[(iline, leg_name)],
                                 linestyle=line_type.style[iline],
                                 linewidth=line_type.width[iline],
                                 zorder=40)

        # Make the line
        lines = None
        if line_type.on:
            # Mask any nans
            try:
                mask = np.isfinite(dfx)
            except:
                mask = dfx == dfx

            # Plot the line
            lines = ax.plot(dfx[mask], df[y][mask],
                            color=line_type.color[(iline, leg_name)],
                            linestyle=line_type.style[iline],
                            linewidth=line_type.width[iline],
                            )

        # Add a reference to the line to self.lines
        if leg_name is not None:
            if leg_name is not None \
                    and leg_name not in list(self.legend.values['Key']):
                self.legend.add_value(
                    leg_name, points if points is not None else lines, line_type_name)

    def restore(self):
        """
        Undo changes to rcParams
        """

        for k, v in self.rc_orig.items():
            mpl.rcParams[k] = self.rc_orig[k]

    def save(self, filename, idx=0):
        """
        Save a plot window

        Args:
            filename (str): name of the file

        """

        kwargs = {'edgecolor': self.fig.edge_color[idx],
                  'facecolor': self.fig.fill_color[idx]}
        if LooseVersion(mpl.__version__) < LooseVersion('3.3'):
            kwargs['linewidth'] = self.fig.edge_width
        self.fig.obj.savefig(filename, **kwargs)

    def see(self):
        """
        Prints a readable list of class attributes
        """

        df = pd.DataFrame({'Attribute': list(self.__dict__.copy().keys()),
                           'Name': [str(f) for f in self.__dict__.copy().values()]})
        df = df.sort_values(by='Attribute').reset_index(drop=True)

        return df

    def set_axes_colors(self, ir, ic):
        """
        Set axes colors (fill, alpha, edge)

        Args:
            ir (int): subplot row index
            ic (int): subplot col index

        """

        axes = self.get_axes()

        # for ax in axes:
        try:
            axes[0].obj[ir, ic].set_facecolor(
                axes[0].fill_color[utl.plot_num(ir, ic, self.ncol)])
        except:
            axes[0].obj[ir, ic].set_axis_bgcolor(
                axes[0].fill_color[utl.plot_num(ir, ic, self.ncol)])

        for f in ['bottom', 'top', 'right', 'left']:
            if len(axes) > 1:
                axes[0].obj[ir, ic].spines[f].set_visible(False)
            if getattr(self.axes, 'spine_%s' % f):
                axes[-1].obj[ir, ic].spines[f].set_color(
                    axes[0].edge_color[utl.plot_num(ir, ic, self.ncol)])
            else:
                axes[-1].obj[ir,
                             ic].spines[f].set_color(self.fig.fill_color[0])
            if self.axes.edge_width != 1:
                axes[-1].obj[ir,
                             ic].spines[f].set_linewidth(self.axes.edge_width)

    def set_axes_grid_lines(self, ir, ic):
        """
        Style the grid lines and toggle visibility

        Args:
            ir (int): subplot row index
            ic (int): subplot col index

        """

        axes = self.get_axes()

        for ax in axes:
            # Turn off secondary gridlines
            if not ax.primary and \
                    not (hasattr(self, 'grid_major_x2') or
                         hasattr(self, 'grid_major_y2')):
                ax.obj[ir, ic].set_axisbelow(True)
                ax.obj[ir, ic].grid(False, which='major')
                ax.obj[ir, ic].grid(False, which='minor')
                continue

            # Set major grid
            ax.obj[ir, ic].set_axisbelow(True)
            if self.grid_major_x.on:
                ax.obj[ir, ic].xaxis.grid(b=True, which='major',
                                          # zorder=self.grid_major_x.zorder,
                                          color=self.grid_major_x.color[0],
                                          linestyle=self.grid_major_x.style[0],
                                          linewidth=self.grid_major_x.width[0])
            else:
                ax.obj[ir, ic].xaxis.grid(b=False, which='major')

            if hasattr(self, 'grid_major_x2') and not ax.primary:
                if self.grid_major_x.on:
                    ax.obj[ir, ic].xaxis.grid(b=True, which='major',
                                              # zorder=self.grid_major_x.zorder,
                                              color=self.grid_major_x2.color[0],
                                              linestyle=self.grid_major_x2.style[0],
                                              linewidth=self.grid_major_x2.width[0])
                else:
                    ax.obj[ir, ic].xaxis.grid(b=False, which='major')

            if self.grid_major_y.on:
                ax.obj[ir, ic].yaxis.grid(b=True, which='major',
                                          # zorder=self.grid_major_y.zorder,
                                          color=self.grid_major_y.color[0],
                                          linestyle=self.grid_major_y.style[0],
                                          linewidth=self.grid_major_y.width[0])
            else:
                ax.obj[ir, ic].yaxis.grid(b=False, which='major')

            if hasattr(self, 'grid_major_y2') and not ax.primary:
                if self.grid_major_y2.on:
                    ax.obj[ir, ic].yaxis.grid(b=True, which='major',
                                              # zorder=self.grid_major_y.zorder,
                                              color=self.grid_major_y2.color[0],
                                              linestyle=self.grid_major_y2.style[0],
                                              linewidth=self.grid_major_y2.width[0])
                else:
                    ax.obj[ir, ic].yaxis.grid(b=False, which='major')

            # Set minor grid
            if self.grid_minor_x.on:
                ax.obj[ir, ic].xaxis.grid(b=True, which='minor',
                                          # zorder=self.grid_minor_x.zorder,
                                          color=self.grid_minor_x.color[0],
                                          linestyle=self.grid_minor_x.style[0],
                                          linewidth=self.grid_minor_x.width[0])
            if self.grid_minor_y.on:
                ax.obj[ir, ic].yaxis.grid(b=True, which='minor',
                                          # zorder=self.grid_minor_y.zorder,
                                          color=self.grid_minor_y.color[0],
                                          linestyle=self.grid_minor_y.style[0],
                                          linewidth=self.grid_minor_y.width[0])

    def set_axes_labels(self, ir, ic):
        """
        Set the axes labels

        Args:
            ir (int): current row index
            ic (int): current column index
            kw (dict): kwargs dict

        """

        if self.name in ['pie']:
            return

        self.get_axes_label_position()

        axis = ['x', 'x2', 'y', 'y2', 'z']
        for ax in axis:
            label = getattr(self, 'label_%s' % ax)
            if not label.on:
                continue
            if type(label.text) not in [str, list]:
                continue
            if type(label.text) is str:
                labeltext = label.text
            if type(label.text) is list:
                labeltext = label.text[ic + ir * self.ncol]

            if '2' in ax:
                axes = self.axes2.obj[ir, ic]
                pad = self.ws_label_tick
            else:
                axes = self.axes.obj[ir, ic]
                pad = self.ws_label_tick

            # Toggle label visibility
            if not self.separate_labels:
                if ax == 'x' and ir != self.nrow - 1 and \
                        self.nwrap == 0 and self.axes.visible[ir+1, ic]:
                    continue
                if ax == 'x2' and ir != 0:
                    continue
                if ax == 'y' and ic != 0 and self.axes.visible[ir, ic - 1]:
                    continue
                if ax == 'y2' and ic != self.ncol - 1 and \
                        utl.plot_num(ir, ic, self.ncol) != self.nwrap:
                    continue
                if ax == 'z' and ic != self.ncol - 1 and \
                        utl.plot_num(ir, ic, self.ncol) != self.nwrap:
                    continue

            # Add the label
            label.obj[ir, ic], label.obj_bg[ir, ic] = \
                self.add_label(ir, ic, labeltext, **self.make_kwargs(label))

    def set_axes_scale(self, ir, ic):
        """
        Set the scale type of the axes

        Args:
            ir (int): subplot row index
            ic (int): subplot col index

        Returns:
            axes scale type
        """

        axes = self.get_axes()

        for ax in axes:
            if ax.scale is None:
                continue
            else:
                if str(ax.scale).lower() in LOGX:
                    ax.obj[ir, ic].set_xscale('log')
                elif str(ax.scale).lower() in SYMLOGX:
                    ax.obj[ir, ic].set_xscale('symlog')
                elif str(ax.scale).lower() in LOGITX:
                    ax.obj[ir, ic].set_xscale('logit')
                if str(ax.scale).lower() in LOGY:
                    ax.obj[ir, ic].set_yscale('log')
                elif str(ax.scale).lower() in SYMLOGY:
                    ax.obj[ir, ic].set_yscale('symlog')
                elif str(ax.scale).lower() in LOGITY:
                    ax.obj[ir, ic].set_yscale('logit')

    def set_axes_ranges(self, ir, ic, ranges):
        """
        Set the axes ranges

        Args:
            ir (int): subplot row index
            ic (int): subplot col index
            limits (dict): min/max axes limits for each axis

        """

        if self.name in ['heatmap', 'pie']:
            return

        # X-axis
        if self.axes.share_x:
            xvals = ['xmin', 'xmax', 'x2min', 'x2max']
            for xval in xvals:
                xx = None
                for irow in range(0, self.nrow):
                    for icol in range(0, self.ncol):
                        if ranges[irow, icol][xval] is not None:
                            if irow == 0 and icol == 0:
                                xx = ranges[irow, icol][xval]
                            elif 'min' in xval:
                                xx = min(xx, ranges[irow, icol][xval])
                            else:
                                xx = max(xx, ranges[irow, icol][xval])

                if xx is not None and xval == 'xmin':
                    self.axes.obj[ir, ic].set_xlim(left=xx)
                elif xx is not None and xval == 'x2min':
                    self.axes2.obj[ir, ic].set_xlim(left=xx)
                elif xx is not None and xval == 'xmax':
                    self.axes.obj[ir, ic].set_xlim(right=xx)
                elif xx is not None and xval == 'x2max':
                    self.axes2.obj[ir, ic].set_xlim(right=xx)
        else:
            if ranges[ir, ic]['xmin'] is not None:
                self.axes.obj[ir, ic].set_xlim(left=ranges[ir, ic]['xmin'])
            if ranges[ir, ic]['x2min'] is not None:
                self.axes2.obj[ir, ic].set_xlim(left=ranges[ir, ic]['x2min'])
            if ranges[ir, ic]['xmax'] is not None:
                self.axes.obj[ir, ic].set_xlim(right=ranges[ir, ic]['xmax'])
            if ranges[ir, ic]['x2max'] is not None:
                self.axes2.obj[ir, ic].set_xlim(right=ranges[ir, ic]['x2max'])

        # Y-axis
        if self.axes.share_y:
            yvals = ['ymin', 'ymax', 'y2min', 'y2max']
            for yval in yvals:
                yy = None
                for irow in range(0, self.nrow):
                    for icol in range(0, self.ncol):
                        if ranges[irow, icol][yval] is not None:
                            if irow == 0 and icol == 0:
                                yy = ranges[irow, icol][yval]
                            elif 'min' in yval:
                                yy = min(yy, ranges[irow, icol][yval])
                            else:
                                yy = max(yy, ranges[irow, icol][yval])

                if yy is not None and yval == 'ymin':
                    self.axes.obj[ir, ic].set_ylim(bottom=yy)
                elif yy is not None and yval == 'y2min':
                    self.axes2.obj[ir, ic].set_ylim(bottom=yy)
                elif yy is not None and yval == 'ymax':
                    self.axes.obj[ir, ic].set_ylim(top=yy)
                elif yy is not None and yval == 'y2max':
                    self.axes2.obj[ir, ic].set_ylim(top=yy)
        else:
            if ranges[ir, ic]['ymin'] is not None:
                self.axes.obj[ir, ic].set_ylim(bottom=ranges[ir, ic]['ymin'])
            if ranges[ir, ic]['y2min'] is not None:
                self.axes2.obj[ir, ic].set_ylim(bottom=ranges[ir, ic]['y2min'])
            if ranges[ir, ic]['ymax'] is not None:
                self.axes.obj[ir, ic].set_ylim(top=ranges[ir, ic]['ymax'])
            if ranges[ir, ic]['y2max'] is not None:
                self.axes2.obj[ir, ic].set_ylim(top=ranges[ir, ic]['y2max'])

    def set_axes_ranges_hist(self, ir, ic, data, hist, iline):
        """
        Special range overrides for histogram plot
            Needed to deal with the late computation of bin counts

        Args:
            ir (int): subplot row index
            ic (int): subplot col index
            data (Data obj): current data object
            hist (mpl.hist obj): result of hist plot

        """

        if not self.hist.horizontal:
            if data.ymin:
                data.ranges[ir, ic]['ymin'] = data.ymin
            else:
                data.ranges[ir, ic]['ymin'] = None
            if data.ymax:
                data.ranges[ir, ic]['ymax'] = data.ymax
            elif data.ranges[ir, ic]['ymax'] is None:
                data.ranges[ir, ic]['ymax'] = \
                    max(hist[0]) * (1 + data.ax_limit_padding_y_max)
            else:
                data.ranges[ir, ic]['ymax'] = \
                    max(data.ranges[ir, ic]['ymax'], max(hist[0]) *
                        (1 + data.ax_limit_padding_y_max))
        elif self.hist.horizontal:
            if data.ymin:
                data.ranges[ir, ic]['ymin'] = data.ymin
            elif iline == 0:
                data.ranges[ir, ic]['ymin'] = data.ranges[ir, ic]['xmin']
            if data.ymax:
                data.ranges[ir, ic]['ymax'] = data.ymax
            elif iline == 0:
                data.ranges[ir, ic]['ymax'] = data.ranges[ir, ic]['xmax']
            if data.xmin:
                data.ranges[ir, ic]['xmin'] = data.xmin
            else:
                data.ranges[ir, ic]['xmin'] = None
            if data.xmax:
                data.ranges[ir, ic]['xmax'] = data.xmax
            elif iline == 0:
                data.ranges[ir, ic]['xmax'] = \
                    max(hist[0]) * (1 + data.ax_limit_padding_y_max)
            else:
                data.ranges[ir, ic]['xmax'] = \
                    max(data.ranges[ir, ic]['xmax'], max(hist[0]) *
                        (1 + data.ax_limit_padding_x_max))

        return data

    def set_axes_rc_labels(self, ir, ic):
        """
        Add the row/column label boxes and wrap titles

        Args:
            ir (int): current row index
            ic (int): current column index

        """

        wrap, row, col = None, None, None

        # Wrap title  --> this guy's text size is not defined in get_elements_size
        if ir == 0 and ic == 0 and self.title_wrap.on:
            kwargs = self.make_kwargs(self.title_wrap)
            if self.axes.edge_width == 0:
                kwargs['size'][0] -= 1
            if self.name == 'imshow' and not self.cbar.on and self.nrow == 1:
                kwargs['size'][0] -= 1  # don't understand this one
            if self.cbar.on:
                kwargs['size'][0] -= (self.ws_ax_cbar + self.cbar.size[0])
            self.title_wrap.obj, self.title_wrap.obj_bg = \
                self.add_label(ir, ic, self.title_wrap.text, **kwargs)

        # Row labels
        if ic == self.ncol-1 and self.label_row.on and not self.label_wrap.on:
            if self.label_row.text_size is not None:
                text_size = self.label_row.text_size[ir, ic]
            else:
                text_size = None
            self.label_row.obj[ir, ic], self.label_row.obj_bg[ir, ic] = \
                self.add_label(ir, ic, '%s=%s' %
                               (self.label_row.text,
                                self.label_row.values[ir]),
                               offset=True, **self.make_kwargs(self.label_row))

        # Col/wrap labels
        if (ir == 0 and self.label_col.on) or self.label_wrap.on:
            if self.label_row.text_size is not None:
                text_size = self.label_col.text_size[ir, ic]
            else:
                text_size = None
            if self.label_wrap.on:
                kwargs = self.make_kwargs(self.label_wrap)
                if self.axes.edge_width == 0:  # and ic == self.ncol - 1:
                    kwargs['size'][0] -= 1
                if self.name == 'imshow' and not self.cbar.on and self.nrow == 1:
                    kwargs['size'][0] -= 1
                text = ' | '.join([str(f) for f in utl.validate_list(
                    self.label_wrap.values[ir*self.ncol + ic])])
                self.label_wrap.obj[ir, ic], self.label_wrap.obj_bg[ir, ic] = \
                    self.add_label(ir, ic, text, **kwargs)
            else:
                text = '%s=%s' % (self.label_col.text,
                                  self.label_col.values[ic])
                self.label_col.obj[ir, ic], self.label_col.obj_bg[ir, ic] = \
                    self.add_label(ir, ic, text, **
                                   self.make_kwargs(self.label_col))

    def set_axes_ticks(self, ir, ic):
        """
        Configure the axes tick marks

        Args:
            ax (mpl axes): current axes to scale
            kw (dict): kwargs dict
            y_only (bool): flag to access on the y-axis ticks

        """

        def get_tick_position(ax, tp, xy, loc='first', idx=0):
            """
            Find the position of a tick given the actual range

            Args:
                ax (mpl.axes): the axis of interest
                tp (dict): tick location dictionary
                xy (str): which axis to calculate ('x' or 'y')
                loc (str): tick location ('first' or 'last')

            Returns:
                the actual x-position of an xtick or the y-position of a ytick

            """

            if idx == 0:
                lab = ''
            else:
                lab = '2'

            size = 0 if xy == 'x' else 1
            if type(loc) is str:
                tick = tp[xy]['label_vals'][tp[xy][loc]]
            else:
                tick = tp[xy]['label_vals'][loc]
            lim = sorted(getattr(ax, 'get_%slim' % xy)())
            if tick > lim[1]:
                pos = self.axes.size[size]
            elif tick < lim[0]:
                pos = -999  # push it far away from axis
            elif getattr(self, 'axes%s' % lab).scale in (LOGX if xy == 'x' else LOGY):
                pos = (np.log10(tick) - np.log10(lim[0])) / \
                      (np.log10(lim[1]) - np.log10(lim[0])) * \
                    self.axes.size[size]
            else:
                pos = (tick - lim[0]) / (lim[1] - lim[0]) * \
                    self.axes.size[size]

            return pos

        if self.name in ['pie']:
            return

        axes = [f.obj[ir, ic] for f in [self.axes, self.axes2] if f.on]

        # Format ticks
        for ia, aa in enumerate(axes):

            minor_on = max(self.ticks_minor_x.on, self.ticks_minor_y.on)
            tp = mpl_get_ticks(axes[ia], True, True, minor_on)

            if ia == 0:
                lab = ''
            else:
                lab = '2'

            # Skip certain calculations if axes are shared and subplots > 1
            skipx, skipy = False, False
            if hasattr(getattr(self, 'axes%s' % lab), 'share_x%s' % lab) and \
                    getattr(getattr(self, 'axes%s' % lab), 'share_x%s' % lab) == True and \
                    (ir != 0 or ic != 0):
                skipx = False
            if hasattr(getattr(self, 'axes%s' % lab), 'share_y%s' % lab) and \
                    getattr(getattr(self, 'axes%s' % lab), 'share_y%s' % lab) and \
                    (ir != 0 or ic != 0):
                skipy = False

            # Turn off scientific
            if ia == 0:
                if not skipx:
                    self.set_scientific(axes[ia], tp)
            elif self.axes.twin_y or self.axes.twin_x:
                if not skipy:
                    self.set_scientific(axes[ia], tp, 2)

            # Turn off offsets
            if not self.tick_labels_major.offset:
                try:
                    if not skipx:
                        aa.get_xaxis().get_major_formatter().set_useOffset(False)
                except:
                    pass
                try:
                    if not skipy:
                        aa.get_yaxis().get_major_formatter().set_useOffset(False)
                except:
                    pass

            # General tick params
            if ia == 0:
                if self.ticks_minor_x.on or self.ticks_minor_y.on:
                    axes[0].minorticks_on()
                axes[0].tick_params(axis='both',
                                    which='major',
                                    pad=self.ws_ticks_ax,
                                    colors=self.ticks_major.color[0],
                                    labelcolor=self.tick_labels_major.font_color,
                                    labelsize=self.tick_labels_major.font_size,
                                    top=False,
                                    bottom=self.ticks_major_x.on,
                                    right=False if self.axes.twin_x
                                    else self.ticks_major_y.on,
                                    left=self.ticks_major_y.on,
                                    length=self.ticks_major._size[0],
                                    width=self.ticks_major._size[1],
                                    direction=self.ticks_major.direction,
                                    zorder=100,
                                    )
                axes[0].tick_params(axis='both',
                                    which='minor',
                                    pad=self.ws_ticks_ax,
                                    colors=self.ticks_minor.color[0],
                                    labelcolor=self.tick_labels_minor.font_color,
                                    labelsize=self.tick_labels_minor.font_size,
                                    top=False,
                                    bottom=self.ticks_minor_x.on,
                                    right=False if self.axes.twin_x
                                    else self.ticks_minor_y.on,
                                    left=self.ticks_minor_y.on,
                                    length=self.ticks_minor._size[0],
                                    width=self.ticks_minor._size[1],
                                    direction=self.ticks_minor.direction,
                                    )
                if self.axes.twin_x:
                    if self.ticks_minor_y2.on:
                        axes[1].minorticks_on()
                    axes[1].tick_params(which='major',
                                        pad=self.ws_ticks_ax,
                                        colors=self.ticks_major.color[0],
                                        labelcolor=self.tick_labels_major.font_color,
                                        labelsize=self.tick_labels_major.font_size,
                                        right=self.ticks_major_y2.on,
                                        length=self.ticks_major.size[0],
                                        width=self.ticks_major.size[1],
                                        direction=self.ticks_major.direction,
                                        zorder=0,
                                        )
                    axes[1].tick_params(which='minor',
                                        pad=self.ws_ticks_ax,
                                        colors=self.ticks_minor.color[0],
                                        labelcolor=self.tick_labels_minor.font_color,
                                        labelsize=self.tick_labels_minor.font_size,
                                        right=self.ticks_minor_y2.on,
                                        length=self.ticks_minor._size[0],
                                        width=self.ticks_minor._size[1],
                                        direction=self.ticks_minor.direction,
                                        zorder=0,
                                        )
                elif self.axes.twin_y:
                    if self.ticks_minor_x2.on:
                        axes[1].minorticks_on()
                    axes[1].tick_params(which='major',
                                        pad=self.ws_ticks_ax,
                                        colors=self.ticks_major.color[0],
                                        labelcolor=self.tick_labels_major.font_color,
                                        labelsize=self.tick_labels_major.font_size,
                                        top=self.ticks_major_x2.on,
                                        length=self.ticks_major.size[0],
                                        width=self.ticks_major.size[1],
                                        direction=self.ticks_major.direction,
                                        )
                    axes[1].tick_params(which='minor',
                                        pad=self.ws_ticks_ax*2,
                                        colors=self.ticks_minor.color[0],
                                        labelcolor=self.tick_labels_minor.font_color,
                                        labelsize=self.tick_labels_minor.font_size,
                                        top=self.ticks_minor_x2.on,
                                        length=self.ticks_minor._size[0],
                                        width=self.ticks_minor._size[1],
                                        direction=self.ticks_minor.direction,
                                        )

            # Set custom tick increment
            redo = True
            xinc = getattr(self, 'ticks_major_x%s' % lab).increment
            if not skipx and xinc is not None and self.name not in ['bar']:
                xstart = 0 if tp['x']['min'] == 0 else tp['x']['min'] + \
                    xinc - tp['x']['min'] % xinc
                axes[ia].set_xticks(np.arange(xstart, tp['x']['max'], xinc))
                redo = True
            yinc = getattr(self, 'ticks_major_y%s' % lab).increment
            if not skipy and yinc is not None:
                axes[ia].set_yticks(
                    np.arange(tp['y']['min'] + yinc - tp['y']['min'] % yinc,
                              tp['y']['max'], yinc))
                redo = True

            if redo:
                tp = mpl_get_ticks(axes[ia], True, True, minor_on)

            # Force ticks
            if self.separate_ticks or getattr(self, 'axes%s' % lab).share_x == False:
                if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
                    mplp.setp(axes[ia].get_xticklabels(), visible=True)
                else:
                    if self.axes.twin_x and ia == 1:
                        axes[ia].xaxis.set_tick_params(
                            which='both', labelbottom=True)
                    elif self.axes.twin_y and ia == 1:
                        axes[ia].xaxis.set_tick_params(
                            which='both', labeltop=True)
                    else:
                        axes[ia].xaxis.set_tick_params(
                            which='both', labelbottom=True)

            if self.separate_ticks or getattr(self, 'axes%s' % lab).share_y == False:
                if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
                    mplp.setp(axes[ia].get_yticklabels(), visible=True)
                else:
                    if self.axes.twin_x and ia == 1:
                        axes[ia].yaxis.set_tick_params(
                            which='both', labelright=True)
                    elif self.axes.twin_y and ia == 1:
                        axes[ia].yaxis.set_tick_params(
                            which='both', labelleft=True)
                    else:
                        axes[ia].yaxis.set_tick_params(
                            which='both', labelleft=True)

            if self.nwrap > 0 and (ic + (ir + 1) * self.ncol + 1) > self.nwrap or \
                    (ir < self.nrow - 1 and not self.axes.visible[ir + 1, ic]):
                if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
                    mplp.setp(axes[ia].get_xticklabels()[1:], visible=True)
                elif self.axes.twin_y and ia == 1:
                    axes[ia].yaxis.set_tick_params(which='both', labeltop=True)
                else:
                    axes[ia].xaxis.set_tick_params(
                        which='both', labelbottom=True)
            if not self.separate_ticks and not self.axes.visible[ir, ic - 1]:
                if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
                    mplp.setp(axes[ia].get_yticklabels(), visible=True)
                elif self.axes.twin_x and ia == 1:
                    axes[ia].yaxis.set_tick_params(
                        which='both', labelright=True)
                else:
                    axes[ia].yaxis.set_tick_params(
                        which='both', labelleft=True)
            elif not self.separate_ticks and (ic != self.ncol - 1 and
                                              utl.plot_num(ir, ic, self.ncol) != self.nwrap) and \
                    self.axes.twin_x and ia == 1:
                mplp.setp(axes[ia].get_yticklabels(), visible=False)
            if not self.separate_ticks and ir != 0 and self.axes.twin_y and ia == 1:
                mplp.setp(axes[ia].get_xticklabels(), visible=False)

            # Major rotation
            if getattr(self, 'tick_labels_major_x%s' % lab).on:
                ticks_font = \
                    font_manager.FontProperties(family=getattr(self, 'tick_labels_major_x%s' % lab).font,
                                                size=getattr(
                                                    self, 'tick_labels_major_x%s' % lab).font_size,
                                                style=getattr(
                                                    self, 'tick_labels_major_x%s' % lab).font_style,
                                                weight=getattr(self, 'tick_labels_major_x%s' % lab).font_weight)
                for text in axes[ia].get_xticklabels():
                    if getattr(self, 'tick_labels_major_x%s' % lab).rotation != 0:
                        text.set_rotation(
                            getattr(self, 'tick_labels_major_x%s' % lab).rotation)
                    text.set_fontproperties(ticks_font)
                    text.set_bbox(dict(edgecolor=getattr(self, 'tick_labels_major_x%s' % lab).edge_color[0],
                                       facecolor=getattr(
                                           self, 'tick_labels_major_x%s' % lab).fill_color[0],
                                       linewidth=getattr(self, 'tick_labels_major_x%s' % lab).edge_width))
            if getattr(self, 'tick_labels_major_y%s' % lab).on:
                ticks_font = \
                    font_manager.FontProperties(family=getattr(self, 'tick_labels_major_y%s' % lab).font,
                                                size=getattr(
                                                    self, 'tick_labels_major_y%s' % lab).font_size,
                                                style=getattr(
                                                    self, 'tick_labels_major_y%s' % lab).font_style,
                                                weight=getattr(self, 'tick_labels_major_y%s' % lab).font_weight)
                for text in axes[ia].get_yticklabels():
                    if getattr(self, 'tick_labels_major_y%s' % lab).rotation != 0:
                        text.set_rotation(
                            getattr(self, 'tick_labels_major_y%s' % lab).rotation)
                    text.set_fontproperties(ticks_font)
                    text.set_bbox(dict(edgecolor=getattr(self, 'tick_labels_major_y%s' % lab).edge_color[0],
                                       facecolor=getattr(
                                           self, 'tick_labels_major_y%s' % lab).fill_color[0],
                                       linewidth=getattr(self, 'tick_labels_major_y%s' % lab).edge_width))

            # Tick label shorthand
            tlmajx = getattr(self, 'tick_labels_major_x%s' % lab)
            tlmajy = getattr(self, 'tick_labels_major_y%s' % lab)

            # Turn off major tick labels
            if not tlmajx.on:
                ll = ['' for f in axes[ia].get_xticklabels()]
                axes[ia].set_xticklabels(ll)

            if not tlmajy.on:
                ll = ['' for f in axes[ia].get_yticklabels()]
                axes[ia].set_yticklabels(ll)

            # Turn on minor tick labels
            ax = ['x', 'y']
            sides = {}
            if LooseVersion(mpl.__version__) < LooseVersion('2.2'):
                sides['x'] = {'labelbottom': 'off'}
                sides['x2'] = {'labeltop': 'off'}
                sides['y'] = {'labelleft': 'off'}
                sides['y2'] = {'labelright': 'off'}
            else:
                sides['x'] = {'labelbottom': False}
                sides['x2'] = {'labeltop': False}
                sides['y'] = {'labelleft': False}
                sides['y2'] = {'labelright': False}

            tlminon = False  # "tick label min"
            for axx in ax:
                axl = '%s%s' % (axx, lab)
                tlmin = getattr(self, 'ticks_minor_%s' % axl)

                if ia == 1 and axx == 'x' and self.axes.twin_x:
                    continue

                if ia == 1 and axx == 'y' and self.axes.twin_y:
                    continue

                if getattr(self, 'ticks_minor_%s' % axl).number is not None:
                    num_minor = getattr(self, 'ticks_minor_%s' % axl).number
                    if getattr(self, 'axes%s' % lab).scale not in (LOG_ALLX if axx == 'x' else LOG_ALLY):
                        loc = None
                        loc = AutoMinorLocator(num_minor+1)
                        getattr(axes[ia], '%saxis' %
                                axx).set_minor_locator(loc)

                if not self.separate_ticks and axl == 'x' and ir != self.nrow - 1 and self.nwrap == 0 or \
                        not self.separate_ticks and axl == 'y2' and ic != self.ncol - 1 and self.nwrap == 0 or \
                        not self.separate_ticks and axl == 'x2' and ir != 0 or \
                        not self.separate_ticks and axl == 'y' and ic != 0 or \
                        not self.separate_ticks and axl == 'y2' and ic != self.ncol - 1 and utl.plot_num(ir, ic, self.ncol) != self.nwrap:
                    axes[ia].tick_params(which='minor', **sides[axl])

                elif tlmin.on:
                    if not getattr(self, 'tick_labels_minor_%s' % axl).on:
                        continue
                    elif 'x' in axx and skipx:
                        continue
                    elif 'y' in axx and skipy:
                        continue
                    else:
                        tlminon = True

                    # Determine the minimum number of decimals needed to display the minor ticks
                    # think we already have this so don't need to call again
                    # tp = mpl_get_ticks(axes[ia],
                    #                    getattr(self, 'ticks_major_x%s' %
                    #                            lab).on,
                    #                    getattr(self, 'ticks_major_y%s' % lab).on)
                    m0 = len(tp[axx]['ticks'])
                    lim = getattr(axes[ia], 'get_%slim' % axx)()
                    vals = [f for f in tp[axx]['ticks'] if f > lim[0]]
                    label_vals = [f for f in tp[axx]
                                  ['label_vals'] if f > lim[0]]
                    inc = label_vals[1] - label_vals[0]
                    minor_ticks = [f[1] for f in tp[axx]['labels']][m0:]

                    # Remove any major tick labels from the list of minor ticks
                    dups = []
                    dups_idx = []
                    for imt, mt in enumerate(minor_ticks):
                        for majt in tp[axx]['ticks']:
                            if math.isclose(mt, majt):
                                dups += [mt]
                                dups_idx += [m0 + imt]
                    minor_ticks2 = [f for f in minor_ticks if f not in dups]
                    number = len([f for f in minor_ticks2 if f >
                                 vals[0] and f < vals[1]]) + 1
                    decimals = utl.get_decimals(inc/number)

                    # Check for minor ticks below the first major tick for log axes
                    if getattr(self, 'axes%s' % lab).scale in (LOGX if axx == 'x' else LOGY):
                        extra_minor = [f for f in minor_ticks
                                       if f < label_vals[0] and f > lim[0]]
                        if len(extra_minor) > 0:
                            decimals += 1

                    # Set the tick decimal format
                    getattr(axes[ia], '%saxis' % axx).set_minor_formatter(
                        ticker.FormatStrFormatter('%%.%sf' % (decimals)))

                    # Text formatting
                    tlminlab = getattr(self, 'tick_labels_minor_%s' % axl)
                    ticks_font_minor = \
                        font_manager.FontProperties(family=tlminlab.font,
                                                    size=tlminlab.font_size,
                                                    style=tlminlab.font_style,
                                                    weight=tlminlab.font_weight)
                    for text in getattr(axes[ia], 'get_%sminorticklabels' % axx)():
                        if tlminlab.rotation != 0:
                            text.set_rotation(
                                getattr(self, 'tick_labels_major_%s' % axx).rotation)
                        text.set_fontproperties(ticks_font_minor)
                        text.set_bbox(dict(edgecolor=tlminlab.edge_color[0],
                                           facecolor=tlminlab.fill_color[0],
                                           linewidth=tlminlab.edge_width))

                    if tlminlab.rotation != 0:
                        for text in getattr(axes[ia], 'get_%sminorticklabels' % axx)():
                            text.set_rotation(tlminlab.rotation)

                    # # Minor tick overlap cleanup
                    # if self.tick_cleanup and tlminon:
                    #     tp = mpl_get_ticks(axes[ia],
                    #                        getattr(self, 'ticks_major_x%s' % lab).on,
                    #                        getattr(self, 'ticks_major_y%s' % lab).on)  # need to update
                    #     buf = 1.99
                    #     if axx == 'x':
                    #         wh = 0
                    #     else:
                    #         wh = 1

                    #     # Check overlap with major tick labels
                    #     majw = getattr(self, 'tick_labels_major_%s' % axl).size[wh]/2
                    #     delmaj = self.axes.size[wh]
                    #     lim = getattr(axes[ia], 'get_%slim' % axx)()
                    #     ticks = [f for f in tp[axx]['ticks'] if f >= lim[0] and f <= lim[1]]
                    #     if len(ticks) > 0:
                    #         if axx == 'x':
                    #             if xfx != xcx:
                    #                 delmaj = (xfx-xcx)/(len(valid_x)-1)
                    #             else:
                    #                 delmaj = xfx
                    #         else:
                    #             if yfy != ycy:
                    #                 delmaj = (yfy-ycy)/(len(valid_y)-1)
                    #             else:
                    #                 delmaj = yfy

                    #         labels = tp[axx]['label_text'][len(tp[axx]['ticks']):]
                    #         delmin = delmaj/number
                    #         wipe = []

                    #         for i in range(0, number - 1):
                    #             if getattr(self, 'axes%s' % lab).scale in \
                    #                     (LOGX if axx == 'x' else LOGY):
                    #                 pos = np.log10(i + 2) * delmaj
                    #             else:
                    #                 pos = delmaj / number * (i + 1)
                    #             if majw > pos - tlminlab.size[wh]/2 - buf or \
                    #                     delmaj - majw < pos + tlminlab.size[wh]/2 + buf:
                    #                 wipe += [i]
                    #         offset = len([f for f in minor_ticks if f < ticks[0]])

                    #         # There is a weird bug where a tick can be both major and minor; need to remove
                    #         # dups = [i+m0 for i, f in enumerate(minor_ticks)
                    #         #         if f in tp[axx]['ticks']]
                    #         if len(dups_idx) == 0:
                    #             dups_idx = [-1, len(tp[axx]['label_text'])]
                    #         if dups_idx[0] != -1:
                    #             dups_idx = [-1] + dups_idx
                    #         if dups_idx[len(dups_idx)-1] != len(dups_idx):
                    #             dups_idx = dups_idx + [len(tp[axx]['label_text'])]
                    #         temp = []
                    #         for j in range(1, len(dups_idx)):
                    #             temp += tp[axx]['label_text'][dups_idx[j-1]+1:dups_idx[j]]

                    #         # Disable ticks above first major tick
                    #         for i, text in enumerate(tp[axx]['label_text']):
                    #             # above first major tick
                    #             if i in wipe:
                    #                 vals = temp[m0+i+offset::number-1]
                    #                 temp[m0+i+offset::number-1] = ['']*len(vals)
                    #         # Disable ticks below first major tick
                    #         rwipe = [number - 1 - f for f in wipe]
                    #         rticks = list(reversed(temp[m0:m0+offset]))
                    #         for i, tick in enumerate(rticks):
                    #             if i + 1 in rwipe:
                    #                 rticks[i] = ''
                    #         temp[m0:m0+offset] = list(reversed(rticks))

                    #         # Put back in duplicates
                    #         for jj in dups_idx[1:]:
                    #             temp.insert(jj, '')
                    #         tp[axx]['label_text'] = temp

                    #     # Check for overlap of first minor with opposite major axis (need to account for twin_x?)
                    #     if len(tp['x']['ticks']) > 0:
                    #         minor = tp['x']['label_vals'][m0:]
                    #         lim = getattr(axes[ia], 'get_%slim' % axx)()
                    #         first = [i for i, f in enumerate(minor) if f > lim[0]][0]
                    #         xwmin, xhmin = tlmajx.size
                    #         ywmin, yhmin = tlmajy.size
                    #         xcxmin = get_tick_position(axes[ia], tp, axx, first+m0, ia)
                    #         xcmin = [xcxmin, -tlmin.size[1]/2-self.ws_ticks_ax + ia*self.axes.size[1]]
                    #         x0miny0 = utl.rectangle_overlap([xwmin+2*buf, xhmin+2*buf, xcmin],
                    #                                         [yw+2*buf, yh+2*buf, yc])
                    #         if x0miny0:
                    #             tp[axx]['label_text'][m0+first] = ''

                    #     # Check minor to minor overlap
                    #     if axx == 'x' and self.axes.scale in LOGX or \
                    #             axx == 'y' and self.axes.scale in LOGY:
                    #         for itick, t0 in enumerate(tp[axx]['label_text'][m0+1:-1]):
                    #             if t0 == '':
                    #                 continue
                    #             t0 = float(t0)
                    #             if t0 == 0:
                    #                 continue
                    #             t0 = np.log10(t0) % 1
                    #             t1 = tp[axx]['label_text'][m0+itick+2]
                    #             if t1 == '':
                    #                 continue
                    #             t1 = np.log10(float(t1)) % 1
                    #             delmin = (t1-t0) * delmaj
                    #             if tlminlab.size[wh] + buf > delmin:
                    #                 if tp[axx]['label_text'][m0+itick+1] != '':
                    #                     tp[axx]['label_text'][m0+itick+2] = ''

                    #     elif tlminlab.size[wh] + buf > delmin:
                    #         for itick, tick in enumerate(tp[axx]['label_text'][m0+1:]):
                    #             if tp[axx]['label_text'][m0+itick] != '':
                    #                 tp[axx]['label_text'][m0+itick+1] = ''

                    #     # Set the labels
                    #     for itick, tick in enumerate(tp[axx]['label_text'][m0:]):
                    #         if tick == '':
                    #             continue
                    #         tp[axx]['label_text'][m0 + itick] = \
                    #             str(decimal.Decimal(tick).normalize())
                    #     getattr(axes[ia], 'set_%sticklabels' % axx) \
                    #         (tp[axx]['label_text'][m0:], minor=True)

    def set_colormap(self, data, **kwargs):
        """
        Replace the color list with discrete values from a colormap

        Args:
            data (Data object)
        """

        if not self.cmap or self.name in \
                ['contour', 'heatmap', 'imshow']:
            return

        try:
            # Conver the color map into discrete colors
            cmap = mplp.get_cmap(self.cmap)
            color_list = []
            if data.legend_vals is None or len(data.legend_vals) == 0:
                if self.axes.twin_x or self.axes.twin_y:
                    maxx = 2
                else:
                    maxx = 1
            else:
                maxx = len(data.legend_vals)
            for i in range(0, maxx):
                color_list += \
                    [mplc_to_hex(cmap((i+1)/(maxx+1)), False)]

            # Reset colors
            if self.legend.column is None:
                if self.axes.twin_x and 'label_y_font_color' not in kwargs.keys():
                    self.label_y.font_color = color_list[0]
                if self.axes.twin_x and 'label_y2_font_color' not in kwargs.keys():
                    self.label_y2.font_color = color_list[1]
                if self.axes.twin_y and 'label_x_font_color' not in kwargs.keys():
                    self.label_x.font_color = color_list[0]
                if self.axes.twin_y and 'label_x_font_color' not in kwargs.keys():
                    self.label_x2.font_color = color_list[1]

            self.lines.color.values = copy.copy(color_list)
            self.lines.color_alpha('color', 'alpha')
            self.markers.edge_color.values = copy.copy(color_list)
            self.markers.color_alpha('edge_color', 'edge_alpha')
            self.markers.fill_color.values = copy.copy(color_list)
            self.markers.color_alpha('fill_color', 'fill_alpha')

        except:
            print('Could not find a colormap called "%s". '
                  'Using default colors...' % self.cmap)

    def set_figure_final_layout(self, data, **kwargs):
        """
        Final adjustment of the figure size and plot spacing
        """

        # Render dummy figure to get the element sizes
        self.get_element_sizes(data)

        # Clean up tick overlaps
        self.get_tick_xs()

        # Resize the figure
        self.get_figure_size(data, **kwargs)
        self.fig.obj.set_size_inches((self.fig.size_inches[0],
                                      self.fig.size_inches[1]))

        # Adjust subplot spacing
        self.get_subplots_adjust()
        self.fig.obj.subplots_adjust(left=self.axes.position[0],
                                     right=self.axes.position[1],
                                     top=self.axes.position[2],
                                     bottom=self.axes.position[3],
                                     hspace=1.0*self.ws_row/self.axes.size[1],
                                     wspace=1.0*self.ws_col/self.axes.size[0],
                                     )

        # Tick overlap cleanup
        self.get_tick_label_sizes()  # update after axes reshape
        self.get_tick_overlaps()

        # Update the axes label positions
        self.get_axes_label_position()
        labels = ['x', 'x2', 'y', 'y2', 'z', 'row', 'col']
        for label in labels:
            # for ir, ic in np.ndindex(ax.obj.shape):
            lab = getattr(self, f'label_{label}')
            if not lab.on:
                continue
            x, y = getattr(self, f'label_{label}').position_xy
            for ir, ic in np.ndindex(lab.obj.shape):
                if lab.obj[ir, ic]:
                    lab.obj[ir, ic].set_position((x, y))

        # Update the rc label positions
        self.get_rc_label_position()
        # row
        for ir, ic in np.ndindex(self.label_row.obj.shape):
            if self.label_row.obj[ir, ic]:
                if self.label_row.rotation == 270 and not self.label_col.on:
                    offset = -2
                else:
                    offset = 0
                x_rect = self.label_row.position[0]
                x_text = x_rect + \
                    (self.label_row.size[0] / 2 + offset) / \
                    self.axes.size[0]
                self.label_row.obj[ir, ic].set_position((x_text, 0.5))
                self.label_row.obj_bg[ir, ic].set_x(x_rect)
        # col
        for ir, ic in np.ndindex(self.label_col.obj.shape):
            if self.label_col.obj[ir, ic]:
                if self.label_col.rotation == 0 and not self.label_row.on:
                    offset = -2
                else:
                    offset = 0
                y_rect = self.label_col.position[3]
                y_text = y_rect + \
                    (self.label_col.size[1] / 2 + offset) / \
                    self.axes.size[1]
                self.label_col.obj[ir, ic].set_position((0.5, y_text))
                self.label_col.obj_bg[ir, ic].set_y(y_rect)
        # wrap label
        if self.name in ['imshow'] and self.ncol > 1:
            hack = 0  # some weirdness on cbar or imshow plots; here is a stupid hack
        elif self.name in ['imshow']:
            hack = -1
        else:
            hack = 1
        for ir, ic in np.ndindex(self.label_wrap.obj.shape):
            if self.label_wrap.obj[ir, ic]:
                offset = 0
                y_rect = self.label_wrap.position[3]
                y_text = y_rect + \
                    (self.label_wrap.size[1] / 2 + offset) / \
                    self.axes.size[1]
                self.label_wrap.obj[ir, ic].set_position((0.5, y_text))
                self.label_wrap.obj_bg[ir, ic].set_y(y_rect)
                self.label_wrap.obj_bg[ir, ic].set_width(
                    1 + hack / self.axes.size[0])
        # wrap title
        if self.title_wrap.on:
            offset = 0
            y_rect = self.title_wrap.position[3]
            y_text = y_rect + \
                (self.title_wrap.size[1] / 2 + offset) / \
                self.axes.size[1]
            self.title_wrap.obj.set_position((self.ncol / 2, y_text))
            self.title_wrap.obj_bg.set_y(y_rect)
            self.title_wrap.obj_bg.set_width(
                self.ncol + hack / self.axes.size[0])

        # Update title position
        if self.title.on:
            self.get_title_position()
            self.title.obj.set_position(self.title.position_xy)

        # Update the legend position
        if self.legend.on and self.legend.location in [0, 11]:
            self.get_legend_position()
            self.legend.obj.set_bbox_to_anchor((self.legend.position[1],
                                                self.legend.position[2]))

        # Update the box labels
        if self.box_group_label.on:
            lab = self.box_group_label
            labt = self.box_group_title

            # Determine the box group row heights
            heights = \
                self.box_group_label.size_all_bg.groupby('ii').max()['height']
            heights *= (1 + 2 * self.box_group_label.padding / 100)
            heights /= self.axes.size[1]

            # Iterate through labels
            offset = 1  # to make labels line up better at default font sizes
            for ir, ic in np.ndindex(self.box_group_label.obj.shape):
                data.df_rc = data.subset(ir, ic)
                data.get_box_index_changes()
                if lab.obj[ir, ic] is None:
                    continue
                for ii, jj in np.ndindex(lab.obj[ir, ic].shape):
                    if lab.obj[ir, ic][ii, jj] is None:
                        continue
                    nrows = self.box_group_label.obj[ir, ic].shape[0]
                    box_label_size = self.box_labels / nrows

                    # group label background rectangle
                    lab.obj_bg[ir, ic][ii, jj].set_height(heights[ii])
                    lab.obj_bg[ir, ic][ii, jj].set_y(-heights[0:ii+1].sum())

                    # group label text strings
                    changes = data.changes[data.changes[len(
                        data.changes.columns) - ii - 1] == 1].index.values
                    changes = np.diff(np.append(changes, len(data.changes)))
                    divider = self.axes.size[0] / len(data.changes)
                    xtext = (
                        divider * (changes[jj] / 2 + changes[0:jj].sum())) / self.axes.size[0]
                    ytext = -heights[ii] / 2 - \
                        heights[0:ii].sum() - offset / self.axes.size[1]

                    # apply an offset to better align the text
                    if lab.obj[ir, ic][ii, jj].get_rotation() == 90:
                        xtext += offset / self.axes.size[0]
                    else:
                        ytext -= offset / self.axes.size[1]

                    # set the position
                    lab.obj[ir, ic][ii, jj].set_position((xtext, ytext))

                # group title
                for ii, jj in np.ndindex(labt.obj[ir, ic].shape):
                    # find and set the label position
                    if labt.obj[ir, ic][ii, 0] is None:
                        continue
                    wtitle = labt.size_all.loc[(labt.size_all.ir == ir) & (
                        labt.size_all.ic == ic) & (labt.size_all.ii == ii), 'width']
                    xtitle = 1 + (self.ws_ax_box_title +
                                  wtitle / 2) / self.axes.size[0]
                    ytitle = - \
                        heights[ii] / 2 - heights[0:ii].sum() - (ii+2) * \
                        offset / self.axes.size[1]
                    labt.obj[ir, ic][ii, 0].set_position((xtitle, ytitle))

        # Pie adjustments?

    def set_figure_title(self):
        """
        Add a figure title
        """

        if self.title.on:
            self.get_title_position()
            self.title.obj, self.title.obj_bg = \
                self.add_label(0, 0, self.title.text, offset=True,
                               **self.make_kwargs(self.title))

    def set_scientific(self, ax, tp, idx=0):
        """
        Turn off scientific notation

        Args:
            ax: axis to adjust
            tp (dict): tick label, position dict from mpl_get_ticks
            idx (int): axis number

        Returns:
            updated axise
        """

        def get_sci(ticks, limit):
            """
            Get the scientific notation format string

            Args:
                ticks: tp['?']['ticks']
                limit: ax.get_?lim()
            """

            max_dec = 0
            for itick, tick in enumerate(ticks):
                if tick != 0:
                    if tick < 0:
                        power = np.nan
                    else:
                        power = np.ceil(-np.log10(tick))
                    if np.isnan(power) or tick < limit[0] or tick > limit[1]:
                        continue
                    dec = utl.get_decimals(tick*10**power)
                    max_dec = max(max_dec, dec)
            dec = '%%.%se' % max_dec
            return dec

        if idx == 0:
            lab = ''
        else:
            lab = '2'

        # Select scientific notation unless specified
        bestx, besty = False, False

        if self.tick_labels_major_x.sci == 'best' and len(tp['x']['ticks']) > 0:
            xrange = tp['x']['ticks'][-1] - tp['x']['ticks'][0]
            nonzero = tp['x']['ticks'][tp['x']['ticks'] != 0]
            xthresh = np.any(np.abs(nonzero) <= self.auto_tick_threshold[0]) or \
                np.any(np.abs(nonzero) >= self.auto_tick_threshold[1])
            if xrange <= self.auto_tick_threshold[0] or \
                    xrange >= self.auto_tick_threshold[1] or xthresh:
                tick_labels_major_x_sci = True
            else:
                tick_labels_major_x_sci = False
            bestx = True
        elif self.tick_labels_major_x.sci == 'best':
            tick_labels_major_x_sci = False
        else:
            tick_labels_major_x_sci = self.tick_labels_major_x.sci

        if self.tick_labels_major_y.sci == 'best' and len(tp['y']['ticks']) > 0:
            yrange = tp['y']['ticks'][-1] - tp['y']['ticks'][0]
            nonzero = tp['y']['ticks'][tp['y']['ticks'] != 0]
            ythresh = np.any(np.abs(nonzero) <= self.auto_tick_threshold[0]) or \
                np.any(np.abs(nonzero) >= self.auto_tick_threshold[1])
            if yrange <= self.auto_tick_threshold[0] or \
                    yrange >= self.auto_tick_threshold[1] or ythresh:
                tick_labels_major_y_sci = True
            else:
                tick_labels_major_y_sci = False
            besty = True
        elif self.tick_labels_major_y.sci == 'best':
            tick_labels_major_y_sci = False
        else:
            tick_labels_major_y_sci = self.tick_labels_major_y.sci

        # Set labels
        logx = getattr(self, 'axes%s' % lab).scale in LOGX + SYMLOGX + LOGITX
        if self.name in ['hist'] and self.hist.horizontal == True and \
                self.hist.kde == False:
            ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
        elif not tick_labels_major_x_sci \
                and self.name not in ['box', 'heatmap'] \
                and not logx:
            try:
                ax.get_xaxis().get_major_formatter().set_scientific(False)
            except:
                pass

        elif not tick_labels_major_x_sci \
                and self.name not in ['box', 'heatmap']:
            try:
                ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
                # need to recompute the ticks after changing formatter
                tp = mpl_get_ticks(ax, minor=self.ticks_minor.on)
                for itick, tick in enumerate(tp['x']['ticks']):
                    if tick < 1 and tick > 0:
                        digits = -np.log10(tick)
                    else:
                        digits = 0
                    tp['x']['label_text'][itick] = \
                        '{0:.{digits}f}'.format(tick, digits=int(digits))
                ax.set_xticklabels(tp['x']['label_text'])
            except:
                pass
        elif (bestx and not logx
                or not bestx and tick_labels_major_x_sci and logx) \
                and self.name not in ['box', 'heatmap']:
            xlim = ax.get_xlim()
            dec = get_sci(tp['x']['ticks'], xlim)
            ax.get_xaxis().set_major_formatter(ticker.FormatStrFormatter(dec))

        logy = getattr(self, 'axes%s' % lab).scale in LOGY + SYMLOGY + LOGITY
        if self.name in ['hist'] and self.hist.horizontal == False and \
                self.hist.kde == False:
            ax.get_yaxis().set_major_locator(MaxNLocator(integer=True))
        elif not tick_labels_major_y_sci \
                and self.name not in ['heatmap'] \
                and not logy:
            try:
                ax.get_yaxis().get_major_formatter().set_scientific(False)
            except:
                pass

        elif not tick_labels_major_y_sci \
                and self.name not in ['heatmap']:
            try:
                ax.get_yaxis().set_major_formatter(ticker.ScalarFormatter())
                # need to recompute the ticks after changing formatter
                tp = mpl_get_ticks(ax, minor=self.ticks_minor.on)
                for itick, tick in enumerate(tp['y']['ticks']):
                    if tick < 1 and tick > 0:
                        digits = -np.log10(tick)
                    else:
                        digits = 0
                    tp['y']['label_text'][itick] = \
                        '{0:.{digits}f}'.format(tick, digits=int(digits))
                ax.set_yticklabels(tp['y']['label_text'])
            except:
                pass
        elif (besty and not logy
                or not besty and tick_labels_major_y_sci and logy) \
                and self.name not in ['heatmap']:
            ylim = ax.get_ylim()
            dec = get_sci(tp['y']['ticks'], ylim)
            ax.get_yaxis().set_major_formatter(ticker.FormatStrFormatter(dec))

        # Cbar z-axis
        if self.tick_labels_major_z.sci == True and self.cbar.on:
            ax = self.cbar.obj.ax
            ylim = ax.get_ylim()
            tp = mpl_get_ticks(ax, minor=False)
            dec = get_sci(tp['y']['ticks'], ylim)
            ax.get_yaxis().set_major_formatter(ticker.FormatStrFormatter(dec))
        elif self.tick_labels_major_z.sci == False and self.cbar.on:
            try:
                self.cbar.obj.ax.get_yaxis().set_major_formatter(ticker.ScalarFormatter())
                self.cbar.obj.ax.get_yaxis().get_major_formatter().set_scientific(False)
            except:
                pass

        return ax

    def show(self, filename=None):
        """
        Handle display of the plot window
        """

        mplp.show(block=False)

    def update_subplot_spacing(self):
        """
        Update spacing for long labels
        """
        if self.label_y.size[1] > self.axes.size[1]:
            self.ws_row += self.label_y.size[1] - self.axes.size[1]
        if self.label_x.size[0] > self.axes.size[0]:
            self.ws_col += self.label_x.size[0] - self.axes.size[0]
        if self.axes.twin_x and self.separate_ticks \
                and self.tick_labels_major_y2.on:
            self.ws_col += self.tick_labels_major_y2.size[0]
        if self.axes.twin_x and self.separate_labels:
            self.ws_col += self.label_y2.size[0]
