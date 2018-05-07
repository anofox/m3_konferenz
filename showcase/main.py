from os.path import dirname, join
from math import ceil

import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Slider, Div
from bokeh.models.mappers import LinearColorMapper
from bokeh.plotting import figure
from bokeh.palettes import OrRd

import audio
from audio import MAX_FREQ, TIMESLICE, NUM_BINS, SUBS_GAIN
from waterfall import WaterfallRenderer

MAX_FREQ_KHZ = MAX_FREQ*0.001
NUM_GRAMS = 800
GRAM_LENGTH = 512
TILE_WIDTH = 200
EQ_CLAMP = 20

PALETTE = ['#081d58', '#253494', '#225ea8', '#1d91c0', '#41b6c4', '#7fcdbb', '#c7e9b4', '#edf8b1', '#ffffd9']
ANO_PALETTE = ["#eaeaea", ] + list(reversed(OrRd[6]))

PLOTARGS = dict(tools="", toolbar_location=None, outline_line_color='#595959')

filename = join(dirname(__file__), "title.html")
title = Div(text=open(filename).read(), render_as_text=False, width=1300, height=50)

waterfall_renderer = WaterfallRenderer(palette=PALETTE, num_grams=NUM_GRAMS,
                                       gram_length=GRAM_LENGTH, tile_width=TILE_WIDTH)
waterfall_plot = figure(plot_width=1300, plot_height=300, min_border_left=80,
                        x_range=[0, NUM_GRAMS], y_range=[0, MAX_FREQ_KHZ], **PLOTARGS)
waterfall_plot.grid.grid_line_color = None
waterfall_plot.background_fill_color = "#024768"
waterfall_plot.renderers.append(waterfall_renderer)


lr_source = ColumnDataSource(data=dict(t=[], y=[]))
lr_plot = figure(plot_width=850, plot_height=220, title="Low rank",
                 x_range=[0, TIMESLICE], y_range=[-0.8, 0.8], **PLOTARGS)
lr_plot.background_fill_color = "#eaeaea"
lr_plot.line(x="t", y="y", line_color="#024768", source=lr_source)

sp_source = ColumnDataSource(data=dict(t=[], y=[]))
sp_plot = figure(plot_width=850, plot_height=220, title="Sparse",
                 x_range=[0, TIMESLICE], y_range=[-0.8, 0.8], **PLOTARGS)
sp_plot.background_fill_color = "#eaeaea"
sp_plot.line(x="t", y="y", line_color="#024768", source=sp_source)


eq_angle = 2*np.pi/NUM_BINS
eq_range = np.arange(EQ_CLAMP, dtype=np.float64)
eq_data = dict(
    inner=np.tile(eq_range+2, NUM_BINS),
    outer=np.tile(eq_range+2.95, NUM_BINS),
    start=np.hstack([np.ones_like(eq_range)*eq_angle*(i+0.05) for i in range(NUM_BINS)]),
    end=np.hstack([np.ones_like(eq_range)*eq_angle*(i+0.95) for i in range(NUM_BINS)]),
    alpha=np.tile(np.zeros_like(eq_range), NUM_BINS),
)
eq_source = ColumnDataSource(data=eq_data)
eq = figure(plot_width=450, plot_height=442,
            x_axis_type=None, y_axis_type=None,
            x_range=[-20, 20], y_range=[-20, 20], **PLOTARGS)
eq.background_fill_color = "#eaeaea"
eq.annular_wedge(x=0, y=0, fill_color="#024768", fill_alpha="alpha", line_color=None,
                 inner_radius="inner", outer_radius="outer", start_angle="start", end_angle="end",
                 source=eq_source)

freq = Slider(start=1, end=MAX_FREQ, value=MAX_FREQ, step=1, title="Frequency")

gain = Slider(start=1, end=20, value=1, step=1, title="Gain")


def map_color(val):
    bins = np.linspace(0, 0.5, len(ANO_PALETTE))
    idx = np.digitize(val, bins)
    return ANO_PALETTE[np.maximum(idx - 1, 0)]


def update():
    signal, spectrum, bins, low_rank, sparse = audio.data['values']
    SUBS_GAIN = gain.value

    pwr_bg = np.sum(low_rank * low_rank)
    pwr_fg = np.sum(sparse * sparse)
    print("%2.2f / %2.2f = %2.2f" % (pwr_fg, pwr_bg, pwr_fg / (pwr_bg + 1e-10)))
    ano_color = map_color(pwr_fg / (pwr_bg + 1e-10))

    # seems to be a problem with Array property, using List for now
    waterfall_renderer.latest = spectrum.tolist()
    waterfall_plot.y_range.end = freq.value * 0.001

    if len(signal) == len(lr_source.data['y']):
        lr_source.data['y'] = low_rank
    else:
        t = np.linspace(0, TIMESLICE, len(signal))
        lr_source.data = dict(t=t, y=low_rank)
    lr_plot.background_fill_color = ano_color

    if len(signal) == len(sp_source.data['y']):
        sp_source.data['y'] = sparse
    else:
        t = np.linspace(0, TIMESLICE, len(signal))
        sp_source.data = dict(t=t, y=sparse)
    sp_plot.background_fill_color = ano_color

    alphas = []
    for x in bins:
        a = np.zeros_like(eq_range)
        N = int(ceil(x))
        a[:N] = (1 - eq_range[:N]*0.05)
        alphas.append(a)
    eq_source.data['alpha'] = np.hstack(alphas)
    eq.background_fill_color = ano_color



curdoc().add_periodic_callback(update, 150)
controls = column(row(widgetbox(gain), widgetbox(freq)))
plots = column(waterfall_plot, row(column(lr_plot, sp_plot), eq))

curdoc().title = "Zoi Realtime Anomaly Detection Showcase"
curdoc().add_root(title)
curdoc().add_root(plots)
curdoc().add_root(controls)
