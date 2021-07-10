from . import data
import pdb
import pandas as pd
import numpy as np
from .. import utilities
import scipy.stats as ss
utl = utilities
db = pdb.set_trace


class ImShow(data.Data):
    def __init__(self, **kwargs):

        name = 'imshow'
        req = []
        opt = []

        kwargs['ax_limit_padding'] = kwargs.get('ax_limit_padding', None)

        super().__init__(name, req, opt, **kwargs)

        # overrides
        self.auto_scale = False
        
        if 'x' not in kwargs.keys() and \
                'y' not in kwargs.keys() and \
                'z' not in kwargs.keys():
            
            self.auto_cols = True
            self.x = ['Column']
            self.y = ['Row']
            self.z = ['Value']
                   
        else:
            self.pivot = True
        
    def check_xyz(self, xyz):
        """
        Validate the name and column data provided for x, y, and/or z
        Args:
            xyz (str): name of variable to check
        TODO:
            add option to recast non-float/datetime column as categorical str
        """

        if xyz not in self.req and xyz not in self.opt:
            return

        if xyz in self.opt and getattr(self, xyz) is None:
            return None

        vals = getattr(self, xyz)

        if vals is None and xyz not in self.opt:
            raise AxisError('Must provide a column name for "%s"' % xyz)

        # Skip standard case check

        # Check for axis errors
        if self.twin_x and len(self.y) != 2:
            raise AxisError('twin_x error! %s y values were specified but'
                            ' two are required' % len(self.y))
        if self.twin_x and len(self.x) > 1:
            raise AxisError('twin_x error! only one x value can be specified')
        if self.twin_y and len(self.x) != 2:
            raise AxisError('twin_y error! %s x values were specified but'
                            ' two are required' % len(self.x))
        if self.twin_y and len(self.y) > 1:
            raise AxisError('twin_y error! only one y value can be specified')

        return vals

    def get_data_range(self, ax, df, plot_num):
        """
        Determine the min/max values for a given axis based on user inputs

        Args:
            axis (str): x, x2, y, y2, z
            df (pd.DataFrame): data table to use for range calculation

        Returns:
            min, max tuple
        """

        if not hasattr(self, ax) or getattr(self, ax) in [None, []]:
            return None, None
        elif self.col == 'x' and self.share_x and ax == 'x':
            cols = self.x_vals
        elif self.row == 'y' and self.share_y and ax == 'y':
            cols = self.y_vals
        else:
            cols = getattr(self, ax)

        # imshow special case
        df = df.dropna(1, 'all')
        groups = self.groupers
        if getattr(self, ax) == ['Column']:
            vmin = 0
            if len(groups) > 0:
                cols = df.iloc[0].dropna().index
                cols = [f for f in cols if f not in groups]
                vmax = len(cols)
            else:
                vmax = len(df.columns)
        elif getattr(self, ax) == ['Row']:
            vmin = 0
            if len(groups) > 0:
                vmax = df.groupby(self.groupers).size().max()
            else:
                vmax = len(df.index)
        elif getattr(self, ax) == ['Value']:# and self.auto_cols:
            vmin = df[utl.df_int_cols(df)].min().min()
            vmax = df[utl.df_int_cols(df)].max().max()
        # elif ax not in ['x2', 'y2', 'z']:
        #     vmin = 0
        #     vmax = len(df[getattr(self, ax)].drop_duplicates())
        # elif ax not in ['x2', 'y2']:
        #     vmin = df[getattr(self, ax)].min().iloc[0]
        #     vmax = df[getattr(self, ax)].max().iloc[0]
        # else:
        #     vmin = None
        #     vmax = None
        # plot_num = utl.plot_num(ir, ic, self.ncol)
        # if getattr(self, '%smin' % ax).get(plot_num):
        #     vmin = getattr(self, '%smin' % ax).get(plot_num)
        # if getattr(self, '%smax' % ax).get(plot_num):
        #     vmax = getattr(self, '%smax' % ax).get(plot_num)
        # if type(vmin) is str:
        #     vmin = None
        # if type(vmax) is str:
        #     vmax = None
        return vmin, vmax

    def get_data_ranges(self):

        """
        Updated data range calculator by subplot for imshow
        """

        # First get any user defined range values and apply optional auto scaling
        df_fig = self.df_fig.copy()  # use temporarily for setting ranges
        self._get_data_ranges_user_defined()
        df_fig = self.get_auto_scale(df_fig)
        
        # Apply shared axes
        for ir, ic, plot_num in self.get_subplot_index():
            for ax in self.axs:
                # Share axes (use self.df_fig to get global min/max)
                if getattr(self, 'share_%s' % ax):
                    vals = self.get_data_range(ax, df_fig, plot_num)
                    self.add_range(ir, ic, ax, 'min', vals[0])
                    self.add_range(ir, ic, ax, 'max', vals[1])
                elif getattr(self, 'share_%s' % ax) and (ir > 0 or ic > 0):
                    self.add_range(ir, ic, ax, 'min', self.ranges[0, 0]['%smin' % ax])
                    self.add_range(ir, ic, ax, 'max', self.ranges[0, 0]['%smax' % ax])

                # Share row
                elif self.share_row and self.row is not None:
                    if self.row == 'y':
                        vals = self.get_data_range(ax, df_fig, plot_num)
                    else:
                        vals = self.get_data_range(ax,
                            df_fig[self.df_fig[self.row[0]] == self.row_vals[ir]], plot_num)
                    self.add_range(ir, ic, ax, 'min', vals[0])
                    self.add_range(ir, ic, ax, 'max', vals[1])
                elif self.share_row and self.row is not None and ic > 0:
                    self.add_range(ir, ic, ax, 'min', self.ranges[ir, 0]['%smin' % ax])
                    self.add_range(ir, ic, ax, 'max', self.ranges[ir, 0]['%smax' % ax])

                # Share col
                elif self.share_col and self.col is not None:
                    if self.col == 'x':
                        vals = self.get_data_range(ax, df_fig, ir, ic)
                    else:
                        vals = self.get_data_range(ax,
                            df_fig[df_fig[self.col[0]] == self.col_vals[ic]], plot_num)
                    self.add_range(ir, ic, ax, 'min', vals[0])
                    self.add_range(ir, ic, ax, 'max', vals[1])
                elif self.share_col and self.col is not None and ir > 0:
                    self.add_range(ir, ic, ax, 'min', self.ranges[0, ic]['%smin' % ax])
                    self.add_range(ir, ic, ax, 'max', self.ranges[0, ic]['%smax' % ax])

                # subplot level when not shared
                else:
                    df_rc = self.subset(ir, ic)
                    
                    # Empty rc
                    if len(df_rc) == 0:  # this doesn't exist yet!
                        self.add_range(ir, ic, ax, 'min', None)
                        self.add_range(ir, ic, ax, 'max', None)
                        continue

                    # Not shared or wrap by x or y
                    elif not getattr(self, 'share_%s' % ax) or \
                            (self.wrap is not None and \
                                self.wrap == 'y' or \
                                self.wrap == 'x'):
                        vals = self.get_data_range(ax, df_rc, plot_num)
                        self.add_range(ir, ic, ax, 'min', vals[0])
                        self.add_range(ir, ic, ax, 'max', vals[1])

                    # Make them all equal to 0,0
                    elif ir > 0 or ic > 0:
                        self.add_range(ir, ic, ax, 'min', self.ranges[0, 0]['%smin' % ax])
                        self.add_range(ir, ic, ax, 'max', self.ranges[0, 0]['%smax' % ax])
        
        # some extras
        width = len(self.df_fig.dropna(1, 'all').columns)
        height = len(self.df_fig.dropna(0, 'all').index)
        self.wh_ratio = width / height
        
        for ir, ic, plot_num in self.get_subplot_index():
            # invert ymin and ymax
            temp = self.ranges[ir, ic]['ymax']
            self.ranges[ir, ic]['ymax'] = self.ranges[ir, ic]['ymin']
            self.ranges[ir, ic]['ymin'] = temp

            # get the ratio of width to height for figure size
            width = self.ranges[ir, ic]['xmax'] - self.ranges[ir, ic]['xmin']
            height = self.ranges[ir, ic]['ymin'] - self.ranges[ir, ic]['ymax']
            self.wh_ratio = max(self.wh_ratio, width / height)     

    def get_rc_subset(self):
        """
        Subset the data by the row/col/wrap values

        Args:
            df (pd.DataFrame): main DataFrame

        Returns:
            subset DataFrame
        """

        for ir in range(0, self.nrow):
            for ic in range(0, self.ncol):
                self.df_rc = self.subset(ir, ic)

                # imshow addition
                self.df_rc.index.astype = int
                cols = utl.df_int_cols(self.df_rc)
                self.df_rc = self.df_rc[cols]
                self.df_rc.columns.astype = int

                # Deal with empty dfs
                if len(self.df_rc) == 0:
                    self.df_rc = pd.DataFrame()

                # Yield the subset
                yield ir, ic, self.df_rc

        self.df_sub = None
        
    def subset_modify(self, df, ir, ic):

        return self._subset_modify(df, ir, ic)

