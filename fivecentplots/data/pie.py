from . import data
import pdb
import pandas as pd
import numpy as np
from .. import utilities
import scipy.stats as ss
try:
    from natsort import natsorted
except:
    natsorted = sorted
utl = utilities
db = pdb.set_trace


class Pie(data.Data):
    def __init__(self, **kwargs):

        name = 'pie'
        req = ['x', 'y']
        opt = []

        super().__init__(name, req, opt, **kwargs)

        # overrides


    def get_data_ranges(self):

        for ir, ic, plot_num in self.get_subplot_index():
            self.ranges[ir, ic]['xmin'] = -1
            self.ranges[ir, ic]['xmax'] = 1
            self.ranges[ir, ic]['ymin'] = -1
            self.ranges[ir, ic]['ymax'] = 1
            
            self.ranges[ir, ic]['x2min'] = None
            self.ranges[ir, ic]['x2max'] = None
            self.ranges[ir, ic]['y2min'] = None
            self.ranges[ir, ic]['y2max'] = None
            self.ranges[ir, ic]['zmin'] = None
            self.ranges[ir, ic]['zmax'] = None
            
    def get_legend_groupings(self, df):
        """
        Determine the legend groupings

        Args:
            df (pd.DataFrame):  data being plotted

        Returns:
            updated kwargs dict
        """

        if self.legend == True and self.twin_x \
                or self.legend == True and len(self.y) > 1:
            self.legend_vals = self.y + self.y2
            self.nleg_vals = len(self.y + self.y2)
            return
        elif self.legend == True and self.twin_y:
            self.legend_vals = self.x + self.x2
            self.nleg_vals = len(self.x + self.x2)
            return

        if not self.legend:
            return

        leg_all = []

        # custom for pie plot
        self.legend = self.x[0]

        if self.legend == True:
            self.legend = None  # no option for legend here so disable
            return

        if self.legend:
            if type(self.legend) is str and ' | ' in self.legend:
                self.legend = self.legend.split(' | ')
            if type(self.legend) is list:
                for ileg, leg in enumerate(self.legend):
                    if ileg == 0:
                        temp = df[leg].copy()
                    else:
                        temp = temp.map(str) + ' | ' + df[leg].map(str)
                self.legend = ' | '.join(self.legend)
                df[self.legend] = temp
            if self.sort:
                legend_vals = \
                    natsorted(list(df.groupby(self.legend).groups.keys()))
            else:
                legend_vals = \
                    list(df.groupby(self.legend, sort=False).groups.keys())
            self.nleg_vals = len(legend_vals)
        else:
            legend_vals = [None]
            self.nleg_vals = 0

        for leg in legend_vals:
            if not self.x or self.name == 'gantt':
                selfx = [None]
            else:
                selfx = self.x + self.x2
            if not self.y:
                selfy = [None]
            else:
                selfy = self.y + self.y2
            for xx in selfx:
                for yy in selfy:
                    leg_all += [(leg, xx, yy)]

        leg_df = pd.DataFrame(leg_all, columns=['Leg', 'x', 'y'])

        # if leg specified
        if not (leg_df.Leg==None).all():
            leg_df['names'] = list(leg_df.Leg)

        # if more than one y axis and leg specified
        if self.wrap == 'y' or self.wrap == 'x':
            leg_df = leg_df.drop(self.wrap, axis=1).drop_duplicates()
            leg_df[self.wrap] = self.wrap
        elif self.row == 'y':
            del leg_df['y']
            leg_df = leg_df.drop_duplicates().reset_index(drop=True)
        elif self.col == 'x':
            del leg_df['x']
            leg_df = leg_df.drop_duplicates().reset_index(drop=True)
        elif len(leg_df.y.unique()) > 1 and not (leg_df.Leg==None).all() \
                and len(leg_df.x.unique()) == 1:
            leg_df['names'] = leg_df.Leg.map(str) + ' | ' + leg_df.y.map(str)

        # if more than one x and leg specified
        if 'names' not in leg_df.columns:
            leg_df['names'] = leg_df.x
        elif 'x' in leg_df.columns and len(leg_df.x.unique()) > 1 \
                and not self.twin_x:
            leg_df['names'] = \
                leg_df['names'].map(str) + ' | ' + leg_df.y.map(str) + ' / ' + leg_df.x.map(str)

        leg_df = leg_df.set_index('names')
        self.legend_vals = leg_df.reset_index()

    def subset_modify(self, df, ir, ic):

        return self._subset_modify(df, ir, ic)

    def subset_wrap(self, ir, ic):

        return self._subset_wrap(ir, ic)

