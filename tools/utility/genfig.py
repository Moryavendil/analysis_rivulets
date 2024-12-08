from typing import Optional, Any, Tuple, Dict, List, Union
import numpy as np

from .. import display, throw_G2L_warning, log_error, log_warn, log_info, log_debug, log_trace, log_subtrace

########## SAVE GRAPHE
import os
import matplotlib.pyplot as plt

in_per_mm = 1 / 25.4

figw_aps:Dict[str, float] = {'simple': 86 * in_per_mm, 'wide': 140 * in_per_mm, 'double': 180 * in_per_mm,
                             'inset': 40 * in_per_mm}
figw_confort:Dict[str, float] = {'simple': 6, 'wide': 9, 'double': 12, 'inset': 4}

figw = {**figw_confort}

def activate_saveplot(activate=True, font_size=10):
    if not activate:
        deactivate_saveplot()
        return
    # use LaTeX
    plt.rcParams['text.usetex'] = True
    plt.rcParams['pgf.texsystem'] = 'pdflatex'

    # use figure size
    global figw, figw_aps
    figw = {**figw_aps}
    figwidth = figw['simple']
    figheight = figwidth / 1.618 # golden ratio
    plt.rcParams["figure.figsize"] = (figwidth, figheight)

    # have appropriate font size
    plt.rcParams.update({'font.family': 'serif', 'font.size': font_size,
                         'legend.fontsize': font_size, 'legend.handlelength': 2,
                         'axes.labelsize': font_size, 'axes.titlesize': font_size,
                         'figure.labelsize': font_size,
                         'savefig.bbox': 'tight', 'savefig.pad_inches': 0., 'savefig.transparent': True,
                         # # tight layout
                         # 'figure.subplot.hspace': 0., 'figure.subplot.wspace': 0.,
                         # # 'figure.subplot.hspace': 0.2, 'figure.subplot.wspace': 0.2,
                         # 'figure.subplot.left': 0, 'figure.subplot.right': 1.,
                         # 'figure.subplot.top': 1., 'figure.subplot.bottom': 0.,
                         # # constrained layout
                         # 'figure.constrained_layout.h_pad': 0.,
                         # 'figure.constrained_layout.w_pad': 0.,
                         })

def deactivate_saveplot(font_size=16):
    # stop using LaTeX for faster display
    plt.rcParams['text.usetex'] = False

    # use figure size
    global figw, figw_confort
    figw = {**figw_confort}
    figwidth = figw['double']
    figheight = figwidth / 1.618 # golden ratio
    plt.rcParams["figure.figsize"] = (figwidth, figheight)

    # have readable font size
    plt.rcParams.update({'font.family': 'serif', 'font.size': font_size,
                         'legend.fontsize': font_size, 'legend.handlelength': 2,
                         'axes.labelsize': font_size, 'axes.titlesize': font_size,
                         'figure.labelsize': font_size,
                         })
def tighten_graph(pad=0., w_pad=0., h_pad=0.):
    plt.tight_layout(pad=pad, w_pad=w_pad, h_pad=h_pad)
def save_graphe(graph_name, imageonly=False, **kwargs):
    figures_directory = 'figures'
    if not os.path.isdir(figures_directory):
        os.mkdir(figures_directory)
    raw_path = os.path.join(figures_directory, graph_name)
    if 'bbox_inches' not in kwargs:
        kwargs['bbox_inches'] = 'tight'
    if 'pad_inches' not in kwargs:
        kwargs['pad_inches'] = 0
    if imageonly:
        plt.savefig(raw_path + '.jpg', **kwargs)
    else:
        if 'dpi' not in kwargs:
            kwargs['dpi'] = 600
        plt.savefig(raw_path + '.png', **kwargs)
        plt.savefig(raw_path + '.pdf', **kwargs)
        plt.savefig(raw_path + '.svg', **kwargs)