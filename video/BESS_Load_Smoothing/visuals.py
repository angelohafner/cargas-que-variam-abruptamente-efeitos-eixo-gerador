"""Shared Manim drawing helpers. Numeric content must pass through MathTex."""
from pathlib import Path
import json
import re
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
BG = '#0B1425'
PANEL = '#101E34'
WHITE = '#F1F5FA'
MUTED = '#91A6C2'
GRID = '#29405A'
BASE = '#FF8066'
BESS = '#3EDCC3'
LOAD = '#FFCE75'
SHAFT = '#A7B6FF'
config.background_color = BG
config.max_files_cached = 500

TEXT_INVENTORY = set()
MATH_INVENTORY = set()


def label(text, size=28, color=WHITE):
    if re.search(r'\d', text):
        raise ValueError('Numerals belong in MathTex: '+text)
    TEXT_INVENTORY.add(text)
    return Text(text, font='Segoe UI', font_size=size, color=color)


def math(text, size=30, color=WHITE):
    MATH_INVENTORY.add(text)
    return MathTex(text, font_size=size, color=color)


def symbol(name, width=1.6, color=WHITE):
    return SVGMobject(str(HERE/'assets'/(name+'.svg'))).set_color(color).set_width(width)


def line(a,b,color=GRID,width=2):
    return Line(np.array(a,dtype=float),np.array(b,dtype=float),color=color,stroke_width=width)


def tag(text, color=BESS, size=22):
    t=label(text,size,color)
    box=RoundedRectangle(width=t.width+.36,height=.42,corner_radius=.1,
                         stroke_color=color,stroke_width=1,fill_color=BG,fill_opacity=1)
    return VGroup(box,t)


class FilmScene(Scene):
    def heading(self,text):
        title=label(text,44).move_to([0,3.3,0])
        rule=line([-6.4,2.82,0],[6.4,2.82,0],GRID,1)
        self.add(title,rule)
        return title

    def footer(self,text):
        f=label(text,19,MUTED).move_to([0,-3.64,0])
        self.add(f)
        return f

    def finish(self, hold=1.5):
        self.wait(hold)
        # Keep the last composed frame as the representative poster.
        out=HERE/'evidence'/'scene_posters'
        out.mkdir(parents=True,exist_ok=True)
        self.camera.capture_mobjects(self.mobjects)
        self.camera.get_image().save(out/(type(self).__name__+'.png'))
        inv=HERE/'evidence'/'inventories'
        inv.mkdir(exist_ok=True)
        (inv/(type(self).__name__+'.json')).write_text(json.dumps({'text':sorted(TEXT_INVENTORY),'math':sorted(MATH_INVENTORY)},indent=2),encoding='utf-8')
        self.play(*[FadeOut(m) for m in list(self.mobjects)],run_time=.7)


class Dataset:
    def __init__(self):
        self.data=np.load(HERE/'data/display.npz')
        self.metrics=json.loads((HERE/'data/metrics.json').read_text())

    def array(self,case,key):
        return self.data[case+'__'+key]

    def value(self,case,key,t):
        return float(np.interp(t,self.array(case,'time'),self.array(case,key)))


def plot_axes(xrange,yrange,center=(.4,0,0),width=10.6,height=1.4,xticks=(),yticks=(),unit=''):
    ax=Axes(x_range=xrange,y_range=yrange,x_length=width,y_length=height,
            axis_config={'color':GRID,'stroke_width':1.4,'include_tip':False,'include_ticks':False},
            tips=False).move_to(center)
    extras=VGroup()
    for y in yticks:
        extras.add(line(ax.c2p(xrange[0],y),ax.c2p(xrange[1],y),GRID,.8))
        extras.add(math(f'{y:g}',18,MUTED).next_to(ax.c2p(xrange[0],y),LEFT,buff=.14))
    for x in xticks:
        extras.add(math(f'{x:g}',18,MUTED).next_to(ax.c2p(x,yrange[0]),DOWN,buff=.12))
    if unit:
        extras.add(math(unit,25).next_to(ax,LEFT,buff=.65))
    return ax,VGroup(ax,extras)


def trace(ax,t,y,start,end,color,step=.008,width=2.5):
    ix=np.flatnonzero((t>=start)&(t<=end))
    stride=max(1,round(step/np.median(np.diff(t))))
    ix=ix[::stride]
    points=[ax.c2p(a,b) for a,b in zip(t[ix],y[ix])]
    if len(points)<2:
        raise ValueError('Trace is too short')
    return VMobject(color=color,stroke_width=width).set_points_as_corners(points)


def legend_pair(y=2.45):
    parts=[]
    for x,txt,col in [(-1.65,'Without BESS',BASE),(1.65,'With BESS',BESS)]:
        item=VGroup(line([0,0,0],[.43,0,0],col,4),label(txt,23,col)).arrange(RIGHT,buff=.19)
        parts.append(item.move_to([x,y,0]))
    return VGroup(*parts)


def moving_cursor(ax,tracker,xrange,yrange,color=MUTED):
    return always_redraw(lambda: line(ax.c2p(tracker.get_value(),yrange[0]),
                                     ax.c2p(tracker.get_value(),yrange[1]),color,1.2))


def dot_on(ax,data,case,key,tracker,color):
    return always_redraw(lambda: Dot(ax.c2p(tracker.get_value(),data.value(case,key,tracker.get_value())),
                                    radius=.047,color=color))


def circuit():
    gen=symbol('generator',1.9,BASE).move_to([-4.7,.7,0])
    load=symbol('load',1.9,LOAD).move_to([4.7,.7,0])
    bus=Dot([0,.7,0],radius=.08,color=WHITE)
    wires=VGroup(line(gen.get_right(),bus.get_center(),WHITE,2.6),line(bus.get_center(),load.get_left(),WHITE,2.6))
    conv=symbol('converter',.85,BESS).move_to([0,-.65,0])
    bat=symbol('battery',.55,BESS).move_to([0,-1.95,0])
    branch=VGroup(line(bus.get_center(),conv.get_top(),BESS,2.6),conv,
                  line(conv.get_bottom(),bat.get_top(),BESS,2.6),bat)
    labels=VGroup(label('Generator',25,BASE).move_to([-4.7,1.65,0]),
                  label('Load',25,LOAD).move_to([4.7,1.65,0]),
                  label('BESS',27,BESS).move_to([1.35,-1.65,0]))
    return VGroup(gen,load,wires,bus),branch,labels


def shaft_rig(data,case,tracker,center=(0,.1,0),scale=1.,gain=45.,names=True):
    c=np.array(center)
    xs=[-3.8,0,3.8]
    radius=.6*scale
    group=VGroup()
    for i in range(2):
        start=c+np.array([xs[i]*scale+radius,0,0])
        end=c+np.array([xs[i+1]*scale-radius,0,0])
        group.add(line(start,end,SHAFT,7*scale),line(start+UP*.08*scale,end+UP*.08*scale,WHITE,1))
        group.add(math(rf'T_{{{i+1}{i+2}}}',23*scale,SHAFT).move_to((start+end)/2+DOWN*.55*scale))
    h=np.array(data.metrics['shaft']['H'])
    def deviation(index,time):
        theta=np.array([data.value(case,f'Shaft_theta{j}_rad',time) for j in (1,2,3)])
        return gain*(theta[index]-np.dot(theta,h)/h.sum())
    for i,x in enumerate(xs):
        pos=c+np.array([x*scale,0,0])
        ring=Circle(radius=radius,color=BASE if case=='without' else BESS,stroke_width=3,fill_color=PANEL,fill_opacity=1).move_to(pos)
        hub=Dot(pos,radius=.09*scale,color=WHITE)
        mark=always_redraw(lambda i=i,pos=pos: line(pos,pos+radius*.85*np.array([
            np.cos(deviation(i,tracker.get_value())),np.sin(deviation(i,tracker.get_value())),0]),WHITE,3))
        group.add(ring,mark,hub)
        group.add(math(rf'\theta_{{{i+1}}}',25*scale).move_to(pos+UP*.96*scale))
        if names:
            group.add(label(['Turbine','Coupling','Generator'][i],24*scale).move_to(pos+DOWN*1.05*scale))
    return group
