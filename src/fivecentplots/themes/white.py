import matplotlib as mpl

#########################################################
# Figure layout defaults
#########################################################
fcp_params = {'ax_edge_color': '#555555',
              'ax_fill_color': '#ffffff',
              'ax_size': [400, 400],  # [width, height]
              'bar_align': 'center',
              'bar_color_by_bar': False,
              'bar_edge_width': 0,
              'bar_error_bars': None,
              'bar_error_color': '#555555',
              'bar_fill_alpha': 0.75,
              'bar_horizontal': False,
              'bar_line': False,
              'bar_stacked': False,
              'bar_width': 0.8,
              'box_divider_color': '#bbbbbb',
              'box_divider_style': '-',
              'box_divider_width': 1,
              'box_fill_color': '#eeeeee',
              'box_grand_mean': False,
              'box_grand_mean_color': '#555555',
              'box_grand_mean_style': '--',
              'box_grand_mean_width': 1,
              'box_grand_median_color': '#0000ff',
              'box_grand_median_style': '--',
              'box_grand_median_width': 1,
              'box_group_means_color': '#ff00ff',
              'box_group_mean_style': '--',
              'box_group_mean_width': 1,
              'box_group_title_edge_color': '#ffffff',
              'box_group_title_fill_color': '#ffffff',
              'box_group_title_font_size': 13,
              'box_group_title_font_color': '#666666',
              'box_group_title_font_style': 'normal',
              'box_group_title_font_weight': 'normal',
              'box_group_label_edge_color': '#555555',
              'box_group_label_font_size': 12,
              'box_group_label_font_color': '#666666',
              'box_group_label_font_style': 'normal',
              'box_group_label_font_weight': 'normal',
              'box_mean_diamonds': False,
              'box_mean_diamonds_alpha': 1,
              'box_mean_diamonds_edge_color': '#00ff00',
              'box_mean_diamonds_edge_style': '-',
              'box_mean_diamonds_edge_width': 0.7,
              'box_mean_diamonds_fill_color': None,
              'box_mean_diamonds_width': 0.8,
              'box_stat_line': 'mean',
              'box_stat_line_color': '#666666',
              'box_stat_line_style': '-',
              'box_stat_line_width': 1,
              'box_violin': False,
              'cbar_size': 30,
              'dpi': 100,
              'fig_edge_color': '#ffffff',
              'fig_fill_color': '#ffffff',
              'grid_major_color': '#b9b9b9',
              'grid_major_style': '-',
              'grid_major_width': 0.9,
              'grid_minor_color': '#cccccc',
              'grid_minor_style': '-',
              'grid_minor_width': 0.5,
              'hist_align': 'mid',
              'hist_bins': 20,
              'hist_cumulative': False,
              'hist_horizonatl': False,
              'hist_kde': False,
              'hist_normalize': False,
              'hist_rwidth': None,
              'hist_type': 'bar',
              'label_color': 'k',
              'label_font_size': 14,
              'label_style': 'italic',
              'label_weight': 'bold',
              'label_rc_edge_color': '#ffffff',
              'label_rc_fill_color': '#888888',
              'label_rc_font_size': 14,
              'label_rc_text_color': '#ffffff',
              'label_rc_text_style': 'normal',
              'label_rc_text_weight': 'bold',
              'label_rc_size': 30,
              'legend_fill_color': '#ffffff',
              'legend_edge_color': '#ffffff',
              'legend_font_size': 12,
              'legend_points': 1,
              'legend_title': '',
              'lines_width': 1,
              'marker_size': 6,
              'marker_type': 'o',
              'pie_percents': None,
              'pie_counter_clock': False,
              'pie_edge_color': '#ffffff',
              'pie_edge_style': '-',
              'pie_label_distance': 1.05,
              'pie_percents_distance': 0.6,
              'pie_radius': 1,
              'pie_rotate_labels': False,
              'pie_shadow': False,
              'pie_start_angle': 90,
              'tick_labels_font_size': 12,
              'tick_labels_color': '#000000',
              'ticks_major_color': '#aaaaaa',
              'ticks_minor_color': '#bbbbbb',
              'ticks_major_length': 6,
              'ticks_major_width': 1.8,
              'title_fill_color': '#ffffff',
              'title_edge_color': '#ffffff',
              'title_font_color': '#333333',
              'title_font_size': 18,
              'title_font_weight': 'bold',
              'title_wrap_edge_color': '#5f5f5f',
              'title_wrap_fill_color': '#5f5f5f',
              'title_wrap_font_size': 16,
              'title_wrap_font_color': '#ffffff',
              'title_wrap_font_style': 'normal',
              'title_wrap_font_weight': 'bold',
              'title_wrap_size': 30,
              'violin_box_color': '#555555',
              'violin_box_on': True,
              'violin_edge_color': '#aaaaaa',
              'violin_markers': False,
              'violin_median_color': '#ffffff',
              'violin_median_marker': 'o',
              'violin_median_size': 2,
              'violin_whisker_color': '#555555',
              'violin_whisker_style': '-',
              'violin_whisker_width': 1.5,
              }

#########################################################
# New color schemes
#########################################################

# colors = []

####################################################
# Default marker scheme
####################################################

# markers = []

####################################################
# Matplotlib default overrides
####################################################
rcParams = {'font.cursive': ['Apple Chancery',
                             'Textile',
                             'Zapf Chancery',
                             'Sand',
                             'cursive'],
            'font.fantasy': ['Comic Sans MS',
                             'Chicago',
                             'Charcoal',
                             'ImpactWestern',
                             'fantasy'],
            'font.monospace': ['Bitstream Vera Sans Mono',
                               'DejaVu Sans Mono',
                               'Andale Mono',
                               'Nimbus Mono L',
                               'Courier New',
                               'Courier',
                               'Fixed',
                               'Terminal',
                               'monospace'],
            'font.sans-serif': ['Arial',
                                'Bitstream Vera Sans',
                                'Lucida Grande',
                                'Verdana',
                                'Geneva',
                                'Lucid',
                                'Helvetica',
                                'Avant Garde',
                                'sans-serif'],
            'font.serif': ['Bitstream Vera Serif',
                           'DejaVu Serif',
                           'New Century Schoolbook',
                           'Century Schoolbook L',
                           'Utopia',
                           'ITC Bookman',
                           'Bookman',
                           'Nimbus Roman No9 L',
                           'Times New Roman',
                           'Times',
                           'Palatino',
                           'Charter',
                           'serif'],
            'agg.path.chunksize': 1000,
            }
mpl.rcParams.update(rcParams)