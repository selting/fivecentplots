############################################################################
# fcp.py
#   Custom library of plot functions based on matplotlib to generate more
#   attractive plots more easily.  Part of the fivecentplots project.
############################################################################
__author__    = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2016 Steve Nicholes'
__license__   = 'GPLv3'
__version__   = '0.2.0'
__url__       = 'https://github.com/endangeredoxen/fivecentplots'

import os
import matplotlib.pyplot as mplp
import matplotlib.ticker as ticker
import matplotlib.patches as patches
import numpy as np
import scipy.stats as stats
import pandas as pd
import pdb
import re
import importlib
import itertools
import shutil
import sys
from fivecentplots.design import FigDesign
import fivecentplots.fileio as fileio
try:
    import win32clipboard
except:
    print('Could not import win32clipboard.  Make sure pywin32 is installed '
          'to use the paste from clipboard option.')
try:
    from natsort import natsorted
except:
    natsorted = sorted
st = pdb.set_trace
osjoin = os.path.join
cur_dir = os.path.dirname(__file__)
user_dir = os.path.expanduser('~')
if not os.path.exists(osjoin(user_dir, '.fivecentplots')):
    os.makedirs(osjoin(user_dir, '.fivecentplots'))
if not os.path.exists(osjoin(user_dir, '.fivecentplots','defaults.py')):
    shutil.copy2(osjoin(cur_dir, 'defaults.py'),
                 osjoin(user_dir, '.fivecentplots', 'defaults.py'))
sys.path = [osjoin(user_dir, '.fivecentplots')] + sys.path
from defaults import *  # use local file


def add_curves(plotter, x, y, color='#000000', marker='o', points=False,
               line=True, **kwargs):
    """ Adds curve data to an axes

    Args:
        plotter (mpl plot obj):  plot, semilogx, semilogy, loglog
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
        else: return r'$%s$' % marker
    
    if points:
        kw = kwargs.copy()
        kw['linewidth'] = 0
        kw['linestyle'] = 'none'
        points = plotter(x, y, color=color, marker=format_marker(marker),
                         markerfacecolor='none', markeredgecolor=color,
                         markeredgewidth=1.5, **kw)
        
    if line:
        kw = kwargs.copy()
        kw['markersize'] = 0
        lines = plotter(x, y, color=color, **kw)
    if points:
        return points
    else:
        return lines


def add_label(label, pos, axis, rotation, fillcolor='#ffffff',
              edgecolor='#aaaaaa', color='#666666', weight='bold',
              fontsize=14):
    """ Add a label to the plot

    This function can be used for title labels or for group labels applied
    to rows and columns when plotting facet grid style plots.

    Args:
        label (str):  label text
        pos (tuple): label position tuple of form (left, bottom, width, height)
        axis (matplotlib.axes):  mpl axes object
        rotation (int):  degrees of rotation
        fillcolor (str):  hex color code for label fill (default='#ffffff')
        edgecolor (str):  hex color code for label edge (default='#aaaaaa')
        color (str):  hex color code for label text (default='#666666')
        weight (str):  label font weight (use standard mpl weights like 'bold')
        fontsize (int):  label font size (default=14)
    """
    
    # Define the label background
    rect = patches.Rectangle((pos[0], pos[1]), pos[2], pos[3],
                             fill=True, transform=axis.transAxes,
                             facecolor=fillcolor, edgecolor=edgecolor,
                             clip_on=False, zorder=-1)
    axis.add_patch(rect)

    # Add the label text
    axis.text(pos[0]+pos[2]/2, pos[1]+pos[3]/2, label,
              transform=axis.transAxes, horizontalalignment='center',
              verticalalignment='center', rotation=rotation, color=color,
              weight=weight, fontsize=fontsize)


def boxplot(**kwargs):
    """ Main boxplot function

    This function wraps the boxplot function from the matplotlib
    library.  At minimum, it requires a pandas DataFrame with at least one
    column and a column name for the y axis.  Plots can be
    customized and enhanced by passing keyword arguments as defined below.
    Default values that must be defined in order to generate the plot are
    pulled from the fcp_params dictionary defined in defaults.py.

    Required Keyword Args:
        df (DataFrame): DataFrame containing data to plot
        y (str|list):   name or list of names of y column in df

    Keyword Args:
        ax_edge_color (str):  hex color code for axis edge border color
            (default from fcp_params)
        ax_face_color (str):  hex color code for axis fill color (default from
            fcp_params)
        ax_fig_ws (int):  axis to figure right whitespace (default from
            fcp_params)
        ax_hlines (list):  list of y-values at which to add horizontal lines
            (default=[])
        ax_label_pad (int):  label offset padding in pixels (default=0)
        ax_lim (list):  axes range values [xmin, xmax, ymin, ymax] (default=[])
        ax_lim_pad (float):  in place of discrete axes limits, adds whitespace
            to the bottom|top and left|right of the axis by this amount as a
            percent/100 of the total axis range (default=0.05)
        ax_scale (None|str):  set the scale of an axis as linear or log
            (default=None --> linear; options include 'logx'|'semilogx' for the
            x-axis, 'logy'|'semilogy' for the y-axis or 'loglog' for both axes
        ax_size (list):  [width, height] of each plot window in pixels
            (default defined by fcp_params)
        bp_divider_color (str): hex color code for divider line color between
            groups (default from fcp_params)
        bp_fill_color (str):  hex color code for boxplot fill color (default
            from fcp_params)
        bp_labels_on (bool):  toggle on|off boxplot grouping labels
            (default=True)
        bp_label_size (int):  grouping label size (default from fcp_params)
        bp_label_edge_color (str):  hex color code for boxplot grouping label
            regions (default from fcp_params)
        bp_label_fill_color (str):  hex color code for grouping labels (default
            from fcp_params)
        bp_label_font_size (int):  grouping label font size (default from
            fcp_params)
        bp_label_text_color (str):  hex color code for grouping label text
            (default from fcp_params)
        bp_label_text_style (str):  grouping label text style; use standard
            mpl styles like 'italic' (default from fcp_params)
        bp_label_text_weight (str):  grouping label text weight; use standard
            mpl weights like 'bold' (default from fcp_params)
        bp_name_font_size (str):  grouping label summary name font size
            (default from fcp_params)
        bp_name_text_color (str):  hex color code for grouping label summary
            name (default from fcp_params)
        bp_name_text_style (str):  grouping label summary name text style; use
            standard mpl styles like 'italic' (default from fcp_params)
        bp_name_text_weight (str):  grouping label summary name text weight;
            use standard mpl weights like 'bold' (default from fcp_params)
        bp_name_ws (int):  whitespace in pixels between grouping labels under
            the boxplot and the summary names (default from fcp_params)
        colors (list):  list of tuple values used to define colors for plotting
            using RGB/255 mpl style (default is palette from defaults.py)
        connect_means (bool):  draw a line connecting the mean value of each
            group in the boxplot (default=False)
        dividers (bool):  show vertical diveider lines between groups
            (default=True)
        fig_ax_ws (int):  number of pixels between the left figure edge and the
            left axis edge (default from fcp_params)
        fig_edge_color (str):  hex color code for figure edge color (default
            from fcp_params)
        fig_face_color (str):  hex color code for figure fill color (default
            from fcp_params)
        fig_groups (list|None):  name of df column by which to group the data
            and make discrete figures based on the unique values in this column
            (default=None)
        fig_group_path (bool):  use the unique grouping item from fig_groups
            in the plot filename (default=False)
        filename (str):  name of saved figure (default=None--> custom filename
            will be built based on the data that is plotted
        filter (str):  str to use in df.query to include or exclude certain
            data from df (default=None).  Note that df.query does not support
            spaces, parenthesis, or brackets. Spaces should be replaced by '_'
            and parenthesis/brackets should be dropped from the str.  Example:
            Temperature [C] --> Temperature_C
        grid_major (bool):  toggle major gridlines (default=True)
        grid_major_color (str):  hex color code for major gridline color
            (default from fcp_params)
        grid_major_linestyle (str):  matplotlib str code for linestyle (default
            from fcp_params)
        grid_minor (bool):  toggle minor gridlines (default=False)
        grid_minor_color (str):  hex color code for minor gridline color
            (default from fcp_params)
        grid_minor_linestyle (str):  matplotlib str code for linestyle (default
            from fcp_params)
        groups (list?):  (default=None)
        jitter (bool):  jitter the data points (default=False)
        label_font_size (int):  font size in pixels for the x and y labels
            (default from fcp_params)
        label_style (str):  define the label style (default from fcp_params).
            Use standard mpl styles like 'italic'
        label_weight (str):  define the label weight (default from fcp_params).
            Use standard mpl weights like 'bold'
        leg_bkgrd (str):  hex color code for legend background (default from
            fcp_params)
        leg_border (str):  hex color code for legend border (default from
            fcp_params)
        leg_groups (str):  name of df column by which to legend the data
            (default=None)
        leg_items (str):  explicit definition of the legend items; ignores any
            values that are not listed (default=None)
        leg_on (bool):  toggle legend visibility (default=True)
        leg_title (str):  title for the legend (default=None)
        line_width (int):  set the linewidth of connect means line (default=1)
        lines (bool):  turn plot lines on|off (default=True)
        marker_size (int):  set marker size (default from fcp_params)
        marker_type (str):  set marker type (default==None)
        points (bool):  turn markers on|off (default=True)
        save_ext (str):  filename extension for saved figures (default='png')
        save_path (str):  destination file folder for plots (default=None)
        scalar_y (bool):  force scalar tick labels on the y-axis instead of
            powers of ten (default=False)
        show (bool):  pop open plot after it is generated.  Otherwise, the plot
            is just saved (default=False)
        tick_major_color (str):  hex color code for major tick marks (default
            from fcp_params)
        tick_minor_color (str):  hex color code for minor tick marks (default
            from fcp_params)
        tick_font_size (int):  font size for tick labels (default from
            fcp_params)
        tick_label_color (str):  hex color code for tick labels (default
            from fcp_params)
        tick_length (int):  length of the tick marks (default from fcp_params)
        tick_width (int):  line width of the tick marks (default from
            fcp_params)
        title (str):  plot title (default=None)
        title_edge_color (str):  hex color code for edge of a box around the
            plot title (default from fcp_params)
        title_fill_color (str):  hex color code for fill of a box around the
            plot title (default from fcp_params)
        title_text_color (str):  hex color code for title color (default from
            fcp_params)
        title_font_size (int):  font size of plot title (default from
            fcp_params)
        title_text_style (str):  define the title style. Use standard mpl
            styles like 'italic' (default from fcp_params)
        ylabel (str):  label for primary y-axis (default=kwargs['y'] or
            kwargs['y'][0])
        ymax (float):  maximum y-value on y-axis (default=None --> use mpl
            defaults)
        ymin (float):  minimum y-value of y-axis (default=None --> use mpl
            defaults)
        yticks (int):  specify the number of yticks (not currently supported)
            (default=None --> use mpl defaults)

    Returns:
        design (FigDesign obj):  contains all the spacing information used to
            construct the figure
    """

    kw = {}
    df = kwargs.get('df')
    if df is None:
        raise ValueError('Must provide a DataFrame called "df" for analysis!')

    y = kwargs.get('y')
    if y is None:
        raise ValueError('Must provide a column name for "y"')


    kw['ax_edge_color'] = kwargs.get('ax_edge_color',
                                     fcp_params['ax_edge_color'])
    kw['ax_face_color'] = kwargs.get('ax_face_color',
                                     fcp_params['ax_face_color'])
    kw['ax_fig_ws'] = kwargs.get('ax_fig_ws', fcp_params['ax_fig_ws'])
    kw['ax_hlines'] = kwargs.get('ax_hlines', [])
    kw['ax_label_pad'] = kwargs.get('ax_label_pad', fcp_params['ax_label_pad'])
    kw['ax_lim'] = kwargs.get('ax_lim', [])
    kw['ax_lim_pad'] = kwargs.get('ax_lim_pad', 0.05)
    kw['ax_scale'] = kwargs.get('ax_scale', None)
    kw['ax_size'] = kwargs.get('ax_size', fcp_params['ax_size'])
    kw['bp_divider_color'] = kwargs.get('bp_divider_color',
                                        fcp_params['bp_divider_color'])
    kw['bp_fill_color'] = kwargs.get('bp_fill_color',
                                        fcp_params['bp_fill_color'])
    kw['bp_labels_on'] = kwargs.get('bp_labels_on', True)
    kw['bp_label_size'] = kwargs.get('bp_label_size',
                                     fcp_params['bp_label_size'])
    kw['bp_label_edge_color'] = kwargs.get('bp_label_edge_color',
                                           fcp_params['bp_label_edge_color'])
    kw['bp_label_fill_color'] = kwargs.get('bp_label_fill_color',
                                           fcp_params['bp_label_fill_color'])
    kw['bp_label_font_size'] = kwargs.get('bp_label_font_size',
                                          fcp_params['bp_label_font_size'])
    kw['bp_label_text_color'] = kwargs.get('bp_label_text_color',
                                           fcp_params['bp_label_text_color'])
    kw['bp_label_text_style'] = kwargs.get('bp_label_text_style',
                                           fcp_params['bp_label_text_style'])
    kw['bp_label_text_weight'] = kwargs.get('bp_label_text_weight',
                                            fcp_params['bp_label_text_weight'])
    kw['bp_name_font_size'] = kwargs.get('bp_name_font_size',
                                          fcp_params['bp_name_font_size'])
    kw['bp_name_text_color'] = kwargs.get('bp_name_text_color',
                                           fcp_params['bp_name_text_color'])
    kw['bp_name_text_style'] = kwargs.get('bp_name_text_style',
                                           fcp_params['bp_name_text_style'])
    kw['bp_name_text_weight'] = kwargs.get('bp_name_text_weight',
                                            fcp_params['bp_name_text_weight'])
    kw['bp_name_ws'] = kwargs.get('bp_name_ws', fcp_params['bp_name_ws'])
    kw['col'] = kwargs.get('col', None)
    kw['col_label'] = kwargs.get('col_label', None)
    kw['col_labels_on'] = kwargs.get('col_labels_on', True)
    kw['col_label_size'] = kwargs.get('col_label_size',
                                      fcp_params['rc_label_size'])
    kw['col_label_ws'] = kwargs.get('col_label_ws', fcp_params['rc_label_ws'])
    kw['col_padding'] = kwargs.get('col_padding', fcp_params['col_padding'])
    kw['colors'] = kwargs.get('colors', palette)
    kw['cols'] = kwargs.get('cols', None)
    kw['colors'] = kwargs.get('colors', palette)
    kw['connect_means'] = kwargs.get('connect_means', False)
    kw['dividers'] = kwargs.get('dividers', True)
    kw['fig_ax_ws'] = kwargs.get('fig_ax_ws',
                                 fcp_params['fig_ax_ws'])
    kw['fig_edge_color'] = kwargs.get('fig_edge_color',
                                     fcp_params['fig_edge_color'])
    kw['fig_face_color'] = kwargs.get('fig_face_color',
                                     fcp_params['fig_face_color'])
    kw['fig_groups'] = kwargs.get('fig_groups', None)
    kw['fig_group_path'] = kwargs.get('fig_group_path', False)
    kw['filename'] = kwargs.get('filename', None)
    kw['filter'] = kwargs.get('filter', None)
    kw['grid_major_color'] = kwargs.get('grid_major_color',
                                        fcp_params['grid_major_color'])
    kw['grid_major_linestyle'] = kwargs.get('grid_major_linestyle',
                                        fcp_params['grid_major_linestyle'])
    kw['grid_minor_color'] = kwargs.get('grid_minor_color',
                                        fcp_params['grid_minor_color'])
    kw['grid_minor_linestyle'] = kwargs.get('grid_minor_linestyle',
                                        fcp_params['grid_minor_linestyle'])
    kw['grid_major'] = kwargs.get('grid_major', True)
    kw['grid_minor'] = kwargs.get('grid_minor', False)
    kw['groups'] = kwargs.get('groups', None)
    kw['jitter'] = kwargs.get('jitter', False)
    kw['label_font_size'] = kwargs.get('label_font_size',
                                       fcp_params['label_font_size'])
    kw['label_style'] = kwargs.get('label_style', fcp_params['label_style'])
    kw['label_weight'] = kwargs.get('label_weight', fcp_params['label_weight'])
    kw['leg_bkgrd'] = kwargs.get('leg_bkgrd', fcp_params['leg_bkgrd'])
    kw['leg_border'] = kwargs.get('leg_border', fcp_params['leg_border'])
    kw['leg_groups'] = kwargs.get('leg_groups', None)
    kw['leg_items'] = kwargs.get('leg_items', [])
    kw['leg_on'] = kwargs.get('leg_on', True)
    kw['leg_title'] = kwargs.get('leg_title', None)
    kw['line_width'] = kwargs.get('line_width', fcp_params['line_width'])
    kw['marker_size'] = kwargs.get('marker_size', fcp_params['marker_size'])
    kw['marker_type'] = kwargs.get('marker_type', fcp_params['marker_type'])
    kw['points'] = kwargs.get('points', True)
    kw['rc_label_edge_color'] = kwargs.get('rc_label_edge_color',
                                           fcp_params['rc_label_edge_color'])
    kw['rc_label_fill_color'] = kwargs.get('rc_label_fill_color',
                                           fcp_params['rc_label_fill_color'])
    kw['rc_label_font_size'] = kwargs.get('rc_label_font_size',
                                          fcp_params['rc_label_font_size'])
    kw['rc_label_text_color'] = kwargs.get('rc_label_text_color',
                                           fcp_params['rc_label_text_color'])
    kw['rc_label_text_style'] = kwargs.get('rc_label_text_style',
                                           fcp_params['rc_label_text_style'])
    kw['row'] = kwargs.get('row', None)
    kw['row_label'] = kwargs.get('row_label', None)
    kw['row_labels_on'] = kwargs.get('row_labels_on', True)
    kw['row_label_size'] = kwargs.get('row_label_size',
                                     fcp_params['rc_label_size'])
    kw['row_label_ws'] = kwargs.get('row_label_ws', fcp_params['rc_label_ws'])
    kw['row_padding'] = kwargs.get('row_padding', fcp_params['row_padding'])
    kw['rows'] = kwargs.get('rows', None)
    kw['save_ext'] = kwargs.get('save_ext', 'png')
    kw['save_name'] = kwargs.get('save_name', None)
    kw['save_path'] = kwargs.get('save_path', None)
    kw['scalar_y'] = kwargs.get('scalar_y', False)
    kw['show'] = kwargs.get('show', False)
    kw['tick_major_color'] = kwargs.get('tick_major_color',
                                        fcp_params['tick_major_color'])
    kw['tick_minor_color'] = kwargs.get('tick_minor_color',
                                        fcp_params['tick_minor_color'])
    kw['tick_font_size'] = kwargs.get('tick_font_size',
                                      fcp_params['tick_font_size'])
    kw['tick_label_color'] = kwargs.get('tick_label_color',
                                      fcp_params['tick_label_color'])
    kw['tick_length'] = kwargs.get('tick_length', fcp_params['tick_length'])
    kw['tick_width'] = kwargs.get('tick_width', fcp_params['tick_width'])
    kw['title'] = kwargs.get('title', None)
    kw['title_edge_color'] = kwargs.get('title_edge_color',
                                        fcp_params['title_edge_color'])
    kw['title_fill_color'] = kwargs.get('title_fill_color',
                                        fcp_params['title_fill_color'])
    kw['title_text_color'] = kwargs.get('title_text_color',
                                        fcp_params['title_text_color'])
    kw['title_font_size'] = kwargs.get('title_font_size',
                                        fcp_params['title_font_size'])
    kw['title_text_style'] = kwargs.get('title_text_style',
                                        fcp_params['title_text_style'])
    kw['ylabel'] = kwargs.get('ylabel', y)
    kw['ymax'] = kwargs.get('ymax', None)
    kw['ymin'] = kwargs.get('ymin', None)
    kw['yticks'] = kwargs.get('yticks', None)


    def add_points(x, y, ax, color, **kw):

        if kw['jitter']:
            x = np.random.normal(x+1, 0.04, size=len(y))
        else:
            x = np.array([x+1]*len(y))
        ax.plot(x, y,
                color=palette[1],
                markersize=kw['marker_size'],
                marker=kw['marker_type'],
                markeredgecolor=palette[1],
                markerfacecolor='none',
                markeredgewidth=1.5,
                linestyle='none')

    # Turn off interactive plotting
    mplp.ioff()

    # Clear out existing plot buffer
    mplp.close('all')

    # Convert column types
    try:
        df[y] = df[y].astype(float)
    except:
        raise ValueError('Could not convert y-column to float!')

    # Handle single level groupings
    if type(kw['groups']) is not list and kw['groups'] is not None:
            kw['groups'] = [kw['groups']]

    # # Dummy-proof colors
    # if type(kw['colors'][0]) is not tuple:
    #     kw['colors'] = [kw['colors']]
    # else:
    #     kw['colors'] = list(kw['colors'])
    # kw['colors'] += [f for f in palette if f not in kw['colors']]

    # Filter the dataframe
    if kw['filter']:
        df = df_filter(df, kw['filter'])
    if len(df) == 0:
        print('No data remains after filter.  Killing plot.')
        return None
    
    # Set up the figure grouping and iterate (each value corresponds to a
    #  separate figure)
    if kw['fig_groups'] is not None:
        if type(kw['fig_groups']) is list:
            kw['fig_items'] = list(df.groupby(kw['fig_groups']).groups.keys())
        else:
            kw['fig_items'] = list(df[kw['fig_groups']].unique())
    else:
        kw['fig_items'] = [None]

    if kw['fig_group_path'] is not None and type(kw['fig_group_path']) is str:
        temp = list(df.groupby([kw['fig_groups'], 
                                kw['fig_group_path']]).groups.keys())
        kw['fig_path_items'] = [f[1] for f in temp]
    else:
        kw['fig_path_items'] = kw['fig_items']
    
    # Eliminate title buffer if no title is provided
    if not kw['title']:
        kw['title_h'] = 0
    
    # Iterate over discrete figures
    for ifig, fig_item in enumerate(kw['fig_items']):
        
        # Make a data subset and filter
        df_fig = df.copy()
        
        if type(fig_item) is tuple:
            for ig, g in enumerate(fig_item):
                df_fig = df_fig[df_fig[kw['fig_groups'][ig]]==g]
        elif kw['fig_groups'] is not None:
            df_fig = df_fig[df_fig[kw['fig_groups']]==fig_item]

        # Set up the row grouping
        if kw['row'] and not kw['rows']:
            rows = natsorted(list(df_fig[kw['row']].unique()))
            nrow = len(rows)
        elif kw['rows']:
            actual = df[kw['row']].unique()
            rows = [f for f in kw['rows'] if f in actual]
            nrow = len(rows)
        else:
            rows = [None]
            kw['row_labels_on'] = False
            kw['row_label_size'] = 0
            nrow = 1
        kw['nrow'] = nrow

        # Set up the column grouping
        if kw['col'] and not kw['cols']:
            cols = natsorted(list(df_fig[kw['col']].unique()))
            ncol = len(cols)
        elif kw['cols']:
            actual = df[kw['col']].unique()
            cols = [f for f in kw['cols'] if f in actual]
            ncol = len(cols)
        else:
            cols = [None]
            kw['col_labels_on'] = False
            kw['col_label_size'] = 0
            ncol = 1
        kw['ncol'] = ncol
        
        if kw['bp_labels_on'] and kw['groups'] is not None:
            kw['row_padding'] = kw['bp_label_size']*(len(kw['groups'])+0.5) + 20
            kw['ax_fig_ws'] = kw['row_padding'] + 10
            kw['fig_ax_ws'] = 100
            kw['ax_leg_fig_ws'] = max([len(gr) for gr in kw['groups']]) * \
                                  kw['bp_label_font_size'] + \
                                  kw['bp_name_ws']
        
        # Account for scalar formatted axes
        if kw['scalar_y']:
            max_y = df[y].values.max()
            max_y = int(10**(np.ceil(np.log10(df[y].values.max()))-3))
            kw['fig_ax_ws'] += 10*len(str(max_y))
        
        # Format the figure dimensions
        design = FigDesign(**kw)
        
        # Make the figure and axes
        if ncol == 0:
            raise ValueError('Cannot make subplot. Number of columns is 0')
        if nrow == 0:
            raise ValueError('Cannot make subplot. Number of rows is 0')
        fig, axes = mplp.subplots(nrow, ncol,
                                  figsize=[design.fig_w, design.fig_h],
                                  dpi=design.dpi,
                                  facecolor=kw['fig_face_color'],
                                  edgecolor=kw['fig_edge_color'])

        # Reformat the axes variable if it is only one plot
        if not type(axes) is np.ndarray:
            axes = np.array([axes])
        if len(axes.shape) == 1:
            if nrow == 1:
                axes = np.reshape(axes, (1, -1))
            else:
                axes = np.reshape(axes, (-1, 1))

        # Format the subplot spacing
        fig.subplots_adjust(
            left=design.left,
            right=design.right,
            bottom=design.bottom,
            top=design.top + kw['ax_fig_ws']/design.ax_h,
            hspace=1.0*design.row_padding/design.ax_h,
            wspace=1.0*design.col_padding/design.ax_w
        )

        for ir, r in enumerate(rows):
            for ic, c in enumerate(cols):
                # Init arrays
                data = []
                labels = []
                dividers = []
                means = []
                medians = []

                # Set colors
                axes[ir,ic].set_axis_bgcolor(kw['ax_face_color'])
                axes[ir,ic].spines['bottom'].set_color(kw['ax_edge_color'])
                axes[ir,ic].spines['top'].set_color(kw['ax_edge_color']) 
                axes[ir,ic].spines['right'].set_color(kw['ax_edge_color'])
                axes[ir,ic].spines['left'].set_color(kw['ax_edge_color'])
                
                # Style major gridlines
                if kw['grid_major']:
                    axes[ir,ic].grid(b=True, which='major', zorder=3,
                                      color=kw['grid_major_color'], 
                                      linestyle=kw['grid_major_linestyle'])
                
                # Toggle minor gridlines
                kw['grid_minor'] = str(kw['grid_minor'])
                axes[ir,ic].minorticks_on()
                if kw['grid_minor'] == 'True' or \
                    kw['grid_minor'].lower() == 'both':
                    axes[ir,ic].grid(b=True, 
                                      color=kw['grid_minor_color'], 
                                      which='minor', zorder=0,
                                      linestyle=kw['grid_minor_linestyle'])
                elif kw['grid_minor'].lower() == 'y':
                    axes[ir,ic].yaxis.grid(b=True, 
                                        color=kw['grid_minor_color'],
                                        which='minor',
                                        linestyle=kw['grid_minor_linestyle'])
                
                # Build the row/col filename labels
                if kw['row_label']:
                    fnrow = filename_label(kw['row_label'])
                elif kw['row']:
                    fnrow = filename_label(kw['row'])
                if kw['col_label']:
                    fncol = filename_label(kw['col_label'])
                elif kw['col']:
                    fncol = filename_label(kw['col'])

                # Subset the data
                if r is not None and c is not None:
                    df_sub = df_fig[(df_fig[kw['row']]==r)&\
                                    (df_fig[kw['col']]==c)].copy()
                    rc_name = ' by %s by %s' % (fnrow, fncol)
                elif r and not c:
                    df_sub = df_fig[(df_fig[kw['row']]==r)].copy()
                    rc_name = ' by %s' % (fnrow)
                elif c and not r:
                    df_sub = df_fig[(df_fig[kw['col']]==c)].copy()
                    rc_name = ' by %s' % (fncol)
                else:
                    df_sub = df_fig.copy()
                    rc_name = ''
                
                num_groups = 0
                changes = None
                if kw['groups'] is not None:
                    groups = df_sub.groupby(kw['groups'])
                    num_groups = groups.ngroups
                    num_groupby = len(kw['groups'])
                    col = ['Level%s' % f for f in range(0, num_groupby)]
                    indices = pd.DataFrame()

                    # Get the group indices in order
                    for i, (n, g) in enumerate(groups):
                        if type(n) is not tuple:
                            n = [n]
                        indices[i] = [f for f in n]
                    indices = indices.T
                    changes = indices.copy()

                    for i in range(1, num_groups):
                        for c in indices.columns:
                            if indices[c].iloc[i-1] == indices[c].iloc[i]:
                                changes.loc[i, c] = 0
                            else:
                                changes.loc[i, c] = 1
                            if i == 1:
                                changes.loc[i-1, c] = 1
                    col = changes.columns

                    # Plot the groups
                    for i, (n,g) in enumerate(groups):
                        data += [g[y]]
                        means += [g[y].mean()]
                        medians += [g[y].median()]
                        if type(n) is not tuple:
                            nn = [n]
                        else:
                            nn = [str(f) for f in n]
                        labels += ['']

                        if len(changes.columns) > 1 and changes[col[0]].iloc[i] == 1 \
                                and len(kw['groups']) > 1:
                            dividers += [i+0.5]

                        if kw['points']:
                            add_points(i, g[y], axes[ir,ic], palette[1], **kw)

                else:
                    data = df_sub[y]
                    labels = ['']
                    if kw['points']:
                        add_points(0, data, axes[ir,ic], palette[1], **kw)

                # Plot
                if kw['points']:
                    showfliers = False
                else:
                    showfliers = True

                if type(data) is pd.Series:
                    data = data.values
                bp = axes[ir,ic].boxplot(data, labels=labels, showfliers=showfliers,
                                boxprops={'color': palette[0]},
                                whiskerprops={'color': palette[0]},
                                capprops={'color': palette[0]},
                                medianprops={'color': palette[1]},
                                patch_artist=True,
                                )
                axes[ir,ic].xaxis.grid(False)
                for patch in bp['boxes']:
                    patch.set_facecolor(kw['bp_fill_color'])
                for flier in bp['fliers']:
                    flier.set(marker='+', markeredgecolor=palette[0]) # can't set with flierprops





                # Add divider lines
                if kw['dividers']:
                    for d in dividers:
                        axes[ir,ic].axvline(d, linewidth=1, color=kw['bp_divider_color'])

                # Add mean/median connecting lines
                if kw['connect_means']:
                    x = np.linspace(1, num_groups, num_groups)
                    axes[ir,ic].plot(x, means, color=palette[2])

                # Add y-axis label
                if kw['ylabel'] is not None:
                    axes[ir,ic].set_ylabel(r'%s' % kw['ylabel'],
                                  fontsize=kw['label_font_size'],
                                  weight=kw['label_weight'],
                                  style=kw['label_style'])

                # Format the subplot spacing
                fig.subplots_adjust(
                    left=design.left,
                    right=design.right,
                    bottom=design.bottom,
                    top=design.top,
                    hspace=(1.0*design.row_padding)/design.ax_h,
                    wspace=1.0*design.col_padding/design.ax_w
                )
                
                # Add the x-axis grouping labels
                if kw['bp_labels_on'] and changes is not None:
                    num_cols = len(changes.columns)
                    height = kw['bp_label_size']/kw['ax_size'][1]
                    for i in range(0, num_cols):
                        sub = changes[num_cols-1-i][changes[num_cols-1-i]==1]
                        for j in range(0, len(sub)):
                            if j == len(sub) - 1:
                                width = len(changes) - sub.index[j]
                            else:
                                width = sub.index[j+1] - sub.index[j]
                            label = indices.loc[sub.index[j], num_cols-1-i]
                            add_label(label,
                                      (sub.index[j]/len(changes), -height*(i+1),
                                       width/len(changes), height),
                                      axes[ir,ic],
                                      0,
                                      edgecolor=kw['bp_label_edge_color'],
                                      fillcolor=kw['bp_label_fill_color'],
                                      color=kw['bp_label_text_color'],
                                      fontsize=kw['bp_label_font_size'],
                                      weight=kw['bp_label_text_style'])

                    # Add the grouping label names
                    for i, gr in enumerate(kw['groups']):
                        offset = (kw['bp_label_size']-kw['bp_label_font_size']) / \
                                 (2*kw['ax_size'][1])
                        axes[ir,ic].text(1+kw['bp_name_ws']/kw['ax_size'][0],
                                -height*(num_cols-i)+offset, gr,
                                fontsize=kw['bp_name_font_size'],
                                color=kw['bp_name_text_color'],
                                style=kw['bp_name_text_style'],
                                weight=kw['bp_name_text_weight'],
                                transform=axes[ir,ic].transAxes)
                # Add row/column labels
                if ic == len(cols)-1 and kw['row_labels_on']:
                    if not kw['row_label']:
                        kw['row_label'] = kw['row']
                    add_label('%s=%s' % (kw['row_label'], r),
                              (design.row_label_left, 0,
                               design.row_label_width, 1),
                              axes[ir, ic], 270, 
                              edgecolor=kw['rc_label_edge_color'],
                              fillcolor=kw['rc_label_fill_color'],
                              color=kw['rc_label_text_color'],
                              fontsize=kw['rc_label_font_size'],
                              weight=kw['rc_label_text_style'])

                if ir == 0 and kw['col_labels_on']:
                    if not kw['col_label']:
                        kw['col_label'] = kw['col']
                    add_label('%s=%s' % (kw['col_label'], c),
                              (0, design.col_label_bottom,
                               1, design.col_label_height),
                              axes[ir, ic], 0, 
                              edgecolor=kw['rc_label_edge_color'],
                              fillcolor=kw['rc_label_fill_color'],
                              color=kw['rc_label_text_color'],
                              fontsize=kw['rc_label_font_size'],
                              weight=kw['rc_label_text_style'])
    if kw['title'] is not None:
            if '@' in kw['title']:
                r = re.search(r'\@(.*)\@', kw['title'])
                if r:
                    val = r.group(1)
                    pos = r.span()
                    if val in df.columns:
                        val = '%s' % df[val].iloc[0]
                    else:
                        val = ''
                    kw['title'] = \
                        kw['title'][0:pos[0]] + val + kw['title'][pos[1]:]
            add_label('%s' % kw['title'],
                      (design.title_left, design.title_bottom,
                       design.title_w, design.title_h),
                      axes[0,0], 0,
                      edgecolor=kw['title_edge_color'],
                      fillcolor=kw['title_fill_color'],
                      color=kw['title_text_color'],
                      fontsize=kw['title_font_size'],
                      weight=kw['title_text_style']
                      )


    if not kw['filename']:
        if kw['groups']:
            groups = ' vs ' + \
                     ', '.join([filename_label(f) for f in kw['groups']])
        else:
            groups = ''
        filename = filename_label(y) + ' Boxplot' + \
                   groups + '.' + kw['save_ext']
    else:
        filename = kw['filename'] + '.' + kw['save_ext']

    if kw['save_path'] and kw['fig_group_path'] and kw['fig_groups']:
        filename = os.path.join(kw['save_path'], fig_item, filename)
    elif kw['save_path']:
        filename = os.path.join(kw['save_path'], filename)

    fig.savefig(filename)

    if kw['show']:
        # mplp.show()
        os.startfile(filename)

    return design


def df_filter(df, filt):
    """  Filter a DataFrame

    Due to limitations in pd.query, column names must not have spaces.  This
    function will temporarily replace spaces in the column names with
    underscores, but the supplied query string must contain column names
    without any spaces

    Args:
        df (pd.DataFrame):  data set to be filtered
        filt (str):  query expression for filtering

    Returns:
        filtered DataFrame
    """

    df2 = df.copy()
    
    # Remove spaces from
    cols_orig = [f for f in df.columns]
    cols_new = [f.replace(' ', '_')
                 .replace('[', '')
                 .replace(']', '')
                 .replace('(', '')
                 .replace(')', '')
                 .replace('-', '_')
                 .replace('^', '')
                for f in cols_orig.copy()]
    
    df2.columns = cols_new
    
    # Apply the filter
    df2 = df2.query(filt)

    # Reset the columns
    df2.columns = cols_orig
    
    return df2


def filename_label(label):
    """
    Format filename to remove parentheses, brackets, leading/trailing spaces

    Args:
        label (str):  label to format

    Returns:
        formatted label
    """

    label = str(label)
    
    brackets = re.findall('\[.*?\]',label)
    for br in brackets:
        if '*' in br:
            label = label.replace(br, br.replace('*', '_'))
        if '/' in br:
            brs = br.split('/')
            label = ''
            for i in range(0, len(brs), 2):
                if brs[i+1][-1] == ']':
                    label = brs[i] + '_' + brs[i+1][0:-1] + '^-1' + ']'
                else:
                    label = brs[i] + '_' + brs[i+1] + '^-1'
                
    label = label.lstrip(' ').rstrip(' ')

    return label


def get_unique_groups(kw):
    """
    Get all unique values from several kwargs

    Args:
        kw (dict):  keyword args dict

    Returns:
        list of unique group values
    """

    groups = []
    vals_2_chk = ['stat_val', 'leg_groups', 'col', 'row']
    for v in vals_2_chk:
        if kw[v] is not None:
            if type(v) is list:
                groups += kw[v]
            else:
                groups += [kw[v]]
                
    return groups


def paste_kwargs(kwargs):
    """
    Get the kwargs from contents of the clipboard in ini file format

    Args:
        kwargs (dict): originally inputted kwargs

    Returns:
        kwargs
    """

    # Read the pasted data using the ConfigFile class and convert to dict
    config = fileio.ConfigFile(paste=True)
    new_kw = list(config.config_dict.values())[0]

    # Maintain any kwargs originally specified
    for k, v in kwargs.items():
        new_kw[k] = v

    return new_kw


def plot(**kwargs):
    """ Main x-y plotting function

    This function wraps many variations of x-y plots from the matplotlib
    library.  At minimum, it requires a pandas DataFrame with at least two
    columns and two column names for the x and y axis.  Plots can be
    customized and enhanced by passing keyword arguments as defined below.
    Default values that must be defined in order to generate the plot are
    pulled from the fcp_params dictionary defined in defaults.py.
    
    Required Keyword Args:
        df (DataFrame): DataFrame containing data to plot
        x (str):        name of x column in df
        y (str|list):   name or list of names of y column(s) in df  
        
    Keyword Args:
        ax_edge_color (str):  hex color code for axis edge border color
            (default from fcp_params)
        ax_face_color (str):  hex color code for axis fill color (default from
            fcp_params)
        ax_hlines (list):  list of y-values at which to add horizontal lines
            (default=[])
        ax_label_pad (int):  label offset padding in pixels (default=0)
        ax_lim (list):  axes range values [xmin, xmax, ymin, ymax] (default=[])
        ax_lim_pad (float):  in place of discrete axes limits, adds whitespace
            to the bottom|top and left|right of the axis by this amount as a
            percent/100 of the total axis range (default=0.05)
        ax_scale (None|str):  set the scale of an axis as linear or log
            (default=None --> linear; options include 'logx'|'semilogx' for the
            x-axis, 'logy'|'semilogy' for the y-axis or 'loglog' for both axes
        ax_scale2 (None|str): same as ax_scale but for secondary y-axis
            when twinx is True
        ax_size (list):  [width, height] of each plot window in pixels
            (default defined by fcp_params)
        ax_vlines (list):  list of x-values at which to add vertical lines
            (default=[])
        cmap (str): name of color map to use for plotting (default=None -->
            use color order defined in fcp_params
        col (str):  name of a column in df to use as a grouping variable for
            facet grid style plotting; each unique value from df[col] will
            represent a column of plots in the final figure (default=None -->
            no column grouping)
        col_label (str):  a custom label to display for each column in the
            facet grid plot (default=None --> use the value of kwargs['col']
        col_labels_on (bool):  toggle on|off column labels in facet grid plot
            (default=True)
        col_label_size (int):  label height in pixel for col labels in pixels
            (default from fcp_params)
        col_label_ws (int):  whitespace in pixels between axis and col labels
            in pixels (default from fcp_params)
        col_padding (int):  whitespace between facet columns in pixels (default
            in fcp_params)
        colors (list):  list of tuple values used to define colors for plotting
            using RGB/255 mpl style (default is palette from defaults.py)
        cols (list):  list used to manually define the columns to use in the
            facet grid (default=None). These values must actually be in df[col]
        fig_ax_ws (int):  number of pixels between the left figure edge and the
            left axis edge (default from fcp_params)
        fig_edge_color (str):  hex color code for figure edge color (default
            from fcp_params)
        fig_face_color (str):  hex color code for figure fill color (default
            from fcp_params)
        fig_groups (list|None):  name of df column by which to group the data
            and make discrete figures based on the unique values in this column
            (default=None)
        fig_group_path (bool):  use the unique grouping item from fig_groups
            in the plot filename (default=False)
        filename (str):  name of saved figure (default=None--> custom filename 
            will be built based on the data that is plotted
        filter (str):  str to use in df.query to include or exclude certain 
            data from df (default=None).  Note that df.query does not support 
            spaces, parenthesis, or brackets. Spaces should be replaced by '_' 
            and parenthesis/brackets should be dropped from the str.  Example:
            Temperature [C] --> Temperature_C
        grid_major (bool):  toggle major gridlines (default=True)
        grid_major_color (str):  hex color code for major gridline color
            (default from fcp_params)
        grid_major_linestyle (str):  matplotlib str code for linestyle (default
            from fcp_params)
        grid_minor (bool):  toggle minor gridlines (default=False)
        grid_minor_color (str):  hex color code for minor gridline color
            (default from fcp_params)
        grid_minor_linestyle (str):  matplotlib str code for linestyle (default
            from fcp_params)
        label_font_size (int):  font size in pixels for the x and y labels
            (default from fcp_params)
        label_style (str):  define the label style (default from fcp_params).  
            Use standard mpl styles like 'italic'
        label_weight (str):  define the label weight (default from fcp_params).  
            Use standard mpl weights like 'bold'
        leg_bkgrd (str):  hex color code for legend background (default from 
            fcp_params)
        leg_border (str):  hex color code for legend border (default from 
            fcp_params)
        leg_groups (str):  name of df column by which to legend the data 
            (default=None)
        leg_items (str):  explicit definition of the legend items; ignores any 
            values that are not listed (default=None)
        leg_on (bool):  toggle legend visibility (default=True)
        leg_title (str):  title for the legend (default=None)
        line_color (str):  hex color code to override the built-in line color
            cycle (default=None)
        line_fit (None|int):  adds a line fit to the data of polynomial order
            ``line_fit`` (default=None)
        line_style (str):  set the default line style (default="-")
        line_width (int):  set the linewidth of curves (default=1)
        lines (bool):  turn plot lines on|off (default=True)
        marker_size (int):  set marker size (default from fcp_params)
        marker_type (str):  set marker type (default==None)
        points (bool):  turn markers on|off (default=True)
        rc_label_edge_color (str):  hex color code for row/column labels border
            edges (default from fcp_params)
        rc_label_fill_color (str):  hex color code for row/column labels
            background (default from fcp_params)
        rc_label_font_size (int):  font size for row/column labels (default
            from fcp_params)
        rc_label_text_color (str):  hex color code for row/column label text
            (default from fcp_params)
        rc_label_text_style (str):  define the style row/column label text. Use
            standard mpl styles like 'italic'" (default from fcp_params)
        row (str):  name of a column in df to use as a grouping variable for
            facet grid style plotting; each unique value from df[row] will
            represent a row of plots in the final figure (default=None --> no
            column grouping)
        row_label (str):  a custom label to display for each row in the facet
            grid plot (default=None --> use the value of kwargs['row'])
        row_labels_on (bool):  toggle visibility of row grouping labels in
            facet grid (default=True)
        row_label_size (int):  label height in pixel for row labels in pixels
            (default from fcp_params)
        row_label_ws (int):  whitespace in pixels between axis and row labels
            in pixels (default from fcp_params)
        row_padding (int):  whitespace between facet rows in pixels (default
            from fcp_params
        rows (list):  list used to manually define the rows to use in the facet
            grid. These values must actually be in df[row] (default=None)
        save_ext (str):  filename extension for saved figures (default='png')
        save_path (str):  destination file folder for plots (default=None)
        scalar_x (bool):  force scalar tick labels on the x-axis instead of
            powers of ten (default=False)
        scalar_y (bool):  force scalar tick labels on the y-axis instead of
            powers of ten (default=False)
        sci_x (bool):  force scientific notation for tick labels on x-axis
            (default=False)
        sci_y (bool):  force scientific notation for tick labels on y-axis
            (default=False)
        separate_labels (bool):  give each plot its own axes labels
        sharex (bool):  share plot range for x-axis (default=True)
        sharey (bool):  share plot range for y-axis (default=True)
        show (bool):  pop open plot after it is generated.  Otherwise, the plot
            is just saved (default=False)
        stat (str):  statistic to apply to the y-data being plotted (default=
            None)
        stat_val (str):  column name to which the statistic should be applied.
            Options include: 'median', 'median_only', 'mean_only', and 'mean'.
            When 'only' is in the stat value, median lines and median/mean data
            points are plotted.  Without 'only', median/mean lines and all raw
            data points are plotted (default=kwargs['x'])
        tick_major_color (str):  hex color code for major tick marks (default
            from fcp_params)
        tick_minor_color (str):  hex color code for minor tick marks (default
            from fcp_params)
        tick_font_size (int):  font size for tick labels (default from
            fcp_params)
        tick_label_color (str):  hex color code for tick labels (default
            from fcp_params)
        tick_length (int):  length of the tick marks (default from fcp_params)
        tick_width (int):  line width of the tick marks (default from
            fcp_params)
        title (str):  plot title (default=None)
        title_edge_color (str):  hex color code for edge of a box around the
            plot title (default from fcp_params)
        title_fill_color (str):  hex color code for fill of a box around the
            plot title (default from fcp_params)
        title_text_color (str):  hex color code for title color (default from
            fcp_params)
        title_font_size (int):  font size of plot title (default from
            fcp_params)
        title_text_style (str):  define the title style. Use standard mpl
            styles like 'italic' (default from fcp_params)
        twinx (bool):  allow for twinning of x-axis for secondary y-axis
            (default=False)
        twiny (bool):  allow for twinning of y-axis for secondary x-axis
            (not currently supported) (default=False)
        xlabel (str):  label for x-axis (default=kwargs['x'])
        xmax (float):  maximum x-value on x-axis (default=None --> use mpl
            defaults)
        xmin (float):  minimum x-value of x-axis (default=None --> use mpl
            defaults)
        xticks (int):  specify the number of xticks (not currently supported)
            (default=None --> use mpl defaults)
        xtrans (str):  translate the x-axis data.  Options include: 'abs'
            (absolute value), 'neg'/'negative' (negative value),
            'inv'/'inverse' (1/data), or tuple of ('pow', int) (to raise to a
            power) (default = None)
        ylabel (str):  label for primary y-axis (default=kwargs['y'] or
            kwargs['y'][0])
        ymax (float):  maximum y-value on y-axis (default=None --> use mpl
            defaults)
        ymin (float):  minimum y-value of y-axis (default=None --> use mpl
            defaults)
        yticks (int):  specify the number of yticks (not currently supported)
            (default=None --> use mpl defaults)
        ytrans (str):  translate the y-axis data.  Options include: 'abs'
            (absolute value), 'neg'/'negative' (negative value),
            'inv'/'inverse' (1/data), or tuple of ('pow', int) (to raise to a
            power) [won't work with ``twinx``] (default=None)
        ylabel2 (str):  label for secondary y-axis (default=kwargs['y'][1])
        ymax2 (float):  maximum y-value on secondary y-axis (default=None -->
            use mpl defaults)
        ymin2 (float):  minimum y-value on secondary y-axis (default=None -->
            use mpl defaults)
        yticks2 (int):  specify the number of yticks2 (not currently supported)
            (default=None --> use mpl defaults)

    Returns:
        design (FigDesign obj):  contains all the spacing information used to
            construct the figure
    """
    
    # Reload defaults
    fcp_params, palette, markers = reload_defaults()
    
    # Check for pasted kwargs
    if kwargs.get('paste'):
        kwargs = paste_kwargs(kwargs)
    
    # Keyword-argument definition
    kw = {}
    df = kwargs.get('df')
    if df is None:
        raise ValueError('Must provide a DataFrame called "df" for analysis!')

    x = kwargs.get('x')
    if x is None:
        raise ValueError('Must provide a column name for "x"')

    y = kwargs.get('y')
    if y is None:
        raise ValueError('Must provide a column name for "y"')

    kw['ax_edge_color'] = kwargs.get('ax_edge_color', 
                                     fcp_params['ax_edge_color'])
    kw['ax_face_color'] = kwargs.get('ax_face_color', 
                                     fcp_params['ax_face_color'])
    kw['ax_fig_ws'] = kwargs.get('ax_fig_ws', fcp_params['ax_fig_ws'])
    kw['ax_hlines'] = kwargs.get('ax_hlines', [])
    kw['ax_label_pad'] = kwargs.get('ax_label_pad', fcp_params['ax_label_pad'])
    kw['ax_lim'] = kwargs.get('ax_lim', [])
    kw['ax_lim_pad'] = kwargs.get('ax_lim_pad', 0.05)
    kw['ax_scale'] = kwargs.get('ax_scale', None)
    kw['ax_scale2'] = kwargs.get('ax_scale2', None)
    kw['ax_size'] = kwargs.get('ax_size', fcp_params['ax_size'])
    kw['ax_vlines'] = kwargs.get('ax_vlines', [])
    kw['cmap'] = kwargs.get('cmap', None)
    kw['col'] = kwargs.get('col', None)
    kw['col_label'] = kwargs.get('col_label', None)
    kw['col_labels_on'] = kwargs.get('col_labels_on', True)
    kw['col_label_size'] = kwargs.get('col_label_size',
                                      fcp_params['rc_label_size'])
    kw['col_label_ws'] = kwargs.get('col_label_ws', fcp_params['rc_label_ws'])
    kw['col_padding'] = kwargs.get('col_padding', fcp_params['col_padding'])
    kw['colors'] = kwargs.get('colors', palette)
    kw['cols'] = kwargs.get('cols', None)
    kw['fig_ax_ws'] = kwargs.get('fig_ax_ws', 
                                 fcp_params['fig_ax_ws'])
    kw['fig_edge_color'] = kwargs.get('fig_edge_color', 
                                     fcp_params['fig_edge_color'])
    kw['fig_face_color'] = kwargs.get('fig_face_color', 
                                     fcp_params['fig_face_color'])
    kw['fig_groups'] = kwargs.get('fig_groups', None)
    kw['fig_group_path'] = kwargs.get('fig_group_path', False)
    kw['fig_label'] = kwargs.get('fig_label', True)
    kw['filename'] = kwargs.get('filename', None)
    kw['filter'] = kwargs.get('filter', None)
    kw['grid_major_color'] = kwargs.get('grid_major_color', 
                                        fcp_params['grid_major_color'])
    kw['grid_major_linestyle'] = kwargs.get('grid_major_linestyle', 
                                        fcp_params['grid_major_linestyle'])

    kw['grid_minor_color'] = kwargs.get('grid_minor_color', 
                                        fcp_params['grid_minor_color'])
    kw['grid_minor_linestyle'] = kwargs.get('grid_minor_linestyle', 
                                        fcp_params['grid_minor_linestyle'])
    kw['grid_major'] = kwargs.get('grid_major', True)
    kw['grid_minor'] = kwargs.get('grid_minor', False)
    kw['label_font_size'] = kwargs.get('label_font_size', 
                                       fcp_params['label_font_size'])
    kw['label_style'] = kwargs.get('label_style', fcp_params['label_style'])
    kw['label_weight'] = kwargs.get('label_weight', fcp_params['label_weight'])
    kw['leg_bkgrd'] = kwargs.get('leg_bkgrd', fcp_params['leg_bkgrd'])
    kw['leg_border'] = kwargs.get('leg_border', fcp_params['leg_border'])
    kw['leg_groups'] = kwargs.get('leg_groups', None)
    kw['leg_items'] = kwargs.get('leg_items', [])
    kw['leg_on'] = kwargs.get('leg_on', True)
    kw['leg_title'] = kwargs.get('leg_title', None)
    kw['line_color'] = kwargs.get('line_color', None)
    kw['line_fit'] = kwargs.get('line_fit', None)
    kw['line_style'] = kwargs.get('line_style', '-')
    kw['line_width'] = kwargs.get('line_width', fcp_params['line_width'])
    kw['lines'] = kwargs.get('lines', True)
    kw['marker_size'] = kwargs.get('marker_size', fcp_params['marker_size'])
    kw['marker_type'] = kwargs.get('marker_type', None)
    kw['points'] = kwargs.get('points', True)
    kw['rc_label_edge_color'] = kwargs.get('rc_label_edge_color',
                                           fcp_params['rc_label_edge_color'])
    kw['rc_label_fill_color'] = kwargs.get('rc_label_fill_color',
                                           fcp_params['rc_label_fill_color'])
    kw['rc_label_font_size'] = kwargs.get('rc_label_font_size',
                                          fcp_params['rc_label_font_size'])
    kw['rc_label_text_color'] = kwargs.get('rc_label_text_color',
                                           fcp_params['rc_label_text_color'])
    kw['rc_label_text_style'] = kwargs.get('rc_label_text_style',
                                           fcp_params['rc_label_text_style'])
    kw['row'] = kwargs.get('row', None)
    kw['row_label'] = kwargs.get('row_label', None)
    kw['row_labels_on'] = kwargs.get('row_labels_on', True)
    kw['row_label_size'] = kwargs.get('row_label_size',
                                     fcp_params['rc_label_size'])
    kw['row_label_ws'] = kwargs.get('row_label_ws', fcp_params['rc_label_ws'])
    kw['row_padding'] = kwargs.get('row_padding', fcp_params['row_padding'])
    kw['rows'] = kwargs.get('rows', None)
    kw['save_ext'] = kwargs.get('save_ext', 'png')
    kw['save_name'] = kwargs.get('save_name', None)
    kw['save_path'] = kwargs.get('save_path', None)
    kw['scalar_x'] = kwargs.get('scalar_x', False)
    kw['scalar_y'] = kwargs.get('scalar_y', False)
    kw['sci_x'] = kwargs.get('sci_x', False)
    kw['sci_y'] = kwargs.get('sci_y', False)
    kw['separate_labels'] = kwargs.get('separate_labels', False)
    kw['sharex'] = kwargs.get('sharex', True)
    kw['sharey'] = kwargs.get('sharey', True)
    kw['show'] = kwargs.get('show', False)
    kw['stat'] = kwargs.get('stat', None)
    kw['stat_val'] = kwargs.get('stat_val', x)
    kw['tick_major_color'] = kwargs.get('tick_major_color', 
                                        fcp_params['tick_major_color'])
    kw['tick_minor_color'] = kwargs.get('tick_minor_color', 
                                        fcp_params['tick_minor_color'])
    kw['tick_font_size'] = kwargs.get('tick_font_size',
                                      fcp_params['tick_font_size'])
    kw['tick_label_color'] = kwargs.get('tick_label_color',
                                      fcp_params['tick_label_color'])
    kw['tick_length'] = kwargs.get('tick_length', fcp_params['tick_length'])
    kw['tick_width'] = kwargs.get('tick_width', fcp_params['tick_width'])
    kw['title'] = kwargs.get('title', None)
    kw['title_edge_color'] = kwargs.get('title_edge_color',
                                        fcp_params['title_edge_color'])
    kw['title_fill_color'] = kwargs.get('title_fill_color',
                                        fcp_params['title_fill_color'])
    kw['title_text_color'] = kwargs.get('title_text_color',
                                        fcp_params['title_text_color'])
    kw['title_font_size'] = kwargs.get('title_font_size',
                                        fcp_params['title_font_size'])
    kw['title_text_style'] = kwargs.get('title_text_style',
                                        fcp_params['title_text_style'])
    kw['twinx'] = kwargs.get('twinx', False)
    kw['twiny'] = kwargs.get('twiny', False)
    kw['xlabel'] = kwargs.get('xlabel', x)
    kw['xlabel_color'] = kwargs.get('xlabel_color', fcp_params['label_color'])
    kw['xmax'] = kwargs.get('xmax', None)
    kw['xmin'] = kwargs.get('xmin', None)
    kw['xticks'] = kwargs.get('xticks', None)
    kw['xtrans'] = kwargs.get('xtrans', None)
    kw['ylabel'] = kwargs.get('ylabel', y)
    kw['ylabel_color'] = kwargs.get('ylabel_color', fcp_params['label_color'])
    kw['yline'] = kwargs.get('yline', None)
    kw['ymax'] = kwargs.get('ymax', None)
    kw['ymin'] = kwargs.get('ymin', None)
    kw['yticks'] = kwargs.get('yticks', None)
    kw['ytrans'] = kwargs.get('ytrans', None)
    kw['ylabel2'] = kwargs.get('ylabel2', y)
    kw['ylabel2_color'] = kwargs.get('ylabel2_color', 
                                     fcp_params['label_color'])
    kw['ymax2'] = kwargs.get('ymax2', None)
    kw['ymin2'] = kwargs.get('ymin2', None)
    kw['yticks2'] = kwargs.get('yticks2', None)
    kw['ytrans2'] = kwargs.get('ytrans2', None)

    df = df.copy()
    
    # Turn off interactive plotting
    mplp.ioff()
    
    # Convert column types
    try:
        df[x] = df[x].astype(float)
    except:
        raise ValueError('Could not convert x-column to float!')
    try:
        df[y] = df[y].astype(float)
    except:
        raise ValueError('Could not convert y-column to float!')
    # Dummy-proof colors
    if type(kw['colors'][0]) is not tuple:
        kw['colors'] = [kw['colors']]
    else:
        kw['colors'] = list(kw['colors'])
    kw['colors'] += [f for f in palette if f not in kw['colors']]
    
    # Filter the dataframe
    if kw['filter']:
        df = df_filter(df, kw['filter'])
    if len(df) == 0:
        print('No data remains after filter.  Killing plot.')
        return None

    # Handle multiple y-values
    if type(y) is not list:
        y = [y]
    if kw['twinx']:
        kw['row_label_ws'] = fcp_params['fig_ax_ws']
        
    
    # Clear out existing plot buffer
    mplp.close('all')

    # Set up the figure grouping and iterate (each value corresponds to a
    #  separate figure)
    if kw['fig_groups'] is not None:
        if type(kw['fig_groups']) is list:
            kw['fig_items'] = list(df.groupby(kw['fig_groups']).groups.keys())
        else:
            kw['fig_items'] = list(df[kw['fig_groups']].unique())
    else:
        kw['fig_items'] = [None]
    if kw['fig_group_path'] is not None and type(kw['fig_group_path']) is str:
        temp = list(df.groupby([kw['fig_groups'], 
                                kw['fig_group_path']]).groups.keys())
        kw['fig_path_items'] = [f[1] for f in temp]
    else:
        kw['fig_path_items'] = kw['fig_items']
    
    # Eliminate title buffer if no title is provided
    if not kw['title']:
        kw['title_h'] = 0
    
    # Iterate over discrete figures
    for ifig, fig_item in enumerate(kw['fig_items']):
        
        # Make a data subset and filter
        df_fig = df.copy()
        
        if type(fig_item) is tuple:
            for ig, g in enumerate(fig_item):
                df_fig = df_fig[df_fig[kw['fig_groups'][ig]]==g]
        elif kw['fig_groups'] is not None:
            df_fig = df_fig[df_fig[kw['fig_groups']]==fig_item]

        # Set up the row grouping
        if kw['row'] and not kw['rows']:
            rows = natsorted(list(df_fig[kw['row']].unique()))
            nrow = len(rows)
        elif kw['rows']:
            actual = df[kw['row']].unique()
            rows = [f for f in kw['rows'] if f in actual]
            nrow = len(rows)
        else:
            rows = [None]
            kw['row_labels_on'] = False
            kw['row_label_size'] = 0
            nrow = 1
        kw['nrow'] = nrow

        # Set up the column grouping
        if kw['col'] and not kw['cols']:
            cols = natsorted(list(df_fig[kw['col']].unique()))
            ncol = len(cols)
        elif kw['cols']:
            actual = df[kw['col']].unique()
            cols = [f for f in kw['cols'] if f in actual]
            ncol = len(cols)
        else:
            cols = [None]
            kw['col_labels_on'] = False
            kw['col_label_size'] = 0
            ncol = 1
        kw['ncol'] = ncol
        
        # Set up the legend grouping
        if kw['leg_groups'] is not None and len(kw['leg_items']) == 0:
            if kw['leg_groups'] not in df_fig.columns:
                print('\nError!  "%s" not in DataFrame.  '
                      'Check reindex value' % kw['leg_groups'])
            df_fig[kw['leg_groups']] = df_fig[kw['leg_groups']].astype(str)
            kw['leg_items'] = natsorted(df_fig[kw['leg_groups']].unique())
            if len(y) > 1: # and not kw['twinx']:
                temp = list(itertools.product(kw['leg_items'], y))
                kw['leg_items'] = ['%s: %s' % (f[0], f[1]) for f in temp]
        elif not kw['leg_groups'] and len(y) > 1:
            kw['leg_items'] = y
        elif not kw['leg_groups']:
            kw['leg_items'] = []
        if not kw['leg_title']:
            kw['leg_title'] = kw['leg_groups']
        kw['leg_items'] = natsorted(kw['leg_items'])

        # Add padding if sharex|sharey
        if not kw['sharex'] or not kw['sharey']:
            if 'row_padding' not in kwargs.keys():
                kw['row_padding'] += kw['tick_font_size']
            if 'col_padding' not in kwargs.keys():
                kw['col_padding'] += kw['tick_font_size']
        if kw['separate_labels']:
            kw['col_padding'] = kw['fig_ax_ws']
            kw['row_padding'] = kw['ax_fig_ws']

        # Account for scalar formatted axes
        if kw['scalar_y']:
            max_y = df[y].values.max()
            max_y = int(10**(np.ceil(np.log10(df[y].values.max()))-3))
            kw['fig_ax_ws'] += 10*len(str(max_y))
            
        # Format the figure dimensions
        design = FigDesign(**kw)

        # Make the figure and axes
        if ncol == 0:
            raise ValueError('Cannot make subplot. Number of columns is 0')
        if nrow == 0:
            raise ValueError('Cannot make subplot. Number of rows is 0')
        fig, axes = mplp.subplots(nrow, ncol,
                                  figsize=[design.fig_w, design.fig_h],
                                  sharex=kw['sharex'],
                                  sharey=kw['sharey'],
                                  dpi=design.dpi,
                                  facecolor=kw['fig_face_color'],
                                  edgecolor=kw['fig_edge_color'])

        # Reformat the axes variable if it is only one plot
        if not type(axes) is np.ndarray:
            axes = np.array([axes])
        if len(axes.shape) == 1:
            if nrow == 1:
                axes = np.reshape(axes, (1, -1))
            else:
                axes = np.reshape(axes, (-1, 1))

        # Format the subplot spacing
        fig.subplots_adjust(
            left=design.left,
            right=design.right,
            bottom=design.bottom,
            top=design.top,
            hspace=1.0*design.row_padding/design.ax_h,
            wspace=1.0*design.col_padding/design.ax_w
        )

        # Handle colormaps
        if kw['cmap']=='jmp_spectral':
            cmap = jmp_spectral
        elif kw['cmap'] is not None:
            cmap = mplp.get_cmap(kw['cmap'])

        # Make the plots by row and by column
        curves = []

        for ir, r in enumerate(rows):
            for ic, c in enumerate(cols):

                # Twinning
                if kw['twinx']:
                    ax2 = axes[ir, ic].twinx()
                else:
                    ax2 = None
                # Set colors
                axes[ir, ic].set_axis_bgcolor(kw['ax_face_color'])
                axes[ir, ic].spines['bottom'].set_color(kw['ax_edge_color'])
                axes[ir, ic].spines['top'].set_color(kw['ax_edge_color'])
                axes[ir, ic].spines['right'].set_color(kw['ax_edge_color'])
                axes[ir, ic].spines['left'].set_color(kw['ax_edge_color'])

                if ax2 is not None:
                    ax2.set_axis_bgcolor(kw['ax_face_color'])
                    ax2.spines['bottom'].set_color(kw['ax_edge_color'])
                    ax2.spines['top'].set_color(kw['ax_edge_color'])
                    ax2.spines['right'].set_color(kw['ax_edge_color'])
                    ax2.spines['left'].set_color(kw['ax_edge_color'])

                # Style major gridlines
                if kw['grid_major']:
                    axes[ir, ic].grid(b=True, which='major', zorder=3,
                                      color=kw['grid_major_color'],
                                      linestyle=kw['grid_major_linestyle'])

                # Toggle minor gridlines
                kw['grid_minor'] = str(kw['grid_minor'])
                axes[ir, ic].minorticks_on()
                if ax2 is not None:
                    ax2.minorticks_on()
                if kw['grid_minor'] == 'True' or \
                    kw['grid_minor'].lower() == 'both':
                    axes[ir, ic].grid(b=True,
                                      color=kw['grid_minor_color'],
                                      which='minor', zorder=0,
                                      linestyle=kw['grid_minor_linestyle'])
                elif kw['grid_minor'].lower() == 'y':
                    axes[ir, ic].yaxis.grid(b=True,
                                        color=kw['grid_minor_color'],
                                        which='minor',
                                        linestyle=kw['grid_minor_linestyle'])
                elif kw['grid_minor'].lower() == 'x':
                    axes[ir, ic].xaxis.grid(b=True,
                                        color=kw['grid_minor_color'],
                                        which='minor',
                                        linestyle=kw['grid_minor_linestyle'])
                if ax2 is not None:
                    ax2.grid(False, which='both')

                # Build the row/col filename labels
                if kw['row_label']:
                    fnrow = filename_label(kw['row_label'])
                elif kw['row']:
                    fnrow = filename_label(kw['row'])
                if kw['col_label']:
                    fncol = filename_label(kw['col_label'])
                elif kw['col']:
                    fncol = filename_label(kw['col'])

                # Subset the data
                if r is not None and c is not None:
                    df_sub = df_fig[(df_fig[kw['row']]==r)&\
                                    (df_fig[kw['col']]==c)].copy()
                    rc_name = ' by %s by %s' % (fnrow, fncol)
                elif r and not c:
                    df_sub = df_fig[(df_fig[kw['row']]==r)].copy()
                    rc_name = ' by %s' % (fnrow)
                elif c and not r:
                    df_sub = df_fig[(df_fig[kw['col']]==c)].copy()
                    rc_name = ' by %s' % (fncol)
                else:
                    df_sub = df_fig.copy()
                    rc_name = ''

                # Set the axes scale
                if kw['ax_scale'] == 'loglog':
                    plotter = axes[ir, ic].loglog
                elif kw['ax_scale'] == 'semilogx' or kw['ax_scale'] == 'logx':
                    plotter = axes[ir, ic].semilogx
                elif kw['ax_scale'] == 'semilogy' or kw['ax_scale'] == 'logy':
                    plotter = axes[ir, ic].semilogy
                else:
                    plotter = axes[ir, ic].plot

                # Apply any data transformations
                if kw['xtrans'] == 'abs':
                    df_sub.loc[:, x] = abs(df_sub[x])
                elif kw['xtrans'] == 'negative' or kw['xtrans'] == 'neg':
                    df_sub.loc[:, x] = -df_sub[x]
                elif kw['xtrans'] == 'inverse' or kw['xtrans'] == 'inv':
                    df_sub.loc[:, x] = 1/df_sub[x]
                elif type(kw['xtrans']) is tuple and kw['xtrans'][0] == 'pow':
                    df_sub.loc[:, x] = df_sub[x]**kw['xtrans'][1]
                ### these will fail if multiple y provided...need handling
                if kw['ytrans'] == 'abs':
                    df_sub.loc[:, y] = abs(df_sub[y])
                elif kw['ytrans'] == 'negative' or kw['ytrans'] == 'neg':
                    df_sub.loc[:, y] = -df_sub[y]
                elif kw['ytrans'] == 'inverse' or kw['ytrans'] == 'inv':
                    df_sub.loc[:, y] = 1/df_sub[y]
                elif type(kw['ytrans']) is tuple and kw['ytrans'][0] == 'pow':
                    df_sub.loc[:, y] = df_sub[y]**kw['ytrans'][1]

                # Add horizontal and vertical lines
                for h in kw['ax_hlines']:
                    if type(h) is tuple and len(h)==3:
                        axes[ir,ic].axhline(h[0], color=h[1], linestyle=h[2])
                    else:
                        axes[ir,ic].axhline(h, color='k', linewidth=0.5)

                for v in kw['ax_vlines']:
                    if type(v) is tuple and len(v)==3:
                        axes[ir,ic].axvline(v[0], color=v[1], linestyle=v[2])
                    else:
                        axes[ir,ic].axvline(v, color='k', linewidth=0.5)
                
                # Legend grouping
                if kw['leg_groups'] is None and not kw['twinx']:
                    for iy, yy in enumerate(natsorted(y)):
                        if len(df[x].dropna()) == 0 or \
                                len(df[yy].dropna()) == 0:
                            continue
                        if len(df_sub[x].dropna()) == 0 or \
                                len(df_sub[yy].dropna()) == 0:
                            continue
                            
                        # Define color and marker types
                        color = \
                            kw['line_color'] if kw['line_color'] is not None \
                                             else kw['colors'][iy]
                        marker = \
                            kw['marker_type'] if kw['marker_type'] is not None\
                                              else markers[iy]
                        # Plot
                        if kw['stat'] is None:
                            curves += add_curves(plotter,
                                                df_sub[x],
                                                df_sub[yy],
                                                color,
                                                marker,
                                                kw['points'],
                                                kw['lines'],
                                                markersize=kw['marker_size'],
                                                linestyle=kw['line_style'],
                                                linewidth=kw['line_width'])
                        
                        else:
                            if 'median' in kw['stat'].lower():
                                df_stat = \
                                    df_sub.groupby(kw['stat_val']).median()
                            else:
                                df_stat = df_sub.groupby(kw['stat_val']).mean()
                            
                            if 'only' not in kw['stat'].lower():
                                # Plot the points for each data set
                                curves += add_curves(
                                             plotter,
                                             df_sub[x],
                                             df_sub[yy],
                                             color,
                                             marker,
                                             True,
                                             False,
                                             markersize=kw['marker_size'],
                                             linestyle='none',
                                             linewidth=0)
                            # Plot the lines
                            if 'only' in kw['stat'].lower():
                                curves += add_curves(
                                    plotter,
                                    df_stat.reset_index()[x],
                                    df_stat[yy],
                                    color,
                                    marker,
                                    True,
                                    True,
                                    markersize=kw['marker_size'],
                                    linestyle=kw['line_style'],
                                    linewidth=kw['line_width'])
                            else:
                                add_curves(
                                    plotter,
                                    df_stat.reset_index()[x],
                                    df_stat[yy],
                                    color,
                                    marker,
                                    False,
                                    True,
                                    markersize=kw['marker_size'],
                                    linestyle=kw['line_style'],
                                    linewidth=kw['line_width'])
                        
                        if kw['line_fit'] is not None and kw['line_fit'] != False:
                            # Fit the polynomial
                            coeffs = np.polyfit(np.array(df_sub[x]), 
                                                np.array(df_sub[yy]), 
                                                kw['line_fit'])
                            
                            # Calculate the fit line
                            xval = df_sub[x]
                            yval = np.polyval(coeffs, xval)
                            
                            # Find r^2
                            ybar = df_sub[yy].sum()/len(df_sub[yy])
                            ssreg = np.sum((yval-ybar)**2)
                            sstot = np.sum((df_sub[y]-ybar)**2)
                            r_sq = ssreg/sstot
                            
                            # Add fit line
                            xval = np.linspace(0.9*xval.min(),
                                               1.1*xval.max(), 10)
                            yval = np.polyval(coeffs, xval)
                            add_curves(plotter,
                                       xval,
                                       yval,
                                       'k',
                                       marker,
                                       False,
                                       True,
                                       linestyle='--')
                            
                            # Add fit equation (need to update for more than
                            # 1D and formatting)
                            if coeffs[1] < 0:
                                sign = '-'
                            else:
                                sign = '+'
                            axes[ir,ic].text(
                                0.05, 0.9,
                                'y=%.4f * x %s %.4f\nR^2=%.5f' %
                                (coeffs[0], sign, abs(coeffs[1]), r_sq),
                                transform=axes[ir,ic].transAxes)
                            
                    if kw['yline'] is not None:
                        if ir==0 and ic==0:
                            kw['leg_items'] += [kw['yline']]
                            curves += add_curves(plotter,
                                           df[x],
                                            df[kw['yline']],
                                           'k',
                                           None,
                                           False,
                                           True,
                                           linestyle='-')
                        else:
                            add_curves(plotter,
                                       df[x],
                                        df[kw['yline']],
                                       'k',
                                       None,
                                       False,
                                       True,
                                       linestyle='-')
                elif kw['leg_groups'] is None and kw['twinx']:

                    # Define color and marker types
                    color = \
                        kw['line_color'] if kw['line_color'] is not None \
                                         else kw['colors'][0:2]
                    marker = \
                        kw['marker_type'] if kw['marker_type'] is not None\
                                          else markers[0:2]
                    # Set the axes scale
                    if kw['ax_scale2'] == 'semilogy' or \
                       kw['ax_scale2'] == 'logy':
                        plotter2 = ax2.semilogy
                    else:
                        plotter2 = ax2.plot
                        
                    if kw['stat'] is None:
                        curves += add_curves(plotter,
                                             df_sub[x],
                                             df_sub[y[0]],
                                             color[0],
                                             marker[0],
                                             True,
                                             markersize=kw['marker_size'],
                                             linestyle=kw['line_style'],
                                             linewidth=kw['line_width'])
                        curves += add_curves(plotter2,
                                             df_sub[x],
                                             df_sub[y[1]],
                                             color[1],
                                             marker[1],
                                             True,
                                             markersize=kw['marker_size'],
                                             linestyle=kw['line_style'],
                                             linewidth=kw['line_width'])
                    else:
                        if 'median' in kw['stat'].lower():
                            df_stat = df_sub.groupby(kw['stat_val']).median()
                        else:
                            df_stat = df_sub.groupby(kw['stat_val']).mean()
                        
                        # Plot the points for each data set
                        if 'only' not in kw['stat'].lower():
                            curves += add_curves(plotter,
                                                 df_sub[x],
                                                 df_sub[y[0]],
                                                 color[0],
                                                 marker[0],
                                                 True,
                                                 False,
                                                 markersize=kw['marker_size'],
                                                 linestyle='none',
                                                 linewidth=0)
                            curves += add_curves(plotter2,
                                                 df_sub[x],
                                                 df_sub[y[1]],
                                                 color[1],
                                                 marker[1],
                                                 True,
                                                 False,
                                                 markersize=kw['marker_size'],
                                                 linestyle='none',
                                                 linewidth=0)
                        # Plot the lines
                        if 'only' in kw['stat'].lower():
                            curves += add_curves(plotter,
                                                 df_stat.reset_index()[x],
                                                 df_stat[y[0]],
                                                 color[0],
                                                 marker[0],
                                                 True,
                                                 True,
                                                 markersize=kw['marker_size'],
                                                 linestyle=kw['line_style'],
                                                 linewidth=kw['line_width'])
                            curves += add_curves(plotter,
                                                 df_stat.reset_index()[x],
                                                 df_stat[y[1]],
                                                 color[1],
                                                 marker[1],
                                                 True,
                                                 True,
                                                 markersize=kw['marker_size'],
                                                 linestyle=kw['line_style'],
                                                 linewidth=kw['line_width'])
                        else:
                            add_curves(plotter,
                                       df_stat.reset_index()[x],
                                       df_stat[y[0]],
                                       color[0],
                                       marker[0],
                                       False,
                                       True,
                                       markersize=kw['marker_size'],
                                       linestyle=kw['line_style'],
                                       linewidth=kw['line_width'])
                            add_curves(plotter2,
                                       df_stat.reset_index()[x],
                                       df_stat[y[1]],
                                       color[1],
                                       marker[1],
                                       False,
                                       True,
                                       markersize=kw['marker_size'],
                                       linestyle=kw['line_style'],
                                       linewidth=kw['line_width'])

                elif kw['leg_groups'] and kw['twinx']:
                    # NEED TO ADJUST FOR LEG GROUPS FROM BELOW
                    # Define color and marker types
                    color = \
                        kw['line_color'] if kw['line_color'] is not None \
                                         else kw['colors'][0:2]
                    marker = \
                        kw['marker_type'] if kw['marker_type'] is not None\
                                          else markers[0:2]
                    # Set the axes scale
                    if kw['ax_scale2'] == 'semilogy' or \
                       kw['ax_scale2'] == 'logy':
                        plotter2 = ax2.semilogy
                    else:
                        plotter2 = ax2.plot

                    for ileg, leg_group in enumerate(kw['leg_items'][::2]):
                        group = leg_group.split(': ')[0]
                        subset = df_sub[kw['leg_groups']]==group
                        if kw['stat'] is None:
                            curves += add_curves(plotter,
                                                 df_sub[x][subset],
                                                 df_sub[y[0]][subset],
                                                 kw['colors'][2*ileg],
                                                 markers[2*ileg],
                                                 True,
                                                 markersize=kw['marker_size'],
                                                 linestyle=kw['line_style'],
                                                 linewidth=kw['line_width'])
                            curves += add_curves(plotter2,
                                                 df_sub[x][subset],
                                                 df_sub[y[1]][subset],
                                                 kw['colors'][2*ileg+1],
                                                 markers[2*ileg+1],
                                                 True,
                                                 markersize=kw['marker_size'],
                                                 linestyle=kw['line_style'],
                                                 linewidth=kw['line_width'])
                        else:
                            if 'median' in kw['stat'].lower():
                                df_stat = \
                                    df_sub.groupby(kw['stat_val']).median()
                            else:
                                df_stat = df_sub.groupby(kw['stat_val']).mean()

                            # Plot the points for each data set
                            if 'only' not in kw['stat'].lower():
                                curves += add_curves(
                                                 plotter,
                                                 df_sub[x][subset],
                                                 df_sub[y[0]][subset],
                                                 kw['colors'][2*ileg],
                                                 markers[2*ileg],
                                                 True,
                                                 False,
                                                 markersize=kw['marker_size'],
                                                 linestyle='none',
                                                 linewidth=0)
                                curves += add_curves(
                                                 plotter2,
                                                 df_sub[x][subset],
                                                 df_sub[y[1]][subset],
                                                 kw['colors'][2*ileg+1],
                                                 markers[2*ileg+1],
                                                 True,
                                                 False,
                                                 markersize=kw['marker_size'],
                                                 linestyle='none',
                                                 linewidth=0)
                            # Plot the lines
                            if 'only' in kw['stat'].lower():
                                curves += add_curves(
                                             plotter,
                                             df_stat.reset_index()[x][subset],
                                             df_stat[y[0]][subset],
                                             kw['colors'][2*ileg],
                                             markers[2*ileg],
                                             True,
                                             True,
                                             markersize=kw['marker_size'],
                                             linestyle=kw['line_style'],
                                             linewidth=kw['line_width'])
                                curves += add_curves(
                                             plotter,
                                             df_stat.reset_index()[x][subset],
                                             df_stat[y[1]][subset],
                                             kw['colors'][2*ileg+1],
                                             markers[2*ileg+1],
                                             True,
                                             True,
                                             markersize=kw['marker_size'],
                                             linestyle=kw['line_style'],
                                             linewidth=kw['line_width'])
                            else:
                                add_curves(plotter,
                                           df_stat.reset_index()[x][subset],
                                           df_stat[y[0]][subset],
                                           kw['colors'][2*ileg],
                                           markers[2*ileg],
                                           False,
                                           True,
                                           markersize=kw['marker_size'],
                                           linestyle=kw['line_style'],
                                           linewidth=kw['line_width'])
                                add_curves(plotter2,
                                           df_stat.reset_index()[x][subset],
                                           df_stat[y[1]][subset],
                                           kw['colors'][2*ileg+1],
                                           markers[2*ileg+1],
                                           False,
                                           True,
                                           markersize=kw['marker_size'],
                                           linestyle=kw['line_style'],
                                           linewidth=kw['line_width'])

                else:
                    for ileg, leg_group in enumerate(kw['leg_items']):

                        # Define color and marker types
                        if kw['cmap']:
                            color = cmap((ileg+1)/(len(kw['leg_items'])+1))
                        else:
                            color = kw['line_color'] \
                                if kw['line_color'] is not None \
                                else kw['colors'][ileg]
                        marker = kw['marker_type'][ileg] \
                                 if kw['marker_type'] is not None \
                                 else markers[ileg]

                        # Subset the data by legend group and plot
                        group = leg_group.split(': ')[0]
                        if len(y) > 1 and not kw['twinx']:
                            yy = leg_group.split(': ')[1]
                        else:
                            yy = y[0]
                        subset = df_sub[kw['leg_groups']]==group
                        if kw['stat'] is None:
                            curves += add_curves(plotter,
                                                 df_sub[x][subset],
                                                 df_sub[yy][subset],
                                                 color,
                                                 marker,
                                                 kw['points'],
                                                 markersize=kw['marker_size'],
                                                 linestyle=kw['line_style'],
                                                 linewidth=kw['line_width'])
                        else:
                            # Plot the points
                            if 'only' not in kw['stat'].lower():
                                curves += add_curves(
                                    plotter,
                                    df_sub[x][subset],
                                    df_sub[yy][subset],
                                    color,
                                    marker,
                                    True,
                                    False,
                                    markersize=kw['marker_size'],
                                    linestyle='none',
                                    linewidth=0)
                            
                            # Plot the lines
                            if 'median' in kw['stat'].lower():
                                df_stat = \
                                    df_sub[subset].groupby(kw['stat_val'])\
                                        .median().reset_index()
                            elif kw['stat'] is not None:
                                df_stat = \
                                    df_sub[subset].groupby(kw['stat_val'])\
                                        .mean().reset_index()
                            
                            if 'only' in kw['stat'].lower():
                                curves += add_curves(
                                    plotter,
                                    df_stat[x],
                                    df_stat[yy],
                                    color,
                                    marker,
                                    True,
                                    True,
                                    markersize=kw['marker_size'],
                                    linestyle=kw['line_style'],
                                    linewidth=kw['line_width'])
                            else:                         
                                add_curves(
                                    plotter,
                                    df_stat.reset_index()[x],
                                    df_stat[yy],
                                    color,
                                    marker,
                                    False,
                                    True,
                                    markersize=kw['marker_size'],
                                    linestyle=kw['line_style'],
                                    linewidth=kw['line_width'])

                # Adjust the tick marks
                axes[ir, ic].tick_params(axis='both', which='major',
                                         pad=kw['ax_label_pad'],
                                         labelsize=kw['tick_font_size'],
                                         colors=kw['tick_label_color'],
                                         )
                if kw['separate_labels']:
                    mplp.setp(axes[ir, ic].get_xticklabels(), visible=True)
                    mplp.setp(axes[ir, ic].get_yticklabels(), visible=True)

                for line in axes[ir, ic].xaxis.get_ticklines()[2:-2]:
                    line.set_color(kw['tick_major_color'])
                    line.set_markersize(kw['tick_length'])
                    line.set_markeredgewidth(kw['tick_width'])
                for line in axes[ir, ic].xaxis.get_minorticklines():
                    line.set_color(kw['tick_minor_color'])
                    line.set_markersize(kw['tick_length']*0.8)
                    line.set_markeredgewidth(kw['tick_width'])
                for line in axes[ir, ic].yaxis.get_ticklines()[2:-2]:
                    line.set_color(kw['tick_major_color'])
                    line.set_markersize(kw['tick_length'])
                    line.set_markeredgewidth(kw['tick_width'])
                for line in axes[ir, ic].yaxis.get_minorticklines():
                    line.set_color(kw['tick_minor_color'])
                    line.set_markersize(kw['tick_length']*0.8)
                    line.set_markeredgewidth(kw['tick_width'])
                if ax2 is not None:
                    for line in ax2.yaxis.get_ticklines()[2:-2]:
                        line.set_color(kw['tick_major_color'])
                        line.set_markersize(kw['tick_length'])
                        line.set_markeredgewidth(kw['tick_width'])
                    for line in ax2.yaxis.get_minorticklines():
                        line.set_color(kw['tick_minor_color'])
                        line.set_markersize(kw['tick_length']*0.8)
                        line.set_markeredgewidth(kw['tick_width'])

                # Handle tick formatting
                if kw['scalar_x']:
                    axes[ir, ic].xaxis\
                                .set_major_formatter(ticker.ScalarFormatter())
                    axes[ir, ic].get_xaxis().get_major_formatter()\
                                .set_scientific(False)
                if kw['scalar_y']:
                    axes[ir, ic].yaxis\
                                .set_major_formatter(ticker.ScalarFormatter())
                    axes[ir, ic].get_yaxis().get_major_formatter()\
                                .set_scientific(False)
                #if kw['xticks'] is not None:
                    #myLocator = ticker.MultipleLocator(kw['xticks'])
                    #axes[ir, ic].xaxis.set_major_locator(myLocator)
                #mplp.locator_params(axis='x',nbins=kw['xticks'])
                #fsf = ticker.FormatStrFormatter
                #axes[ir, ic].xaxis.set_major_formatter(fsf('%.2e'))

                # Axis ranges
                if kw['sharex']:
                    dfx = df_fig
                else:
                    dfx = df_sub
                if kw['sharey']:
                    dfy = df_fig
                else:
                    dfy = df_sub
                if kw['stat'] is not None and 'only' in kw['stat']:
                    groups = get_unique_groups(kw)
                    if 'median' in kw['stat']:
                        dfx = dfx.groupby(groups).median().reset_index()
                        dfy = dfy.groupby(groups).median().reset_index()
                    else:
                        dfx = dfx.groupby(groups).mean().reset_index()
                        dfy = dfy.groupby(groups).mean().reset_index()
                dfx = dfx[x]
                dfy = dfy[y]

                xmin = dfx.min()
                xmax = dfx.max()
                xdelta = xmax-xmin

                if kw['xmin'] is not None:
                    axes[ir, ic].set_xlim(left=kw['xmin'])
                else:
                    if kw['ax_scale'] in ['logx', 'loglog', 'semilogx']:
                        xmin = np.log10(xmin) - kw['ax_lim_pad']*\
                               np.log10(xdelta)/(1-2*kw['ax_lim_pad'])
                        xmin = 10**xmin
                    else:
                        xmin -= kw['ax_lim_pad']*xdelta/(1-2*kw['ax_lim_pad'])
                    axes[ir, ic].set_xlim(left=xmin)
                if kw['xmax'] is not None:
                    if kw['fig_groups'] is not None and \
                       type(kw['xmax']) is list:
                        xmax = kw['xmax'][ifig]
                    else:
                        xmax = kw['xmax']
                    axes[ir, ic].set_xlim(right=xmax)
                else:
                    if kw['ax_scale'] in ['logx', 'loglog', 'semilogx']:
                        xmax = np.log10(xmax) + kw['ax_lim_pad']*\
                               np.log10(xdelta)/(1-2*kw['ax_lim_pad'])
                        xmax = 10**xmax
                    else:
                        xmax += kw['ax_lim_pad']*xdelta/(1-2*kw['ax_lim_pad'])
                    axes[ir, ic].set_xlim(right=xmax)

                ymin = dfy.min().min()
                ymax = dfy.max().max()
                ydelta = ymax-ymin

                if kw['ymin'] is not None:
                    axes[ir, ic].set_ylim(bottom=kw['ymin'])
                # else:
                    # if kw['ax_scale'] in ['logy', 'loglog', 'semilogy']:
                        # ymin = np.log10(ymin) - \
                               # kw['ax_lim_pad']*np.log10(ydelta)/(1-2*kw['ax_lim_pad'])
                        # ymin = 10**ymin
                    # else:
                        # ymin = ymin -kw['ax_lim_pad']*ydelta/(1-2*kw['ax_lim_pad'])
                    # axes[ir, ic].set_ylim(bottom=ymin)
                if kw['ymax'] is not None:
                    axes[ir, ic].set_ylim(top=kw['ymax'])
                # else:
                    # if kw['ax_scale'] in ['logy', 'loglog', 'semilogy']:
                        # ymax = np.log10(ymax) + \
                               # kw['ax_lim_pad']*np.log10(ydelta)/(1-2*kw['ax_lim_pad'])
                        # ymax = 10**ymax
                    # else:
                        # ymax = ymax + kw['ax_lim_pad']*ydelta/(1-2*kw['ax_lim_pad'])
                    # axes[ir, ic].set_ylim(top=ymax)


                # Add labels
                if not kw['separate_labels']:
                    if kw['xlabel'] is not None and ir == len(rows)-1:
                        axes[ir, ic].set_xlabel(r'%s' % kw['xlabel'],
                                                fontsize=kw['label_font_size'],
                                                weight=kw['label_weight'],
                                                style=kw['label_style'],
                                                color=kw['xlabel_color'])
                    if kw['ylabel'] is not None and ic == 0:
                        axes[ir, ic].set_ylabel(r'%s' % kw['ylabel'],
                                                fontsize=kw['label_font_size'],
                                                weight=kw['label_weight'],
                                                style=kw['label_style'],
                                                color=kw['ylabel_color'])
                        axes[ir, ic].get_yaxis().get_offset_text().set_x(-0.12)
                    if kw['ylabel2'] is not None and \
                       ic == len(cols)-1 and kw['twinx']:
                        ax2.set_ylabel(r'%s' % kw['ylabel2'],
                                       rotation=270,
                                       labelpad=kw['label_font_size'],
                                       fontsize=kw['label_font_size'],
                                       weight=kw['label_weight'],
                                       style=kw['label_style'],
                                       color=kw['ylabel2_color'])
                else:
                    if kw['xlabel'] is not None:
                        axes[ir, ic].set_xlabel(r'%s' % kw['xlabel'],
                                                fontsize=kw['label_font_size'],
                                                weight=kw['label_weight'],
                                                style=kw['label_style'],
                                                color=kw['xlabel_color'])
                    if kw['ylabel'] is not None:
                        axes[ir, ic].set_ylabel(r'%s' % kw['ylabel'],
                                                fontsize=kw['label_font_size'],
                                                weight=kw['label_weight'],
                                                style=kw['label_style'],
                                                color=kw['ylabel_color'])
                        axes[ir, ic].get_yaxis().get_offset_text().set_x(-0.12)
                    if kw['ylabel2'] is not None and kw['twinx']:
                        ax2.set_ylabel(r'%s' % kw['ylabel2'],
                                       rotation=270,
                                       labelpad=kw['label_font_size'],
                                       fontsize=kw['label_font_size'],
                                       weight=kw['label_weight'],
                                       style=kw['label_style'],
                                       color=kw['ylabel2_color'])

                # Add row/column labels
                if ic == len(cols)-1 and kw['row_labels_on']:
                    if not kw['row_label']:
                        kw['row_label'] = kw['row']
                    add_label('%s=%s' % (kw['row_label'], r),
                              (design.row_label_left, 0,
                               design.row_label_width, 1),
                              axes[ir, ic], 270,
                              edgecolor=kw['rc_label_edge_color'],
                              fillcolor=kw['rc_label_fill_color'],
                              color=kw['rc_label_text_color'],
                              fontsize=kw['rc_label_font_size'],
                              weight=kw['rc_label_text_style'])

                if ir == 0 and kw['col_labels_on']:
                    if not kw['col_label']:
                        kw['col_label'] = kw['col']
                    add_label('%s=%s' % (kw['col_label'], c),
                              (0, design.col_label_bottom,
                               1, design.col_label_height),
                              axes[ir, ic], 0,
                              edgecolor=kw['rc_label_edge_color'],
                              fillcolor=kw['rc_label_fill_color'],
                              color=kw['rc_label_text_color'],
                              fontsize=kw['rc_label_font_size'],
                              weight=kw['rc_label_text_style'])

        # Add the legend (wrong indent??)
        if kw['leg_items'] is not None and len(kw['leg_items'])>0 \
            and kw['leg_on']:
            leg = fig.legend(curves,
                             kw['leg_items'],
                             loc='upper right',
                             title=kw['leg_title'],
                             bbox_to_anchor=(design.leg_right,
                                             design.leg_top),
                             numpoints=1,
                             prop={'size':12})
            leg.get_frame().set_facecolor(kw['leg_bkgrd'])
            leg.get_frame().set_edgecolor(kw['leg_border'])

        # Add a figure title
        if kw['title'] is not None:
            title_bkup = '%s' % kw['title']
            if '@' in kw['title']:
                r = re.search(r'\@(.*)\@', kw['title'])
                val = r.group(1)
                pos = r.span()
                if val in df_fig.columns:
                    val = '%s' % df_fig[val].iloc[0]
                else:
                    val = ''
                kw['title'] = \
                    kw['title'][0:pos[0]] + val + kw['title'][pos[1]:]
            add_label('%s' % kw['title'],
                      (design.title_left, design.title_bottom,
                       design.title_w, design.title_h),
                      axes[0, 0], 0,
                      edgecolor=kw['title_edge_color'],
                      fillcolor=kw['title_fill_color'],
                      color=kw['title_text_color'],
                      fontsize=kw['title_font_size'],
                      weight=kw['title_text_style']
                      )
        
        if kw['fig_label']:
            if kw['twinx']:
                twinx = ' and %s' % filename_label(y[1])
            else:
                twinx = ''
            if kw['fig_groups'] is not None and not kw['fig_group_path']:
                figlabel = ' where ' + kw['fig_groups'] + '=' + \
                            str(kw['fig_path_items'][ifig]) + ' '
            else:
                figlabel = ''
            if not kw['filename']:
                filename = filename_label(y[0]) + twinx + ' vs ' + \
                    filename_label(x) + rc_name + figlabel.rstrip(' ') + \
                    '.' + kw['save_ext']
            else:
                filename = kw['filename'] + figlabel.rstrip(' ') + \
                           '.' + kw['save_ext']
        else:
            filename = kw['filename'] + '.' + kw['save_ext']
        
        if kw['save_path'] and kw['fig_group_path'] and kw['fig_groups']:
            filename = os.path.join(kw['save_path'], 
                       str(kw['fig_path_items'][ifig]), filename)
        elif kw['save_path']:
            filename = os.path.join(kw['save_path'], filename)
        
        # Remove multiplication and divide signs
        try:
            fig.savefig(filename)
            
            if kw['show']:
                os.startfile(filename)
        
        except:
            print(filename)
            raise NameError('%s is not a valid filename!' % filename)
        
        # Reset values for next loop
        if kw['title'] is not None:
            kw['title'] = title_bkup
        kw['leg_items'] = []
        
        
    return design


def reload_defaults():
    """
    Reload the fcp params
    """
    
    #del fcp_params
    import defaults
    importlib.reload(defaults)
    fcp_params = defaults.fcp_params
    palette = defaults.palette
    markers = defaults.markers
    
    return fcp_params, palette, markers
