import pandas as pd
import numpy as np
import itertools
import datetime
import fivecentplots.utilities as utl

try:
    from natsort import natsorted
except:
    natsorted = sorted

import pdb
st = pdb.set_trace

REQUIRED_VALS = {'xy': ['x', 'y'],
                 'boxplot': ['y'],
                 'contour': ['x', 'y', 'z']}
# utl.kwget = utilities.utl.kwget
# reload_defaults = utilities.reload_defaults
# validate_list = utilities.validate_list


class AxisError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class GroupingError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class Data:
    def __init__(self, plot_type='xy', **kwargs):

        #from fivecentplots.fcp import utl.kwget, reload_defaults

        # Reload default file
        self.fcpp, dummy, dummy2 = utl.reload_defaults()

        # Set the plot type
        self.plot_type = plot_type

        # Default axis attributes
        self.dependent = None
        self.independent = None
        self.ax_scale = kwargs.get('ax_scale', None)
        self.ax_limit_padding = utl.kwget(kwargs, self.fcpp,
                                          'ax_limit_padding', 0.05)
        self.legend = None
        self.legend_vals = None
        self.ranges = None
        self.share_col = utl.kwget(kwargs, self.fcpp, 'share_col', False)
        self.share_row = utl.kwget(kwargs, self.fcpp, 'share_row', False)
        self.share_x = utl.kwget(kwargs, self.fcpp, 'share_x', True)
        self.share_x2 = utl.kwget(kwargs, self.fcpp, 'share_x2', True)
        self.share_y = utl.kwget(kwargs, self.fcpp, 'share_y', True)
        self.share_y2 = utl.kwget(kwargs, self.fcpp, 'share_y2', True)
        self.share_z = utl.kwget(kwargs, self.fcpp, 'share_z', True)
        if self.share_row or self.share_col:
            self.share_x = False
            self.share_y = False
        if kwargs.get('wrap', None) is not None:
            self.share_x = True
            self.share_y = True
        self.twinx = kwargs.get('twinx', False)
        self.twiny = kwargs.get('twiny', False)
        if self.twinx == self.twiny and self.twinx:
            raise AxisError('cannot simultaneously twin x and y axes')
        self.xtrans = kwargs.get('xtrans', None)
        self.x2trans = kwargs.get('x2trans', None)
        self.ytrans = kwargs.get('ytrans', None)
        self.y2trans = kwargs.get('y2trans', None)
        self.ztrans = kwargs.get('ztrans', None)
        self.xmin = kwargs.get('xmin', None)
        self.x2min = kwargs.get('x2min', None)
        self.xmax = kwargs.get('xmax', None)
        self.x2max = kwargs.get('x2max', None)
        self.ymin = kwargs.get('ymin', None)
        self.y2min = kwargs.get('y2min', None)
        self.ymax = kwargs.get('ymax', None)
        self.y2max = kwargs.get('y2max', None)
        self.zmin = kwargs.get('zmin', None)
        self.zmax = kwargs.get('zmax', None)

        # Define DataFrames
        self.df_all = self.check_df(kwargs.get('df'))
        self.df_fig = None
        self.df_sub = None

        # Get the x, y, and (optional) axis column names and error check
        self.x = utl.validate_list(kwargs.get('x'))
        self.y = utl.validate_list(kwargs.get('y'))
        self.z = utl.validate_list(kwargs.get('z'))
        self.x = self.check_xyz('x')
        self.y = self.check_xyz('y')
        self.z = self.check_xyz('z')

        # Stats
        self.stat = kwargs.get('stat', None)

        # Boxplot specifid
        self.bp_groups = None

        # Apply an optional filter to the data
        self.filter = kwargs.get('filter', None)
        if self.filter:
            self.df_all = self.df_filter(self.filter)

        # Define rc grouping column names
        self.col = self.check_group_columns('col', kwargs.get('col', None))
        self.col_vals = None
        self.row = self.check_group_columns('row', kwargs.get('row', None))
        self.row_vals = None
        self.wrap = self.check_group_columns('wrap', kwargs.get('wrap', None))
        self.wrap_vals = None
        self.ncol = 1
        self.nleg = 0
        self.nrow = 1
        self.nwrap = 0

        # Define legend grouping column names (legends are common to a figure,
        #   not an rc subplot)
        if 'legend' in kwargs.keys():
            self.legend = self.check_group_columns('legend',
                                                   kwargs.get('legend', None))
            self.legend = self.legend[0]

        # Define figure grouping column names
        if 'fig_groups' in kwargs.keys():
            self.fig = self.check_group_columns('fig',
                                                kwargs.get('fig_groups', None))
        else:
            self.fig = self.check_group_columns('fig', kwargs.get('fig', None))
        self.fig_vals = None

        # Other kwargs
        for k, v in kwargs.items():
            if k not in ['df', 'plot_type', 'x', 'y', 'z']:
                setattr(self, k, v)

    def check_df(self, df):
        """
        Validate the dataframe
        """

        if df is None:
            raise ValueError('Must provide a DataFrame called "df" '
                             'for plotting!')

        if len(df) == 0:
            raise ValueError('DataFrame is empty.  Nothing to plot!')

        return df.copy()

    def check_group_columns(self, group_type, col_names):
        """
        Check wrap/row/column grouping variables for errors

        Args:
            group_type (str): type of grouping (row, col, leg, wrap)
            col_name (str): name of the column by which to group

        """

        # Force list type
        values = utl.validate_list(col_names)

        # Check that each value exists in the dataframe
        if values is None:
            return

        for val in values:
            if val not in self.df_all.columns:
                raise GroupingError('Grouping column "%s" is not '
                                    'in the DataFrame!' % val)

        # Check for no groups
        if len(natsorted(list(self.df_all.groupby(values).groups.keys()))) == 0:
            raise GroupingError('The number of unique groups in the data for '
                                'the "%s=[%s]" is 0' %
                                (group_type, ', '.join(col_names)))

        return values

    def check_xyz(self, xyz):
        """
        Validate the name and column data provided for x, y, and/or z
        Args:
            xyz (str): name of variable to check
        TODO:
            add option to recast non-float/datetime column as categorical str
        """

        if xyz not in REQUIRED_VALS[self.plot_type]:
            return

        vals = getattr(self, xyz)

        if vals is None:
            raise AxisError('Must provide a column name for "%s"' % xyz)

        for val in vals:
            # Check case
            try:
                self.df_all[val] = self.df_all[val].astype(float)
                continue
            except:
                pass
            try:
                self.df_all[val] = self.df_all[val].astype('datetime64[ns]')
                continue
            except:
                raise AxisError('Could not convert x-column "%s" to float or '
                                 'datetime.' % val)

        # Check for axis errors
        if self.twinx and len(self.y) != 2:
            raise AxisError('twinx error! %s y values were specified but'
                            ' two are required' % len(self.y))
        if self.twinx and len(self.x) > 1:
            raise AxisError('twinx error! only one x value can be specified')
        if self.twiny and len(self.x) != 2:
            raise AxisError('twiny error! %s x values were specified but'
                            ' two are required' % len(self.x))
        if self.twiny and len(self.y) > 1:
            raise AxisError('twiny error! only one y value can be specified')
        # if len(self.y) > 1 and len(self.x) > 1 and len(self.y) != len(self.x):
        #     raise AxisError('too many axes! Number of x and y axes specified '
        #                     'must match OR at least one axis must contain '
        #                     'only one value')

        # not sure if this is relevant anymore!
        self.independent = 'x' if len(self.y) >= len(self.x) else 'y'
        self.dependent = 'y' if len(self.y) >= len(self.x) else 'x'

        return vals

    def df_filter(self, filt_orig):
        """  Filter the DataFrame

        Due to limitations in pd.query, column names must not have spaces.  This
        function will temporarily replace spaces in the column names with
        underscores, but the supplied query string must contain column names
        without any spaces

        Args:
            filt_orig (str):  query expression for filtering

        Returns:
            filtered DataFrame
        """

        def special_chars(text, skip=[]):
            """
            Replace special characters in a text string

            Args:
                text (str): input string
                skip (list): characters to skip

            Returns:
                formatted string
            """

            chars = {' ': '_', '.': 'dot', '[': '',']': '', '(': '', ')': '',
                     '-': '_', '^': '', '>': '', '<': '', '/': '_', '@': 'at',
                     '%': 'percent'}
            for sk in skip:
                chars.pop(sk)
            for k, v in chars.items():
                text = text.replace(k, v).lstrip(' ').rstrip(' ')
            return text

        df2 = self.df_all.copy()

        # Parse the filter string
        filt = utl.get_current_values(df2, filt_orig)

        # Remove spaces from
        cols_orig = [f for f in self.df_all.columns]
        cols_new = ['fCp%s' % f for f in cols_orig.copy()]
        cols_new = [special_chars(f) for f in cols_new]

        df2.columns = cols_new

        # Reformat the filter string for compatibility with pd.query
        operators = ['==', '<', '>', '!=']
        ands = [f.lstrip().rstrip() for f in filt.split('&')]
        for ia, aa in enumerate(ands):
            ors = [f.lstrip() for f in aa.split('|')]
            for io, oo in enumerate(ors):
                # Temporarily remove any parentheses
                param_start = False
                param_end = False
                if oo[0] == '(':
                    oo = oo[1:]
                    param_start = True
                if oo[-1] == ')':
                    oo = oo[0:-1]
                    param_end = True
                for op in operators:
                    if op not in oo:
                        continue
                    vals = oo.split(op)
                    vals[0] = vals[0].rstrip()
                    vals[1] = vals[1].lstrip()
                    if vals[1] == vals[0]:
                        vals[1] = 'fCp%s' % special_chars(vals[1])
                    vals[0] = 'fCp%s' % special_chars(vals[0])
                    ors[io] = op.join(vals)
                    if param_start:
                        ors[io] = '(' + ors[io]
                    if param_end:
                        ors[io] = ors[io] + ')'
            if len(ors) > 1:
                ands[ia] = '|'.join(ors)
            else:
                ands[ia] = ors[0]
        if len(ands) > 1:
            filt = '&'.join(ands)
        else:
            filt = ands[0]

        # Apply the filter
        try:
            df2 = df2.query(filt)
            df2.columns = cols_orig

            return df2

        except:
            print('Could not filter data!\n   Original filter string: %s\n   '
                  'Modified filter string: %s' % (filt_orig, filt))

            return df

    def get_all_groups(self, df):
        """
        Generator to get all possible allowed groups of data

        Args:
            df:

        Returns:

        """

        group_cols = ['row', 'col', 'wrap', 'leg']
        groups = [getattr(self, f) for f in group_cols
                  if hasattr(self, f) and getattr(self, f) is not None]

        for i, (nn, gg) in enumerate(df.groupby(groups)):
            yield i, nn, self.transform(gg.copy())

    def get_data_range(self, ax, df):
        """
        Determine the min/max values for a given axis based on user inputs

        Args:
            axis (str): x, x2, y, y2, z
            df (pd.DataFrame): data table to use for range calculation

        Returns:
            min, max tuple
        """

        if not hasattr(self, ax) or getattr(self, ax) is None:
            return None, None
        elif len([f for f in getattr(self, ax) if str(f) not in df.columns]) > 0:
            return None, None
        else:
            cols = getattr(self, ax)

        # Groupby for stats
        if self.stat is not None and 'only' in self.stat:
            stat_groups = []
            vals_2_chk = ['stat_val', 'leg', 'col', 'row', 'wrap']
            for v in vals_2_chk:
                if getattr(self, v) is not None:
                    stat_groups += getattr(self, v)

        # Account for any applied stats
        if self.stat is not None and 'only' in self.stat \
                and 'median' in self.stat:
            df = df.groupby(stat_groups).median().reset_index()
        elif self.stat is not None and 'only' in self.stat:
            df = df.groupby(stat_groups).mean().reset_index()

        # Get the dataframe values for this axis
        dfax = df[cols]

        # Calculate actual min / max vals for the axis
        if self.ax_scale in ['log%s' % ax, 'loglog', 'semilog%s' % ax]:
            axmin = dfax[dfax > 0].stack().min()
            axmax = dfax.stack().max()
            axdelta = np.log10(axmax)-np.log10(axmin)
        else:
            axmin = dfax.stack().min()
            axmax = dfax.stack().max()
            axdelta = axmax-axmin
        if axdelta <= 0:
            axmin -= 0.1*axmin
            axmax += 0.1*axmax

        # Check user-specified min values
        vmin = getattr(self, '%smin' % ax)
        if vmin is not None and 'iqr' in str(vmin).lower():
            factor = str(vmin).split('*')
            if len(factor) == 1:
                factor = 1
            else:
                factor = float(factor[0])
            if self.box_groups is None:
                q1 = dfax.quantile(0.25).min()
                q3 = dfax.quantile(0.75).max()
                iqr = factor*(q3 - q1)
                vmin = q1 - iqr
            else:
                st()
                q1 = dfax.groupby(self.box_groups) \
                          .quantile(0.25)[cols[iax]].reset_index()
                q3 = dfax.groupby(self.box_groups) \
                         .quantile(0.75)[cols[iax]].reset_index()
                iqr = factor*(q3[cols[iax]] - q1[cols[iax]])
                vmin = (q1[cols[iax]] - iqr[cols[iax]]).min().iloc[0]
        elif vmin is not None and 'q' in str(vmin).lower():
            xq = float(str(vmin).lower().replace('q', ''))/100
            if self.box_groups is None:
                vmin = dfax.quantile(xq).min()
            else:
                st()
                vmin = dfax.groupby(self.box_groups) \
                        .quantile(xq)[cols[iax]].min().iloc[0]
        elif vmin is not None:
            vmin = vmin
        elif self.ax_limit_padding is not None:
            if self.ax_scale in ['log%s' % ax, 'loglog',
                                 'semilog%s' % ax]:
                axmin = np.log10(axmin) - self.ax_limit_padding * \
                        np.log10(axdelta)/(1-2*self.ax_limit_padding)
                vmin = 10**axmin
            else:
                axmin -= self.ax_limit_padding*axdelta / \
                         (1-2*self.ax_limit_padding)
                vmin = axmin
        else:
            vmin = None

        # Check user-specified max values
        vmax = getattr(self, '%smax' % ax)
        if vmax is not None and 'iqr' in str(vmin).lower():
            factor = str(vmax).split('*')
            if len(factor) == 1:
                factor = 1
            else:
                factor = float(factor[0])
            if self.box_groups is None:
                q1 = dfax.quantile(0.25).min()
                q3 = dfax.quantile(0.75).max()
                iqr = factor*(q3 - q1)
                vmax = q3 + iqr
            else:
                st()
                q1 = dfax.groupby(self.box_groups) \
                          .quantile(0.25)[cols[iax]].reset_index()
                q3 = dfax.groupby(self.box_groups) \
                         .quantile(0.75)[cols[iax]].reset_index()
                iqr = factor*(q3[cols[iax]] - q1[cols[iax]])
                vmax = (q3[cols[iax]] + iqr[cols[iax]]).max().iloc[0]
        elif vmax is not None and 'q' in str(vmax).lower():
            xq = float(str(vmax).lower().replace('q', ''))/100
            if self.box_groups is None:
                vmax = dfax.quantile(xq).max()
            else:
                st()
                vmax = dfax.groupby(self.box_groups) \
                        .quantile(xq)[cols[iax]].max().iloc[0]
        elif vmax is not None:
            vmax = vmax
        elif self.ax_limit_padding is not None:
            if self.ax_scale in ['log%s' % ax, 'loglog',
                                 'semilog%s' % ax]:
                axmax = np.log10(axmax) + self.ax_limit_padding * \
                        np.log10(axdelta)/(1-2*self.ax_limit_padding)
                vmax = 10**axmax
            else:
                axmax += self.ax_limit_padding*axdelta
                vmax = axmax
        else:
            vmax = None

        return vmin, vmax

    def get_data_ranges(self, ir, ic):
        """
        Get the data ranges

        Args:
            ir:
            ic:

        """

        axs = ['x', 'x2', 'y', 'y2', 'z']

        for ax in axs:
            if getattr(self, 'share_%s' % ax) and ir==0 and ic==0:
                vals = self.get_data_range(ax, self.df_fig)
                self.ranges[ir, ic]['%smin' % ax] = vals[0]
                self.ranges[ir, ic]['%smax' % ax] = vals[1]
            elif self.share_row:
                vals = self.get_data_range(
                           ax,
                           self.df_fig[self.df_fig[self.row]==self.row_vals[ir]])
                self.ranges[ir, ic]['%smin' % ax] = vals[0]
                self.ranges[ir, ic]['%smax' % ax] = vals[1]
            elif self.share_col and ir==0:
                vals = self.get_data_range(
                           ax,
                           self.df_fig[self.df_fig[self.col]==self.col_vals[ic]])
                self.ranges[ir, ic]['%smin' % ax] = vals[0]
                self.ranges[ir, ic]['%smax' % ax] = vals[1]
            elif not getattr(self, 'share_%s' % ax):
                vals = self.get_data_range(ax, self.df_rc)
                self.ranges[ir, ic]['%smin' % ax] = vals[0]
                self.ranges[ir, ic]['%smax' % ax] = vals[1]
            else:
                self.ranges[ir, ic]['%smin' % ax] = \
                    self.ranges[0, 0]['%smin' % ax]
                self.ranges[ir, ic]['%smax' % ax] = \
                    self.ranges[0, 0]['%smax' % ax]

    def get_df_figure(self):
        """
        Generator to subset the main DataFrame based on fig_item grouping

        Args:
            fig_item (str): figure grouping value
            kw (dict): kwargs dict

        Returns:
            DataFrame subset
        """

        self.get_fig_groupings()
        if not self.fig_vals:
            self.get_legend_groupings(self.df_all)
            self.get_rc_groupings(self.df_all)
            self.df_fig = self.df_all
            for ir, ic, df_rc in self.get_rc_subset(self.df_fig, True):
                continue
            yield None, None, None, self.df_fig

        else:
            for ifig, fig_val in enumerate(self.fig_vals):
                if type(fig_val) is tuple:
                    for ig, gg in enumerate(fig_val):
                        self.df_fig = self.df_all[self.df_all[self.fig_groups[ig]] == gg].copy()
                elif self.fig_groups is not None:
                    if type(self.fig_groups) is list:
                        self.df_fig = self.df_all[self.df_all[self.fig_groups[0]] == fig_val].copy()
                    else:
                        self.df_fig = self.df_all[self.df_all[self.fig_groups] == fig_val].copy()
                else:
                    self.df_fig = self.df_all

                self.get_legend_groupings(self.df_fig)
                self.get_rc_groupings(self.df_fig)

                for ir, ic, df_rc in self.get_rc_subset(self.df_fig, True):
                    continue
                yield ifig, fig_val, self.fig, self.df_fig

        self.df_fig = None

    def get_fig_groupings(self):
        """
        Determine the figure grouping levels
        """

        if self.fig:
            self.fig_vals = list(self.df_all.groupby(self.fig).groups.keys())

    def get_legend_groupings(self, df):
        """
        Determine the legend groupings

        Args:
            df (pd.DataFrame):  data being plotted

        Returns:
            updated kwargs dict
        """

        if not self.legend:
            return

        leg_all = []

        if self.legend:
            if type(self.legend) is list:
                for ileg, leg in enumerate(self.legend):
                    if ileg == 0:
                        temp = df[leg].copy()
                    else:
                        temp = temp.map(str) + ' | ' + df[leg].map(str)
                self.legend = ' | '.join(self.legend)
                df[self.legend] = temp
            legend_vals = \
                natsorted(list(df.groupby(self.legend).groups.keys()))
            self.nleg = len(legend_vals)
        else:
            legend_vals = [None]
            self.nleg = 0

        for leg in legend_vals:
            for xx in self.x:
                for yy in self.y:
                    leg_all += [(leg, xx, yy)]

        leg_df = pd.DataFrame(leg_all, columns=['Leg', 'x', 'y'])

        # if leg specified
        if not (leg_df.Leg==None).all():
            leg_df['names'] = list(leg_df.Leg)

        # if more than one y axis and leg specified
        if len(leg_df.y.unique()) > 1 and not (leg_df.Leg==None).all() and len(leg_df.x.unique()) == 1:
            leg_df['names'] = leg_df.Leg.map(str) + ' | ' + leg_df.y.map(str)
        # elif self.twinx:
        #     leg_df['names'] = leg_df.y

        # if more than one x and leg specified
        if 'names' not in leg_df.columns:
            leg_df['names'] = leg_df.x
        elif len(leg_df.x.unique()) > 1 and not self.twinx:
            leg_df['names'] = \
                leg_df['names'].map(str) + ' | ' + leg_df.y.map(str) + ' / ' + leg_df.x.map(str)
        # elif self.twinx:
        #     leg_df['names'] = leg_df.x.map(str)

        new_index = natsorted(leg_df['names'])
        leg_df = leg_df.set_index('names')
        # leg_df = leg_df.loc[new_index].reset_index() # why is this here??
        self.legend_vals = leg_df.reset_index()

    def get_plot_data(self, df):
        """
        Generator to subset into discrete sets of data for each curve

        Args:
            df (pd.DataFrame): main DataFrame

        Returns:
            subset
        """

        if type(self.legend_vals) != pd.DataFrame:
            vals = pd.DataFrame({'x':self.x, 'y':self.y})
            for irow, row in vals.iterrows():
                # Set twin ax status
                twin = False
                if (row['x'] != vals.loc[0, 'x'] and self.twiny) \
                        or (row['y'] != vals.loc[0, 'y'] and self.twinx):
                    twin = True
                yield irow, df, row['x'], row['y'], None, twin

        else:
            for irow, row in self.legend_vals.iterrows():
                if row['Leg'] is not None:
                    df2 = df[df[self.legend]==row['Leg']].copy()

                # Filter out all nan data
                if len(df2[row['x']].dropna()) == 0 \
                        or len(df2[row['y']].dropna()) == 0:
                    continue

                # Set twin ax status
                twin = False
                if (row['x'] != self.legend_vals.loc[0, 'x'] and self.twiny) \
                        or (row['y'] != self.legend_vals.loc[0, 'y'] and self.twinx):
                    twin = True

                yield irow, df2, row['x'], row['y'], row['names'], twin

    def get_plot_data2(self, df):
        """
        Generator to subset into discrete sets of data for each curve

        Args:
            df (pd.DataFrame): main DataFrame

        Returns:
            subset
        """

        if self.legend_vals:
            leg_df = []
            #for ileg, (nleg, gleg) in enumerate(df.groupby(self.legend)):
            #    leg_df += [(ileg, nleg, gleg)]
            for ival, val in enumerate(self.legend_vals):
                leg_df += [(ival, val, df[df[self.legend]==val])]
        else:
            leg_df = [(0, None, df)]

        for ileg, nleg, gleg in leg_df:
            for ix, nx in enumerate(self.x):
                gx = gleg[nx]
                for iy, ny in enumerate(self.y):
                    gy = gleg[ny]
                    idx = ileg*len(self.x)*len(self.y) + ix*len(self.y) + iy
                    yield (ileg, ix, iy, idx), (nleg, nx, ny), gx, gy

    def get_rc_groupings(self, df):
        """
        Determine the row and column or wrap grid groupings

        Args:
            df (pd.DataFrame):  data being plotted; usually a subset of
                self.df_all
        """

        # Set up wrapping (wrap option overrides row/col)
        if self.wrap:
            self.wrap_vals = \
                natsorted(list(df.groupby(self.wrap).groups.keys()))
            rcnum = int(np.ceil(np.sqrt(len(self.wrap_vals))))
            self.ncol = rcnum
            self.nrow = int(np.ceil(len(self.wrap_vals)/rcnum))
            self.nwrap = len(self.wrap_vals)

        # Non-wrapping option
        else:
            # Set up the row grouping
            if self.col:
                self.col_vals = \
                    natsorted(list(df.groupby(self.col).groups.keys()))
                self.ncol = len(self.col_vals)

            if self.row:
                self.row_vals = \
                    natsorted(list(df.groupby(self.row).groups.keys()))
                self.nrow = len(self.row_vals)

        if self.ncol == 0:
            raise GroupingError('Cannot make subplot(s): '
                                'number of columns is 0')
        if self.nrow == 0:
            raise GroupingError('Cannot make subplot(s): '
                                'number of rows is 0')

        self.ranges = np.array([[None]*self.ncol]*self.nrow)
        for ir in range(0, self.nrow):
            for ic in range(0, self.ncol):
                self.ranges[ir, ic] = {}

    def get_rc_subset(self, df, ranges=False):
        """
        Subset the data by the row/col values

        Args:
            df (pd.DataFrame): main DataFrame

        Returns:
            subset DataFrame
        """

        transform = any([self.xtrans, self.x2trans, self.ytrans, self.y2trans,
                         self.ztrans])

        for ir in range(0, self.nrow):
            for ic in range(0, self.ncol):
                if self.wrap is not None:
                    if ir*self.ncol + ic > self.nwrap-1:
                        self.df_rc = pd.DataFrame()
                    else:
                        wrap = dict(zip(self.wrap,
                                    utl.validate_list(self.wrap_vals[ir*self.ncol + ic])))
                        self.df_rc = df.loc[(df[list(wrap)] == pd.Series(wrap)).all(axis=1)].copy()
                else:
                    if self.row is not None and self.col is not None:
                        row = self.row_vals[ir]
                        col = self.col_vals[ic]
                        self.df_rc = df[(df[self.row]==row) &
                                        (df[self.col]==col)].copy()
                    elif self.row and not self.col:
                        row = self.row_vals[ir]
                        self.df_rc = df[(df[self.row]==row)].copy()
                    elif self.col and not self.row:
                        col = self.col_vals[ic]
                        self.df_rc = df[(df[self.col]==col)].copy()
                    else:
                        self.df_rc = df

                # Perform any axis transformations
                if transform:
                    self.df_rc = self.transform(self.df_rc)

                # Deal with empty dfs
                if len(self.df_rc) == 0:
                    self.df_rc = pd.DataFrame()

                # Calculate axis ranges
                if ranges:
                    self.get_data_ranges(ir, ic)

                # Yield the subset
                yield ir, ic, self.df_rc

        self.df_sub = None

    def see(self):
        """
        Prints a readable list of class attributes
        """

        df = pd.DataFrame({'Attribute':list(self.__dict__.copy().keys()),
             'Name':[str(f) for f in self.__dict__.copy().values()]})
        df = df.sort_values(by='Attribute').reset_index(drop=True)

        return df

    def transform(self, df):
        """
        Transform x, y, or z data

        Args:
            df (pd.DataFrame): current DataFrame
            x (str): x column name
            y (list): y column names
            z (str): z column name

        Returns:
            updated DataFrame
        """

        df = df.copy()

        axis = ['x', 'y', 'z']

        for ax in axis:
            vals = getattr(self, ax)
            if not vals:
                continue
            for val in vals:
                if getattr(self, '%strans' % ax) == 'abs':
                    df.loc[:, val] = abs(df[val])
                elif getattr(self, '%strans' % ax) == 'negative' \
                        or getattr(self, '%strans' % ax) == 'neg':
                    df.loc[:, val] = -df[val]
                elif getattr(self, '%strans' % ax) == 'inverse' \
                        or getattr(self, '%strans' % ax) == 'inv':
                    df.loc[:, val] = 1/df[val]
                elif (type(getattr(self, '%strans' % ax)) is tuple \
                        or type(getattr(self, '%strans' % ax)) is list) \
                        and getattr(self, '%strans' % ax)[0] == 'pow':
                    df.loc[:, val] = df[val]**getattr(self, '%strans' % ax)[1]
                elif getattr(self, '%strans' % ax) == 'flip':
                    maxx = df.loc[:, val].max()
                    df.loc[:, val] -= maxx
                    df.loc[:, val] = abs(df[val])

        return df