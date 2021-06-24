from . import data
import pdb
import pandas as pd
import numpy as np
from .. import utilities
import scipy.stats as ss
utl = utilities
db = pdb.set_trace


class NQ(data.Data):
    def __init__(self, **kwargs):

        name = 'nq'
        req = []
        opt = ['x']

        if not kwargs.get('x', None):
            kwargs['x'] = ['Value']
            kwargs['df'] = pd.DataFrame(kwargs['df'].stack())
            kwargs['df'].columns = kwargs['x']
        kwargs['trans_x'] = 'nq'
                    
        super().__init__(name, req, opt, **kwargs)

        # overrides
        self.y = ['Sigma']

    def get_data_ranges(self):

        self._get_data_ranges()

    def subset_modify(self, df, ir, ic):

        return self._subset_modify(df, ir, ic)

