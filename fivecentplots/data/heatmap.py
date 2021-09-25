from . import data
import pdb
import pandas as pd
import numpy as np
from .. import utilities
import scipy.stats as ss
from natsort import natsorted
utl = utilities
db = pdb.set_trace


class Heatmap(data.Data):
    def __init__(self, **kwargs):

        name = 'heatmap'
        req = []
        opt = ['x', 'y', 'z']
        kwargs['auto_scale'] = False

        super().__init__(name, req, opt, **kwargs)

        if 'x' not in kwargs.keys() and \
                'y' not in kwargs.keys() and \
                'z' not in kwargs.keys():

            self.auto_cols = True
            self.x = ['Column']
            self.y = ['Row']
            self.z = ['Value']

        else:
            self.pivot = True

        self.ax_limit_padding = kwargs.get('ax_limit_padding', None)

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

    def get_data_ranges(self):

        # First get any user defined range values and apply optional auto scaling
        df_fig = self.df_fig.copy()  # use temporarily for setting ranges
        self._get_data_ranges_user_defined()
        df_fig = self.get_auto_scale(df_fig)

        # set ranges by subset
        for ir, ic, plot_num in self.get_subplot_index():
            df_rc = self.subset(ir, ic)

            # auto cols option
            if self.auto_cols:
                df_rc = df_rc[utl.df_int_cols(df_rc)]

                # x
                cols = [f for f in df_rc.columns if type(f) is int]
                self.add_range(ir, ic, 'x', 'min', min(cols))
                self.add_range(ir, ic, 'x', 'max', max(cols))

                # y
                rows = [f for f in df_rc.index if type(f) is int]
                self.add_range(ir, ic, 'y', 'min', min(rows))
                self.add_range(ir, ic, 'y', 'max', max(rows))

                # z
                self.add_range(ir, ic, 'z', 'min', df_rc.min().min())
                self.add_range(ir, ic, 'z', 'max', df_rc.max().max())

            else:
                # x
                self.add_range(ir, ic, 'x', 'min', -0.5)
                self.add_range(ir, ic, 'x', 'max', len(df_rc.columns) + 0.5)

                # y (can update all the get plot nums to range?)
                if self.ymin.get(plot_num) is not None \
                        and self.ymax.get(plot_num) is not None \
                        and self.ymin.get(plot_num) < self.ymax.get(plot_num):
                    ymin = self.ymin.get(plot_num)
                    self.add_range(ir, ic, 'y', 'min', self.ymax.get(plot_num))
                    self.add_range(ir, ic, 'y', 'max', ymin)
                self.add_range(ir, ic, 'y', 'max', -0.5)
                self.add_range(ir, ic, 'y', 'min', len(df_rc) + 0.5)

                # z
                if self.share_col:
                    pass
                elif self.share_row:
                    pass
                elif self.share_z and ir==0 and ic==0:
                    self.add_range(ir, ic, 'z', 'min', self.df_fig[self.z[0]].min())
                    self.add_range(ir, ic, 'z', 'max', self.df_fig[self.z[0]].max())
                elif self.share_z:
                    self.add_range(ir, ic, 'z', 'min', self.ranges[0, 0]['zmin'])
                    self.add_range(ir, ic, 'z', 'max', self.ranges[0, 0]['zmax'])
                else:
                    self.add_range(ir, ic, 'z', 'min', df_rc.min().min())
                    self.add_range(ir, ic, 'z', 'max', df_rc.max().max())

            # not used
            self.add_range(ir, ic, 'x2', 'min', None)
            self.add_range(ir, ic, 'y2', 'min', None)
            self.add_range(ir, ic, 'x2', 'max', None)
            self.add_range(ir, ic, 'y2', 'max', None)

    def subset_modify(self, df, ir, ic):

        if len(df) == 0:
            return df

        if self.pivot:
            # Reshape if input dataframe is stacked
            df = pd.pivot_table(df, values=self.z[0],
                                index=self.y[0], columns=self.x[0])
        if self.sort:
            cols = natsorted(df.columns)
            df = df[cols]
            df.index = natsorted(df.index)

        # Ensure only int columns are present for imshow case and set range
        if self.auto_cols:
            df = df[utl.df_int_cols(df)]

            if 'xmin' in self.ranges[ir, ic].keys() and \
                    self.ranges[ir, ic]['xmin'] is not None:
                df = df[[f for f in df.columns if f >= self.ranges[ir, ic]['xmin']]]
            if 'xmax' in self.ranges[ir, ic].keys() and \
                    self.ranges[ir, ic]['xmax'] is not None:
                df = df[[f for f in df.columns if f <= self.ranges[ir, ic]['xmax']]]
            if 'ymin' in self.ranges[ir, ic].keys() and \
                    self.ranges[ir, ic]['ymin'] is not None:
                df = df.loc[[f for f in df.index if f >= self.ranges[ir, ic]['ymin']]]
            if 'ymax' in self.ranges[ir, ic].keys() and \
                    self.ranges[ir, ic]['ymax'] is not None:
                df = df.loc[[f for f in df.index if f <= self.ranges[ir, ic]['ymax']]]

        # check dtypes to properly designated tick labels
        dtypes = [int, np.int32, np.int64]
        if df.index.dtype in dtypes and list(df.index) != \
                [f + df.index[0] for f in range(0, len(df.index))]:
            df.index = df.index.astype('O')
        if df.columns.dtype == 'object':
            ddtypes = list(set([type(f) for f in df.columns]))
            if all(f in dtypes for f in ddtypes):
                df.columns = [np.int64(f) for f in df.columns]
        elif df.columns.dtype in dtypes and list(df.columns) != \
                [f + df.columns[0] for f in range(0, len(df.columns))]:
            df.columns = df.columns.astype('O')

        # set heatmap element size parameters
        if self.x[0] in self.df_fig.columns:
            self.num_x = len(self.df_fig[self.x].drop_duplicates())
        else:
            self.num_x = None
        if self.y[0] in self.df_fig.columns:
            self.num_y = len(self.df_fig[self.y].drop_duplicates())
        else:
            self.num_y = None

        return df

    def subset_wrap(self, ir, ic):

        return self._subset_wrap(ir, ic)


# fix tick labels, need excess ws_ax_fig?  test_simple
# sharing options not right