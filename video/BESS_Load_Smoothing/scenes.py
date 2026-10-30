"""English animation of verified PSCAD generator/BESS comparison data."""
from visuals import *
from shaft_twist import load_twist_data, GAUGE_GAIN
from twist_visuals import shaft_context, twist_gauge


class Applications(FilmScene):
    def construct(self):
        self.heading('When loads change abruptly')
        cards=VGroup()
        icons=[]
        waves=[]
        positions=[-5.05,-1.68,1.68,5.05]
        titles=['Motors','Rolling mills','Cranes','Pulsed loads']
        for i,x in enumerate(positions):
            panel=RoundedRectangle(width=3.1,height=3.9,corner_radius=.2,
                stroke_color=GRID,stroke_width=1.2,fill_color=PANEL,fill_opacity=.7).move_to([x,.15,0])
            name=label(titles[i],25).move_to([x,-1.35,0])
            cards.add(panel,name)
            if i==0:
                ring=Circle(radius=.57,color=LOAD,stroke_width=3).move_to([x,.8,0])
                spokes=VGroup(*[Line([x,.8,0],[x+.44*np.cos(a),.8+.44*np.sin(a),0],color=LOAD,stroke_width=3) for a in np.arange(0,TAU,TAU/3)])
                icon=VGroup(ring,spokes,line([x+.57,.8,0],[x+1,.8,0],LOAD,4))
            elif i==1:
                icon=VGroup(*[Circle(radius=.35,color=LOAD,stroke_width=3).move_to([x,.8+dy,0]) for dy in [-.42,.42]],
                    line([x-1,.8,0],[x+1,.8,0],LOAD,6))
            elif i==2:
                icon=VGroup(line([x-.8,.2,0],[x-.8,1.5,0],LOAD,4),line([x-.8,1.5,0],[x+.8,1.5,0],LOAD,4),
                    line([x+.4,1.5,0],[x+.4,.65,0],LOAD,2),Rectangle(width=.65,height=.4,color=LOAD,fill_color=LOAD,fill_opacity=.15).move_to([x+.4,.42,0]))
            else:
                icon=VMobject(color=LOAD,stroke_width=4).set_points_as_corners([[x-.9,.35,0],[x-.45,.35,0],[x-.45,1.25,0],[x+.1,1.25,0],[x+.1,.35,0],[x+.55,.35,0],[x+.55,1.25,0],[x+.9,1.25,0]])
            icons.append(icon)
            tt=np.linspace(0,1,61)
            yy=[np.where(tt<.35,.1,.6), .2+.35*(np.sin(tt*4*np.pi)>0),
                np.where((tt>.25)&(tt<.65),.6,.1), .15+.45*(np.sin(tt*8*np.pi)>0)][i]
            waves.append(VMobject(color=BESS,stroke_width=2).set_points_as_corners([[x-1+2*a,-.7+b*.6,0] for a,b in zip(tt,yy)]))
        self.play(FadeIn(cards,shift=UP*.15),LaggedStart(*[Create(a) for a in icons],lag_ratio=.15),run_time=2)
        self.play(LaggedStart(*[Create(w) for w in waves],lag_ratio=.15),run_time=2)
        causal=math(r'\Delta P_L\;\longrightarrow\;\Delta T_e',42).move_to([0,-2.65,0])
        self.play(Write(causal),run_time=1.5)
        self.footer('Illustrative applications')
        self.play(Rotate(icons[0][1],angle=TAU,about_point=[positions[0],.8,0]),
                  Indicate(icons[1],color=WHITE),Indicate(icons[2],color=WHITE),Indicate(icons[3],color=WHITE),run_time=4)
        self.finish(2)


class ParallelBuffer(FilmScene):
    def construct(self):
        self.heading('A parallel energy buffer')
        base,branch,labels=circuit()
        self.play(Create(base),FadeIn(labels[:2]),run_time=2)
        equation=math(r'P_G+P_B=P_L+P_{\mathrm{loss}}',34).move_to([0,-3.02,0])
        self.play(Create(branch),FadeIn(labels[2]),Write(equation),run_time=2)
        self.footer('Single-line equivalent')
        up=Arrow([.5,-1.5,0],[.5,.45,0],buff=0,color=BESS,stroke_width=6)
        demand=Arrow([1.3,1.12,0],[3.6,1.12,0],buff=0,color=LOAD,stroke_width=7)
        supply=Arrow([-3.6,1.12,0],[-1.3,1.12,0],buff=0,color=BASE,stroke_width=4)
        state=tag('Discharge',BESS,25).move_to([2,-.6,0])
        sign=math(r'\Delta P_L>0\qquad P_B>0',31,LOAD).move_to([0,2.24,0])
        self.play(GrowArrow(up),GrowArrow(demand),GrowArrow(supply),FadeIn(state),Write(sign),run_time=1.4)
        balls=VGroup(*[Dot(color=BESS,radius=.07) for _ in range(3)])
        self.add(balls)
        for _ in range(2):
            self.play(LaggedStart(*[MoveAlongPath(b,Line([0,-1.3,0],[0,.7,0]),rate_func=linear) for b in balls],lag_ratio=.35),run_time=2)
        self.remove(balls)
        down=Arrow([.5,.45,0],[.5,-1.5,0],buff=0,color=BESS,stroke_width=6)
        charge=tag('Charge',BESS,25).move_to(state)
        negative=math(r'\Delta P_L<0\qquad P_B<0',31,LOAD).move_to(sign)
        small=Arrow([1.3,1.12,0],[3.6,1.12,0],buff=0,color=LOAD,stroke_width=3)
        self.play(ReplacementTransform(up,down),ReplacementTransform(state,charge),
                  ReplacementTransform(sign,negative),ReplacementTransform(demand,small),run_time=1.5)
        balls=VGroup(*[Dot(color=BESS,radius=.07) for _ in range(3)])
        self.add(balls)
        for _ in range(2):
            self.play(LaggedStart(*[MoveAlongPath(b,Line([0,.7,0],[0,-1.3,0]),rate_func=linear) for b in balls],lag_ratio=.35),run_time=2)
        self.remove(balls)
        self.finish(2)


class PowerComparison(FilmScene):
    def construct(self):
        d=Dataset()
        self.heading('Same demand. Smoother generation.')
        self.add(legend_pair(2.42))
        definitions=[('Pload_MW',1.36,[200,550,125],[250,500],r'\substack{P_L\\(\mathrm{MW})}'),
                     ('Pgen_MW',-.35,[200,550,125],[250,500],r'\substack{P_G\\(\mathrm{MW})}'),
                     ('Pbess_MW',-2.06,[-250,250,250],[-250,0,250],r'\substack{P_B\\(\mathrm{MW})}')]
        curves=VGroup(); axes=[]
        for key,y,yr,yt,unit in definitions:
            ax,group=plot_axes([1.5,30,5],yr,center=(.55,y,0),height=1.1,width=10.6,
                xticks=[5,10,15,20,25,30] if key=='Pbess_MW' else [],yticks=yt,unit=unit)
            self.add(group)
            axes.append((ax,key,yr))
            if key=='Pload_MW':
                curves.add(trace(ax,d.array('with','time'),d.array('with','Pload_command_MW'),1.5,30,LOAD,width=1.1))
            for case,color in [('without',BASE),('with',BESS)]:
                if key=='Pbess_MW' and case=='without':
                    continue
                curves.add(trace(ax,d.array(case,'time'),d.array(case,key),1.5,30,color,width=2.2))
        self.play(FadeIn(curves),run_time=1.5)
        clock=ValueTracker(1.5)
        cursors=VGroup(*[moving_cursor(ax,clock,[1.5,30],yr) for ax,key,yr in axes])
        dots=VGroup(*[dot_on(ax,d,case,key,clock,color) for ax,key,yr in axes for case,color in [('without',BASE),('with',BESS)] if key!='Pbess_MW' or case=='with'])
        self.add(cursors,dots)
        time_label=math(r't\;(\mathrm{s})',23,MUTED).move_to([0,-3.15,0])
        self.add(time_label)
        footer=VGroup(label('PSCAD  |  Power average',18,MUTED),math(r'1/60\,\mathrm{s}',21,MUTED)).arrange(RIGHT,buff=.15).move_to([0,-3.56,0])
        self.add(footer)
        self.play(clock.animate.set_value(30),run_time=17,rate_func=linear)
        for obj in [cursors,dots]:obj.clear_updaters(recursive=True)
        self.finish(3)


class ShaftMechanism(FilmScene):
    def construct(self):
        data=load_twist_data(HERE/'data/display.npz')
        self.heading('Twist at the generator shaft')
        self.add(shaft_context())
        clock=ValueTracker(1.8)
        gauges=VGroup()
        for case,x,color,name in [('without',-3.4,BASE,'Without BESS'),('with',3.4,BESS,'With BESS')]:
            self.add(label(name,29,color).move_to([x,1.83,0]))
            d=data[case]
            gauges.add(twist_gauge(d['time'],d['delta'],clock,(x,.15,0),color))
        self.add(gauges)
        definition=math(r'\Delta\theta_{23}=\Delta(\theta_2-\theta_3)',26).move_to([0,.91,0])
        scale=VGroup(label('Visual scale',19,MUTED),math(rf'\times{GAUGE_GAIN:g}',31,WHITE)).arrange(DOWN,buff=.13).move_to([0,-.54,0])
        self.add(definition,scale)
        ax,ag=plot_axes([1.8,2.8,.2],[.22,.52,.1],center=(.55,-2.15,0),width=10.6,height=1.05,
            xticks=[1.8,2,2.2,2.4,2.6,2.8],yticks=[.25,.5],unit=r'\substack{T_{23}\\(\mathrm{pu})}')
        self.add(ag,line(ax.c2p(2,.22),ax.c2p(2,.52),LOAD,1.5))
        curves=VGroup(*[trace(ax,data[case]['time'],data[case]['torque'],1.8,2.8,color,step=.0005,width=2.3)
                       for case,color in [('without',BASE),('with',BESS)]])
        self.play(FadeIn(curves),run_time=1.3)
        movers=VGroup(moving_cursor(ax,clock,[1.8,2.8],[.22,.52]))
        for case,color in [('without',BASE),('with',BESS)]:
            d=data[case]
            movers.add(always_redraw(lambda d=d,color=color: Dot(ax.c2p(clock.get_value(),
                float(np.interp(clock.get_value(),d['time'],d['torque']))),radius=.047,color=color)))
        self.add(movers,math(r't\;(\mathrm{s})',22,MUTED).move_to([0,-3.16,0]))
        self.footer('Slow motion  |  Amplitudes are step-size sensitive')
        self.wait(1)
        self.play(clock.animate.set_value(2.0),run_time=3.6,rate_func=linear)
        step=tag('Load step',LOAD,21).move_to([0,.24,0])
        self.play(FadeIn(step),run_time=.6)
        self.play(clock.animate.set_value(2.8),run_time=14.4,rate_func=linear)
        gauges.clear_updaters(recursive=True);movers.clear_updaters(recursive=True)
        self.finish(3)


class MeasuredBenefits(FilmScene):
    def construct(self):
        d=Dataset(); m=d.metrics
        self.heading('What the simulation demonstrates')
        self.add(legend_pair(2.38))
        card_elements=VGroup()
        for cx,key,title,unit in [(-3.35,'std_MW',r'\sigma(P_G)',r'\mathrm{MW}'),
                                  (3.35,'max_ramp_MW_s',r'\max\left|\Delta P_G/\Delta t\right|',r'\mathrm{MW/s}')]:
            a=m['without']['Pgen_MW'][key]; b=m['with']['Pgen_MW'][key]
            pc=m['reductions_percent']['Pgen_MW'][key]
            box=RoundedRectangle(width=6,height=4.45,corner_radius=.2,stroke_color=GRID,stroke_width=1,fill_color=PANEL,fill_opacity=.65).move_to([cx,-.15,0])
            card_elements.add(box,math(title,31).move_to([cx,1.58,0]))
            left=cx-2.1
            for val,y,col in [(a,.72,BASE),(b,-.1,BESS)]:
                bar=Rectangle(width=4.1*val/a,height=.19,color=col,fill_color=col,fill_opacity=1,stroke_width=0)
                bar.move_to([left+bar.width/2,y,0])
                card_elements.add(bar,math(f'{val:.1f}'+r'\;'+unit,27,col).move_to([cx,y+.36,0]))
            card_elements.add(math(rf'\downarrow\;{pc:.2f}\%',45,BESS).move_to([cx,-1.19,0]))
        self.play(FadeIn(card_elements,shift=UP*.15),run_time=2)
        note=VGroup(math(r't\in[1.5,30]~\mathrm{s}',23,MUTED),math(r'\Delta t=100~\mathrm{ms}',23,MUTED)).arrange(RIGHT,buff=1).move_to([0,-2.85,0])
        self.add(note)
        self.footer('Generator-terminal power  |  Same load command')
        self.finish(9)


SCENE_ORDER=['Applications','ParallelBuffer','PowerComparison','ShaftMechanism',
             'MeasuredBenefits']
