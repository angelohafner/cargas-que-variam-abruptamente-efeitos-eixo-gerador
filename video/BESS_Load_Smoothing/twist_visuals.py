"""Large twist indicators with a common scale and MathTex numeric readouts."""
from visuals import *
from shaft_twist import GAUGE_GAIN, EVENT_WINDOW, visual_deflection


def shaft_context():
    g=VGroup()
    points=[np.array([x,2.43,0]) for x in [-1.45,0,1.45]]
    for i in range(2):
        g.add(line(points[i]+RIGHT*.16,points[i+1]-RIGHT*.16,LOAD if i==1 else MUTED,6 if i==1 else 3))
    for point,name in zip(points,['Turbine','Coupling','Generator']):
        g.add(Circle(radius=.16,color=WHITE,stroke_width=2,fill_color=PANEL,fill_opacity=1).move_to(point),
              label(name,17,MUTED).move_to(point+DOWN*.36))
    g.add(math(r'\theta_2-\theta_3',23,LOAD).move_to([3.2,2.43,0]))
    return g


def twist_gauge(t,delta,tracker,center,color):
    """Angles are amplified only geometrically; all tick/readout values remain physical."""
    c=np.array(center,dtype=float); radius=1.03
    ring=Circle(radius=radius,color=GRID,stroke_width=2,fill_color=PANEL,fill_opacity=.8).move_to(c)
    static=VGroup(ring)
    zero=c+UP*radius*.94
    static.add(DashedLine(c,zero,color=MUTED,stroke_width=1,dash_length=.05))

    def position(value,r=radius*.88):
        angle=PI/2-float(visual_deflection(value))
        return c+r*np.array([np.cos(angle),np.sin(angle),0])

    for value,text in [(0.,'0'),(.0025,'2.5'),(.005,'5')]:
        static.add(line(position(value,radius*.96),position(value,radius*1.07),MUTED,2))
        static.add(math(text,18,MUTED).move_to(position(value,radius*1.25)))

    sector=AnnularSector(inner_radius=.12,outer_radius=radius*.91,start_angle=PI/2,
                         angle=-1e-7,color=color,fill_opacity=.17,stroke_width=0).shift(c)
    arc=Arc(radius=radius*.91,start_angle=PI/2,angle=-1e-7,arc_center=c,color=color,stroke_width=5)
    lags=np.linspace(.085,.012,7)
    ghosts=VGroup(*[line(c,zero,color,2).set_opacity(.07+i*.035) for i in range(len(lags))])
    pointer=Line(c,zero,color=color,stroke_width=5)
    tip=Dot(zero,radius=.04,color=WHITE)
    hub=Dot(c,radius=.065,color=WHITE)
    peak=Dot(zero,radius=.035,color=WHITE)
    value=DecimalNumber(0.,num_decimal_places=2,mob_class=MathTex,group_with_commas=False,
                        font_size=29,color=color,edge_to_fix=RIGHT)
    unit=math(r'\mathrm{mrad}',25,color)
    reading=VGroup(value,unit).arrange(RIGHT,buff=.11).move_to(c+DOWN*1.35)
    MATH_INVENTORY.update(list('0123456789')+['.','-'])
    MATH_INVENTORY.add(r'\Delta\theta_{23}\;\mathrm{(mrad)}')
    group=VGroup(static,sector,ghosts,arc,pointer,tip,hub,peak,reading)
    event=(t>=EVENT_WINDOW[0])&(t<=EVENT_WINDOW[1])
    peak_times=t[event]; peak_values=np.maximum.accumulate(np.maximum(delta[event],0.))
    last=[None]

    def update(_):
        now=tracker.get_value()
        v=float(np.interp(now,t,delta))
        angle=-float(visual_deflection(v))
        safe_angle=angle if abs(angle)>1e-7 else 1e-7
        sector.become(AnnularSector(inner_radius=.12,outer_radius=radius*.91,start_angle=PI/2,
                                    angle=safe_angle,color=color,fill_opacity=.17,stroke_width=0).shift(c))
        arc.become(Arc(radius=radius*.91,start_angle=PI/2,angle=safe_angle,arc_center=c,color=color,stroke_width=5))
        for ghost,lag in zip(ghosts,lags):
            past=max(EVENT_WINDOW[0],now-lag)
            ghost.put_start_and_end_on(c,position(float(np.interp(past,t,delta))))
        end=position(v)
        pointer.put_start_and_end_on(c,end);tip.move_to(end)
        k=max(0,min(len(peak_times)-1,np.searchsorted(peak_times,now,side='right')-1))
        peak.move_to(position(peak_values[k],radius*.91))
        rounded=round(v*1000,2)
        if rounded==0:rounded=0.
        if rounded!=last[0]:value.set_value(rounded);last[0]=rounded
    group.add_updater(update)
    update(group)
    return group
