from bokeh.plotting import figure
from bokeh.models import (ColumnDataSource,
                          LinearColorMapper,
                          CustomJS,
                          HoverTool,
                          Rect)
from bokeh.layouts import layout


def makelayout(PADataFrame, MRKDataFrame, imgs):
    """Makes a bokeh layout from input-data and the list of thumbnails"""

    # The Data Source from the imported csv stub info
    PAsource = ColumnDataSource(PADataFrame)

    # Add the image files
    PAsource.add(imgs, 'imgs')

    # The Data source of the markers
    MRKsource = ColumnDataSource(MRKDataFrame)

    # Definition of the color mapper with UM content as color coding
    color_mapper = LinearColorMapper(palette="Viridis256",
                                     nan_color="Firebrick",
                                     low=0, high=1e2)

    # Definition of a linear interpolator to map the circle sizes
    from bokeh.models import LinearInterpolator

    size_mapper = LinearInterpolator(
        x=[PADataFrame.AvgDiam.min(), PADataFrame.AvgDiam.max()],
        y=[0.1, 0.3]
    )

    # Global Definitions of the plots (sizes, scalings, etc)

    fig_width = 300
    fig_height = 300
    circle_size = 6

    MRK_OPTIONS = dict(size=10,
                       color='LightSlateGrey',
                       line_width=2)

    SUBSTRATE_OPTIONS = dict(x=0, y=0,
                             radius=12.5,
                             fill_alpha=0.2,
                             fill_color='Ivory',
                             line_color='black')

    renderers = {}

    TOOLS = "pan,wheel_zoom,box_select,lasso_select,reset,help"

    CBsource = ColumnDataSource({'x': [], 'y': [], 'width': [], 'height': []})

    jscode = """
        var data = source.data;
        var start = cb_obj.start;
        var end = cb_obj.end;
        data['%s'] = [start + (end - start) / 2];
        data['%s'] = [end - start];
        source.trigger('change');
    """

    #      TOP LEFT PLOT

    top_left = figure(tools=TOOLS,
                      active_scroll="wheel_zoom",
                      width=fig_width,
                      height=fig_height,
                      title='Particle Positions on Substrate',
                      x_range=[-13, 13], y_range=[-13, 13])

    renderers['top_left'] = top_left.circle(
        'StgX', 'StgY',
        fill_color={
            'field': 'UM',
            'transform': color_mapper
        },
        fill_alpha=0.5,
        radius={
            'field': 'AvgDiam',
            'transform': size_mapper
        },
        hover_color='red',
        source=PAsource)

    # Add the substrate shape

    top_left.circle(**SUBSTRATE_OPTIONS)

    # Add the markers

    renderers['MRKtop_left'] = top_left.cross(
        'StgX', 'StgY',
        source=MRKsource,
        **MRK_OPTIONS)

    # JS Callback for range update

    top_left.x_range.callback = CustomJS(
            args=dict(source=CBsource), code=jscode % ('x', 'width'))
    top_left.y_range.callback = CustomJS(
            args=dict(source=CBsource), code=jscode % ('y', 'height'))

    # TOP RIGHT PLOT #

    top_right = figure(tools=TOOLS,
                       width=fig_width, height=fig_height,
                       toolbar_location=None,
                       title='Substrate Overview',
                       x_range=[-13, 13], y_range=[-13, 13])

    rect = Rect(x='x', y='y',
                width='width', height='height',
                fill_alpha=0.3,
                line_alpha=0,
                fill_color='Teal')

    top_right.add_glyph(CBsource, rect)

    renderers['top_right'] = top_right.circle(
        'StgX', 'StgY',
        fill_color={
            'field': 'UM',
            'transform': color_mapper
        },
        fill_alpha=0.5,
        radius={
            'field': 'AvgDiam',
            'transform': size_mapper
        },
        hover_color='red',
        source=PAsource)

    # Add the markers
    renderers['MRKtop_right'] = top_right.cross(
        'StgX', 'StgY',
        source=MRKsource,
        **MRK_OPTIONS)

    # Add the substrate shape
    top_right.circle(**SUBSTRATE_OPTIONS)

    # create bottom-left plot
    bottom_left = figure(tools=TOOLS,
                         active_scroll="wheel_zoom",
                         width=fig_width,
                         height=fig_height,
                         title='Content vs Particle Size')

    renderers['bottom_left'] = bottom_left.circle(
        'AvgDiam', 'UM',
        size=circle_size,
        alpha=0.5,
        hover_color='red',
        source=PAsource)

    # create bottom-right
    bottom_right = figure(tools=TOOLS,
                          active_scroll="wheel_zoom",
                          width=fig_width,
                          height=fig_height,
                          title='Circularity vs Particle Size')

    renderers['bottom_right'] = bottom_right.circle(
        'AvgDiam', 'Circ',
        fill_color={
            'field': 'UM',
            'transform': color_mapper},
        fill_alpha=0.5,
        size=circle_size,
        alpha=0.5,
        hover_color='red',
        source=PAsource)

    # Axis labels
    top_left.xaxis.axis_label = "x / mm"
    top_left.yaxis.axis_label = "y / mm"

    top_right.xaxis.axis_label = "x / mm"
    top_right.yaxis.axis_label = "y / mm"

    bottom_left.xaxis.axis_label = "Average Diameter / µm"
    bottom_left.yaxis.axis_label = "Content / (wt %)"

    # Hover configuration

    PA_hover = HoverTool(
        tooltips="""
           <div>
                 <div>
                     <img
                         src="@imgs" alt="@imgs"
                         style="float: left; margin: 0px 15px 15px 0px;"
                         border="2"
                     ></img>
                 </div>
                 <div>
                     <span style="font-size: 15px;
                            font-weight: bold;"># @Part</span>
                 </div>
                 <div>
                     <span style="font-size: 12px;">
                     Field: @Field<br>
                     (x,y): (@StgX, @StgY) / mm<br>
                     UM: @UM / wt. %<br>
                     AvgDiam: @AvgDiam / microm<br>
                     </span>
                 </div>
             </div>
            """,
        renderers=[renderers['top_left']],
        point_policy='snap_to_data',
        show_arrow=True
    )

    MRK_hover = HoverTool(
        tooltips=[("Marker", "@MarkerType"),
                  ("(x,y)", "(@StgX, @StgY)")],
        renderers=[renderers['MRKtop_right']],
        point_policy='snap_to_data',
        show_arrow=True)

    left_hover = HoverTool(
        tooltips="""
           <div>
                 <div>
                     <img src="@imgs" alt="@imgs"
                          style="width = 50px"></img><br>
                 </div>
                 <div>
                     <span style="font-size: 15px; font-weight: bold;
                           "># @Part</span>
                 </div>
                 <div>
                     <span style="font-size: 12px;">
                     Field: @Field<br>
                     (x,y): (@StgX, @StgY) / mm<br>
                     UM: @UM / wt. %<br>
                     AvgDiam: @AvgDiam / microm<br>
                     </span>
                 </div>
             </div>
            """,
        renderers=[renderers['bottom_left']],
        point_policy='snap_to_data',
        show_arrow=True
    )

    right_hover = HoverTool(
        tooltips="""
           <div>
                 <div>
                     <img src="@imgs" alt="@imgs"
                          style="width = 50px"></img><br>
                 </div>
                 <div>
                     <span style="font-size: 15px; font-weight: bold;
                           "># @Part</span>
                 </div>
                 <div>
                     <span style="font-size: 12px;">
                     Field: @Field<br>
                     (x,y): (@StgX, @StgY) / mm<br>
                     UM: @UM / wt. %<br>
                     AvgDiam: @AvgDiam / microm<br>
                     </span>
                 </div>
             </div>
            """,
        renderers=[renderers['bottom_right']],
        point_policy='snap_to_data',
        show_arrow=True
    )

    # add specialy configured tool
    top_left.add_tools(PA_hover)
    top_right.add_tools(MRK_hover)
    bottom_left.add_tools(left_hover)
    bottom_right.add_tools(right_hover)

    figures = [top_right, top_left, bottom_left]
    for plot in figures:
        plot.title.align = 'center'
        plot.title.text_font_style = 'normal'
        plot.xaxis.axis_label_text_font_style = 'normal'
        plot.yaxis.axis_label_text_font_style = 'normal'
        plot.outline_line_color = "black"

    return layout([[top_left, top_right], [bottom_left]])
