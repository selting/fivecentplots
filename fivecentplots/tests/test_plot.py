import fivecentplots as fcp
import pandas as pd
import os
import sys
import pdb
import platform
import fivecentplots.utilities as utl
import inspect
osjoin = os.path.join
db = pdb.set_trace
if platform.system() != 'Windows':
    print('Warning!  Image test files generated in windows.  Compatibility with linux/mac may vary')

MPL = utl.get_mpl_version_dir()
MASTER = osjoin(os.path.dirname(fcp.__file__),
                'tests', 'test_images', MPL, 'plot.py')

# Sample data
df = pd.read_csv(osjoin(os.path.dirname(
    fcp.__file__), 'tests', 'fake_data.csv'))
ts = pd.read_csv(osjoin(os.path.dirname(fcp.__file__), 'tests', 'fake_ts.csv'))

# Set theme
fcp.set_theme('gray')
# fcp.set_theme('white')


# Other
SHOW = False


def make_all():
    """
    Remake all test master images
    """

    members = inspect.getmembers(sys.modules[__name__])
    members = [f for f in members if 'plt_' in f[0]]
    for member in members:
        print('Running %s...' % member[0], end='')
        member[1](master=True)
        print('done!')


def show_all():
    """
    Run the show=True option on all plt functions
    """

    members = inspect.getmembers(sys.modules[__name__])
    members = [f for f in members if 'plt_' in f[0]]
    for member in members:
        print('Running %s...' % member[0], end='')
        member[1](show=True)
        db()


# plt_ functions can be used directly outside of pytest for debug
def plt_xy_scatter(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'xy_scatter_master') if master else 'xy_scatter'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False,
             show=False, filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_xy_legend(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'xy_legend_master') if master else 'xy_legend'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', show=SHOW, ymax=1.4,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_xy_log_scale(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'xy_log-scale_master') if master else 'xy_log-scale'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', ax_scale='loglog', legend='Die', show=SHOW, xmin=0.9, xmax=2.1,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             grid_minor=True, filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_xy_categorical(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'xy_categorical_master') if master else 'xy_categorical'

    # Make the plot
    fcp.plot(df, x='Die', y='I [A]', show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25 & Voltage==1.5',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_xy_ts(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'xy_ts_master') if master else 'xy_ts'

    # Make the plot
    fcp.plot(ts, x='Date', y='Happiness Quotient', markers=False, ax_size=[1000, 250],
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_secondary_xy_shared_y(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'secondary-xy_shared-y_master') if master else 'secondary-xy_shared-y'

    # Make the plot
    fcp.plot(df, x='Voltage', y=['Voltage', 'I [A]'], twin_x=True, show=SHOW, legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25 & Die=="(-1,2)"',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_secondary_xy_shared_x(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'secondary-xy_shared-x_master') if master else 'secondary-xy_shared-x'

    # Make the plot
    fcp.plot(df, x=['Voltage', 'I [A]'], y='Voltage', legend='Die', twin_y=True, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25 & Die=="(-1,2)"',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_multiple_xy_y(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'multiple-xy_y-only_master') if master else 'multiple-xy_y-only'

    # Make the plot
    fcp.plot(df, x='Voltage', y=['Boost Level', 'I [A]'], legend='Die', show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_multiple_xy_x(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'multiple-xy_x-only_master') if master else 'multiple-xy_x-only'

    # Make the plot
    fcp.plot(df, x=['Boost Level', 'I [A]'], y='Voltage', legend='Die', show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_multiple_xy_both(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'multiple-xy_both_master') if master else 'multiple-xy_both'

    # Make the plot
    fcp.plot(df, x=['Boost Level', 'I [A]'], y=['Voltage', 'Temperature [C]'], legend='Die', show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_multiple_xy_both_label(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'multiple-xy_both_label_master') if master else 'multiple-xy_both_label'

    # Make the plot
    fcp.plot(df, x=['Boost Level', 'I [A]'], y=['Voltage', 'Temperature [C]'], legend='Die', show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             label_x='yep', label_y_text='no way',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_row(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'grid-plots-row_master') if master else 'grid-plots-row'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', row='Boost Level',
             show=SHOW, ax_size=[225, 225],
             filter='Substrate=="Si" & Target Wavelength==450 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_column(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'grid-plots-column_master') if master else 'grid-plots-column'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', col='Boost Level', show=SHOW, ax_size=[225, 225],
             filter='Substrate=="Si" & Target Wavelength==450 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')
        assert not compare


def plt_row_x_column(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'grid-plots-row-x-column_master') if master else 'grid-plots-row-x-column'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', col='Boost Level', row='Temperature [C]', show=SHOW,
             ax_size=[225, 225],
             filter='Substrate=="Si" & Target Wavelength==450', label_rc_font_size=13,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_row_x_column_sep_labels(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'grid-plots-row-x-column_sep_labels_master') if master else 'grid-plots-row-x-column_sep_labels'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', col='Boost Level', row='Temperature [C]', show=SHOW,
             ax_size=[225, 225],
             filter='Substrate=="Si" & Target Wavelength==450',
             label_rc_font_size=13, separate_labels=True, share_y=False,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_wrap(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'grid-plots-wrap_master') if master else 'grid-plots-wrap'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', legend='Die', wrap=['Temperature [C]', 'Boost Level'], show=SHOW,
             ax_size=[225, 225], filter='Substrate=="Si" & Target Wavelength==450', label_rc_font_size=13,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_lines(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'other_lines_master') if master else 'other_lines'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW, legend=True,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             ax_hlines=[(0, '#FF0000', '--', 3, 1, 'Open'), 1.2], ax_vlines=[0, (1, '#00FF00')],
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_lines_df(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_lines_df_master') if master else 'other_lines_df'

    # Make the plot
    df['Open'] = 0
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW, legend=True,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             ax_hlines=[('Open', '#FF0000', '--', 3, 1), 1.2], ax_vlines=[0, (1, '#00FF00')],
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_curve_fitting(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_curve-fitting_master') if master else 'other_curve-fitting'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             fit=4, fit_eqn=True, fit_rsq=True, fit_font_size=9,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_curve_fitting_range(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_curve-fitting-range_master') if master else 'other_curve-fitting-range'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             fit=1, fit_eqn=True, fit_rsq=True, fit_font_size=9, fit_range_x=[1.3, 2],
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_curve_fitting_legend(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_curve-fitting-legend_master') if master else 'other_curve-fitting-legend'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW, legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             fit=1, fit_range_x=[1.3, 2], fit_width=2, fit_style='--',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_curve_fitting_legend2(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_curve-fitting-legend2_master') if master else 'other_curve-fitting-legend2'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW, wrap='Die', legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             fit=1, fit_range_x=[1.3, 2], fit_width=2, fit_color='#555555', ax_size=[250, 250],
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_stat_bad(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_stat-lines-bad_master') if master else 'other_stat-lines-bad'

    # Make the plot
    fcp.plot(df, x='I [A]', y='Voltage', title='IV Data', lines=False, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             stat='median',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_stat_good(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_stat-lines-good_master') if master else 'other_stat-lines-good'

    # Make the plot
    fcp.plot(df, x='I [A]', y='Voltage', title='IV Data', lines=False, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             stat='median', stat_val='I Set',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_stat_good_mult(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_stat-lines-good-multiple-y_master') if master else 'other_stat-lines-good-multiple-y'

    # Make the plot
    fcp.plot(df, x='Voltage', y=['Boost Level', 'I [A]'], show=SHOW, legend=True, stat='median',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_conf_int(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_conf-int_master') if master else 'other_conf-int'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False, show=SHOW,
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             conf_int=0.95,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ref_line(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_ref-line-y=x_master') if master else 'other_ref-line-y=x'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', show=SHOW, legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             ref_line=df['Voltage'], ref_line_legend_text='y=x', xmin=0, ymin=0, xmax=1.6, ymax=1.6,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ref_line_mult(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_ref-line_mult_master') if master else 'other_ref-line_mult'

    # Make the plot
    df['2*Voltage'] = 2 * df['Voltage']
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', show=SHOW, legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             xmin=0, ymin=0, xmax=1.6, ymax=1.6,
             ref_line=['Voltage', '2*Voltage'], ref_line_legend_text=['y=x', 'y=2*x'], ref_line_style=['-', '--'],
             ref_line_color=[5, 6], filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ref_line_complex(bm=False, master=False, remove=True, show=False):

    name = osjoin(
        MASTER, 'other_ref-line-complex_master') if master else 'other_ref-line-complex'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', show=SHOW, legend='Die',
             filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             ref_line=1.555 * df['Voltage']**4 - 3.451 * df['Voltage']**3
             + 2.347 * df['Voltage']**2 - 0.496 * df['Voltage'] + 0.014,
             filename=name + '.png', save=not bm, inline=False)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_lcl_only(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'other_lcl_only_master') if master else 'other_lcl_only'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False,
             show=False, filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False,
             lcl=-0.5, ymin=-1, lcl_fill_color='#FF0000')
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ucl_only(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'other_ucl_only_master') if master else 'other_ucl_only'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False,
             show=False, filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False,
             ucl=1.0, ymax=3, ucl_fill_alpha=0.8)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ucl_lcl_inside(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'other_ucl_lcl_inside_master') if master else 'other_ucl_lcl_inside'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False,
             show=False, filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False,
             ucl=1.0, ymax=3, lcl=-0.5, ymin=-1, control_limit_side='inside',
             legend=True)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


def plt_other_ucl_lcl_outside(bm=False, master=False, remove=True, show=False):

    name = osjoin(MASTER, 'other_ucl_lcl_outside_master') if master else 'other_ucl_lcl_outside'

    # Make the plot
    fcp.plot(df, x='Voltage', y='I [A]', title='IV Data', lines=False,
             show=False, filter='Substrate=="Si" & Target Wavelength==450 & Boost Level==0.2 & Temperature [C]==25',
             filename=name + '.png', save=not bm, inline=False,
             ucl=1.0, ymax=3, lcl=-0.5, ymin=-1, ucl_fill_color='#FFFF00',
             legend=True)
    if bm:
        return

    # Compare with master
    if master:
        return
    elif show:
        utl.show_file(osjoin(MASTER, name + '_master.png'))
        utl.show_file(name + '.png')
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'), show=True)
    else:
        compare = utl.img_compare(
            name + '.png', osjoin(MASTER, name + '_master.png'))
        if remove:
            os.remove(name + '.png')

        assert not compare


# test_ functions call plt_ funcs 2x:
# 1) do the comparison with saved image
# 2) do a test plot only with save=False and inline=False and benchmark spead
def test_column(benchmark):
    plt_column()
    benchmark(plt_column, True)


def test_multiple_xy_both(benchmark):
    plt_multiple_xy_both()
    benchmark(plt_multiple_xy_both, True)


def test_multiple_xy_both_label(benchmark):
    plt_multiple_xy_both_label()
    benchmark(plt_multiple_xy_both_label, True)


def test_multiple_xy_x(benchmark):
    plt_multiple_xy_x()
    benchmark(plt_multiple_xy_x, True)


def test_multiple_xy_y(benchmark):
    plt_multiple_xy_y()
    benchmark(plt_multiple_xy_y, True)


def test_other_conf_int(benchmark):
    plt_other_conf_int()
    benchmark(plt_other_conf_int, True)


def test_other_curve_fitting(benchmark):
    plt_other_curve_fitting()
    benchmark(plt_other_curve_fitting, True)


def test_other_curve_fitting_legend(benchmark):
    plt_other_curve_fitting_legend()
    benchmark(plt_other_curve_fitting_legend, True)


def test_other_curve_fitting_legend2(benchmark):
    plt_other_curve_fitting_legend2()
    benchmark(plt_other_curve_fitting_legend2, True)


def test_other_curve_fitting_range(benchmark):
    plt_other_curve_fitting_range()
    benchmark(plt_other_curve_fitting_range, True)


def test_other_lines(benchmark):
    plt_other_lines()
    benchmark(plt_other_lines, True)


def test_other_lines_df(benchmark):
    plt_other_lines_df()
    benchmark(plt_other_lines_df, True)


def test_other_lcl_only(benchmark):
    plt_other_lcl_only()
    benchmark(plt_other_lcl_only, True)


def test_other_ucl_only(benchmark):
    plt_other_ucl_only()
    benchmark(plt_other_ucl_only, True)


def test_other_ucl_lcl_inside(benchmark):
    plt_other_ucl_lcl_inside()
    benchmark(plt_other_ucl_lcl_inside, True)


def test_other_ucl_lcl_outside(benchmark):
    plt_other_ucl_lcl_outside()
    benchmark(plt_other_ucl_lcl_outside, True)


def test_other_ref_line(benchmark):
    plt_other_ref_line()
    benchmark(plt_other_ref_line, True)


def test_other_ref_line_complex(benchmark):
    plt_other_ref_line_complex()
    benchmark(plt_other_ref_line_complex, True)


def test_other_ref_line_mult(benchmark):
    plt_other_ref_line_mult()
    benchmark(plt_other_ref_line_mult, True)


def test_other_stat_bad(benchmark):
    plt_other_stat_bad()
    benchmark(plt_other_stat_bad, True)


def test_other_stat_good(benchmark):
    plt_other_stat_good()
    benchmark(plt_other_stat_good, True)


def test_other_stat_good_mult(benchmark):
    plt_other_stat_good_mult()
    benchmark(plt_other_stat_good_mult, True)


def test_row(benchmark):
    plt_row()
    benchmark(plt_row, True)


def test_row_x_column(benchmark):
    plt_row_x_column()
    benchmark(plt_row_x_column, True)


def test_secondary_xy_shared_x(benchmark):
    plt_secondary_xy_shared_x()
    benchmark(plt_secondary_xy_shared_x, True)


def test_secondary_xy_shared_y(benchmark):
    plt_secondary_xy_shared_y()
    benchmark(plt_secondary_xy_shared_y, True)


def test_wrap(benchmark):
    plt_wrap()
    benchmark(plt_wrap, True)


def test_xy_categorical(benchmark):
    plt_xy_categorical()
    benchmark(plt_xy_categorical, True)


def test_xy_legend(benchmark):
    plt_xy_legend()
    benchmark(plt_xy_legend, True)


def test_xy_log_scale(benchmark):
    plt_xy_log_scale()
    benchmark(plt_xy_log_scale, True)


def test_xy_scatter(benchmark):
    plt_xy_scatter()
    benchmark(plt_xy_scatter, True)


def test_xy_ts(benchmark):
    plt_xy_ts()
    benchmark(plt_xy_ts, True)


if __name__ == '__main__':
    pass
