#!/usr/bin/env python3
"""Procedural neon ASCII aquarium with depth, currents and gliding jellyfish. Python 3, no dependencies."""
import argparse, math, random, shutil, sys, time
from dataclasses import dataclass
from functools import lru_cache
from math import sin, cos, sqrt, pi
PALETTE = [(35,235,255),(170,65,255),(255,35,190),(255,190,45),(35,120,255),(45,255,180)]
@dataclass
class Jelly:
    x: float; y: float; size: float; speed: float; phase: float; color: tuple; seed: int
    depth: float = 1.0
    frequency: float = 2.4
    born: float = 0.0
    vy: float = 0.0
    vx: float = 0.0
    home: float = 0.5

def spawn(rng, i, n, initial=True):
    j = Jelly((i+rng.uniform(.25,.75))/n, rng.uniform(.05,1.25) if initial else rng.uniform(1.05,1.4), rng.uniform(.65,1.35),rng.uniform(.035,.075),rng.uniform(0,2*pi),PALETTE[i%len(PALETTE)],rng.randrange(100000))

    j.home=(i+.5)/n
    j.depth=rng.uniform(.38,1.0)
    j.size *= .72+.28*j.depth
    j.frequency=rng.uniform(1.65,2.65)
    j.vy=j.speed*.65
    return j

def flow(x,y,t):
    return .013*sin(t*.24+y*3.8)+.007*sin(t*.13+x*5-y*2)

def cycle(j,t):
    return (t-j.born)*j.frequency+j.phase

def advance(j,t,dt,steer=0.0,pace=1.0):
    # Thrust peaks while the rim is closing; water drag produces a glide.
    angle=cycle(j,t)
    thrust=max(0.,cos(angle))**2
    target=j.speed*(.30+2.15*thrust)*(.68+.32*j.depth)*pace
    j.vy+=(target-j.vy)*(1-math.exp(-dt*3.0))
    target_x=flow(j.x,j.y,t)*(.45+.55*j.depth)+.004*sin(t*.35+j.phase)
    target_x+=.12*(j.home-j.x)+steer
    j.vx+=(target_x-j.vx)*(1-math.exp(-dt*1.4))
    j.x+=j.vx*dt
    # Soft boundaries keep the bells in view without teleporting.
    if j.x<.08: j.vx+=dt*(.08-j.x)*.4
    if j.x>.92: j.vx-=dt*(j.x-.92)*.4
    j.y-=j.vy*dt

def footprint(j,w,h):
    r=max(5,min(w*.115,h*.27)*j.size)*1.1
    return (2.0*r/w, .60*r/h, max(12,r*1.95)*1.24/h)

def layout(js,w,h,rng,initial=False):
    # Spread adjacent lanes vertically when their silhouettes are too wide.
    for i,j in enumerate(js):
        if not initial: continue
        j.x=j.home
        j.y=.10+(i%3)*.47+rng.uniform(-.035,.035)

def avoid(js,w,h,t):
    steering=[0.0]*len(js); pace=[1.0]*len(js)
    for i,a in enumerate(js):
        ax,at,ab=footprint(a,w,h)
        for k in range(i+1,len(js)):
            b=js[k]; bx,bt,bb=footprint(b,w,h)
            dx=b.x-a.x; dy=b.y-a.y
            gap=(ab+bt if dy>=0 else bb+at)+.055
            reach=ax+bx+.025
            if abs(dx)>=reach or abs(dy)>=gap+.12: continue
            weight=(1-abs(dx)/reach)*max(0,1-abs(dy)/(gap+.12))
            sign=1 if dx>=0 else -1
            steering[i]-=.15*weight*sign; steering[k]+=.15*weight*sign
            # The trailing animal yields rather than swimming into the leading one.
            trailing=k if dy>=0 else i
            pace[trailing]=min(pace[trailing],max(.15,1-1.5*weight))
    return steering,pace

def respawn(rng,i,js,w,h,t):
    j=spawn(rng,i,len(js),False); j.born=t
    rx,top,bottom=footprint(j,w,h)
    # Search below the screen for a free entry slot, including existing tendrils.
    best=None
    for y in [1.05+.12*k for k in range(24)]:
        for x in [j.home]+[(k+.5)/len(js) for k in range(len(js))]:
            if any(abs(x-a.x)<rx+footprint(a,w,h)[0]+.025 and
                   y-top<a.y+footprint(a,w,h)[2]+.07 and
                   y+bottom>a.y-footprint(a,w,h)[1]-.07
                   for k,a in enumerate(js) if k!=i): continue
            score=y+.9*abs(x-j.home)
            if best is None or score<best[0]: best=(score,x,y)
    if best: _,j.x,j.y=best
    else: j.y=max(a.y+footprint(a,w,h)[2] for a in js)+top+.15
    j.home=j.x
    return j

def render(w,h,t,jellies,stars,glow):
    cells={}
    def put(x,y,ch,color,b):
        x,y=int(round(x)),int(round(y))
        if not (0<=x<w and 0<=y<h) or b<=0: return
        key=(x,y)
        if key not in cells or cells[key][2]<b: cells[key]=(ch,color,b)
    for j in sorted(jellies,key=lambda j:j.depth):
        angle=cycle(j,t)
        pulse=sin(angle)
        depth_light=.46+.54*j.depth
        bell_light=depth_light*(.89+.11*(1+pulse)*.5)
        cx=j.x*w+sin(t*.65+j.phase)*w*.009
        cy=j.y*h
        rx=max(5,min(w*.115,h*.27)*j.size)*(1+.10*pulse)
        ry=max(3,rx*.49)*(1-.12*pulse)
        # Rounded, layered bell with luminous knots and fine connecting bands.
        rows=max(4,round(ry)); rng=random.Random(j.seed)
        knots=[rng.uniform(-.6,.6) for _ in range(rows+1)]
        # Smooth, progressive inward curl of the three lowest bell rows.
        clench=(1+pulse)*.5
        clench=clench*clench*(3-2*clench)
        for k in range(rows+1):
            v=k/rows
            span=rx*sqrt(max(.12,1-(1-v)**2))
            curl=max(0.0,1-(rows-k)/3)
            span-=min(1.5,rx*.12)*clench*curl**1.6
            for dx in range(-int(span),int(span)+1):
                u=dx/max(1,span); edge=abs(u)
                wave=sin(dx*.63+k*.72-t*2+j.phase)
                knot=abs(u-knots[k])<.14 or edge>.85
                if k==rows or k==0:
                    chars='&%#+*'; bright=.88+.12*wave
                elif knot or (wave>.72 and k%2==0):
                    chars='&%+*#'; bright=.76+.18*wave
                else:
                    chars='---==:.'; bright=.53+.14*wave
                ch=chars[(dx*13+k*7+j.seed)%len(chars)]
                put(cx+dx,cy+k-rows,ch,j.color,bright*bell_light)
            if glow:
                for d in (1,2):
                    for sign in (-1,1): put(cx+sign*(span+d),cy+k-rows,'.',j.color,.14/d*depth_light)
        # Coherent current: the whole body bends, but strands retain their own motion.
        length=max(12,rx*1.95)
        def current(k):
            v=k/length
            return (rx*.42*sin(t*1.25-k*.20+j.phase)+rx*.23*sin(t*.24+j.y*3.8-k*.07)-j.vx*w*.45)*min(1,v*2)
        # Dense textured oral body, tapering into a broken, translucent plume.
        # The lower body (not the tendrils) now rhythmically squeezes inward during
        # the swim cycle, like a jellyfish contracting its bell.
        body=length*.56
        contraction=(1+pulse)*.5  # 0 relaxed, 1 squeezed
        for k in range(1,int(body)+1):
            v=k/body
            center=cx+current(k)
            base_span=rx*(.43*(1-v)**.8+.04)*(1+.12*sin(k*.5-t*2))
            pinch_zone=max(0.0,(v-.18)/.82)
            squeeze=1-.34*contraction*(pinch_zone**1.7)
            span=max(1,base_span*squeeze)
            for dx in range(-int(span),int(span)+1):
                u=dx/max(1,span)
                texture=sin(dx*1.5+k*.68-t*1.9+j.phase)+sin(dx*.7-k*.9+t*1.3)
                noise=((dx*73+k*113+j.seed)%97)/97
                if noise<.30+.60*v or (abs(u)>.8 and v>.45): continue
                chars='&%+*:' if v<.38 else '*+:.' if v<.68 else ':..'
                ch=chars[(dx*11+k*7+j.seed)%len(chars)]
                brightness=(.75*(1-v)**1.15+.10)*(.78+.22*sin(texture))
                put(center+dx,cy+k,ch,j.color,brightness*depth_light*(.91+.09*sin(angle-2*v)))
        # Distinct outer and inner tentacles with wider spacing toward the tips.
        base_rx=max(5,min(w*.115,h*.27)*j.size)
        count=max(4,min(8,round(base_rx*.42)+1))
        rng=random.Random(j.seed+100003)
        for a in range(count):
            u=2*a/(count-1)-1; phase=rng.uniform(0,2*pi)
            strand=length*rng.uniform(.76,1.24)
            def path(k):
                v=k/strand
                # Follow the bell at the root, then transmit the contraction
                # down the strand with increasing delay and decreasing strength.
                local_pulse=sin(angle-1.6*v)
                local_clench=(1+local_pulse)*.5
                local_clench=local_clench**2*(3-2*local_clench)
                local_rx=base_rx*(1+.10*local_pulse)
                rim_curl=min(1.5,local_rx*.12)*local_clench
                spread=local_rx*(.86+.34*v)-rim_curl*.86*(1-.65*v)
                return (cx+u*spread+current(k)
                        +rx*.15*sin(t*1.8-k*.28+phase)*v
                        +rx*.09*sin(k*.48-t*1.2+phase)*v)
            for k in range(1,int(strand)+1):
                v=k/strand; xx=path(k); slope=path(k+.5)-path(k-.5)
                b=(.95-.75*v)*(.91+.09*sin(k*.55-t*2+phase))*depth_light*(.87+.13*(1+sin(angle-3.2*v))*.5)
                if v>.85: ch='.'
                elif v>.63: ch=':' if (k+a)%3 else '.'
                elif slope>.60: ch='\\'
                elif slope<-.60: ch='/'
                elif slope>.22: ch=')'
                elif slope<-.22: ch='('
                else: ch='|'
                if v>.67 and (k+a)%5==0: continue
                put(xx,cy+k,ch,j.color,b)
                if v<.65:
                    prev=round(path(k-1)); curr=round(xx)
                    for bridge in range(min(prev,curr)+1,max(prev,curr)):
                        put(bridge,cy+k,ch,j.color,b*.78)
    # Background particles are composited last, only in empty cells.
    # Their depth and phase are stable, so they drift instead of flickering.
    for x,y,p in stars:
        depth=.25+.75*((p*1.618)%1)
        yy=(y+t*(.002+.004*depth))%1
        xx=(x+depth*(.021*sin(t*.19+y*3.8)+.010*sin(t*.11+x*5)))%1
        px,py=xx*w,yy*h
        reaction=0.; tint=(100,150,190)
        for j in jellies:
            r=max(5,min(w*.115,h*.27)*j.size)
            dx=px-j.x*w; dy=(py-j.y*h)*2
            d=sqrt(dx*dx+dy*dy)/r
            if d<2.2:
                q=(1-d/2.2)**2
                if q>reaction:
                    reaction=q; tint=tuple(int(.65*v+.35*c) for v,c in zip((100,150,190),j.color))
                if d>.01:
                    px+=dx/d/r*q*1.2; py+=dy/d/r*q*.6
        brightness=(.13+.16*depth+.035*sin(t*.55+p))+.24*reaction
        # Rare soft plankton twinkles, without illuminating the whole background.
        twinkle=max(0.,sin(t*.7+p*7))**12
        if depth>.78: brightness+=.10*twinkle
        key=(int(round(px)),int(round(py)))
        if key not in cells:
            put(px,py,'.' if depth<.80 else ('+' if depth>.97 else ':'),tint,brightness)
    return cells

def water_light(w,h,cells,strength=1.0):
    """Diffuse light from existing glyphs; never alter the foreground geometry."""
    if strength <= 0: return {}
    # Terminal cells are roughly twice as tall as they are wide.
    # Two separable Gaussian passes make the halo approximately round on screen.
    def kernel(sigma):
        radius=math.ceil(sigma*2.7)
        weights=[math.exp(-.5*(i/sigma)**2) for i in range(-radius,radius+1)]
        total=sum(weights)
        return [(i-radius,v/total) for i,v in enumerate(weights)]
    # Accumulate on a half-resolution light grid, then interpolate smoothly.
    gw,gh=(w+1)//2,(h+1)//2
    kx,ky=kernel(2.5),kernel(1.25)
    sources={}
    for (x,y),(ch,c,b) in cells.items():
        if c not in PALETTE or b<.18: continue
        dest=sources.setdefault((x//2,y//2),[0.,0.,0.])
        power=b*b*.25
        dest[0]+=c[0]*power; dest[1]+=c[1]*power; dest[2]+=c[2]*power
    def blur(src,kernel,horizontal):
        dst={}
        for (x,y),(r,g,b) in src.items():
            for d,k in kernel:
                xx,yy=(x+d,y) if horizontal else (x,y+d)
                if not (0<=xx<gw and 0<=yy<gh): continue
                v=dst.setdefault((xx,yy),[0.,0.,0.])
                v[0]+=r*k; v[1]+=g*k; v[2]+=b*k
        return dst
    light=blur(blur(sources,kx,True),ky,False)
    result={}; zero=(0.,0.,0.); scale=strength*1.65
    for (gx,gy),a in light.items():
        if max(a)*scale<.15: continue
        b=light.get((gx+1,gy),zero); c=light.get((gx,gy+1),zero); d=light.get((gx+1,gy+1),zero)
        for ox,oy,values in ((0,0,a),(1,0,tuple((a[i]+b[i])*.5 for i in range(3))), (0,1,tuple((a[i]+c[i])*.5 for i in range(3))), (1,1,tuple((a[i]+b[i]+c[i]+d[i])*.25 for i in range(3)))):
            x,y=gx*2+ox,gy*2+oy
            if x>=w or y>=h: continue
            color=tuple(round(95*(1-math.exp(-v*scale/95))) for v in values)
            if max(color)>0: result[x,y]=color
    return result

def frame_pixels(w,h,cells,halo,water_base):
    light=water_light(w,h,cells,halo)
    base=water_base if halo>0 else None
    pixels={}
    for pos,emission in light.items():
        pixels[pos]=(' ',None,tuple(min(255,a+b) for a,b in zip(water_base,emission)))
    for pos,(ch,c,b) in cells.items():
        b=min(1,b); extra=max(0,b-.78)*220
        rgb=tuple(min(255,int(v*b+extra)) for v in c)
        pixels[pos]=(ch,rgb,pixels.get(pos,(' ',None,base))[2])
    return pixels

class TerminalRenderer:
    def __init__(self):
        self.previous={}; self.size=None; self.base=None
    def draw(self,w,h,cells,halo,water_base,sync=True):
        pixels=frame_pixels(w,h,cells,halo,water_base)
        base=water_base if halo>0 else None
        empty=(' ',None,base)
        full=self.size!=(w,h) or self.base!=base
        out=['\x1b[?2026h' if sync else '', '\x1b[0m']; fg=bg=None
        if full:
            out.append('\x1b[49m' if base is None else '\x1b[48;2;%d;%d;%dm'%base)
            out.append('\x1b[2J'); bg=base
        changed=sorted((pos for pos in (pixels.keys() | (set() if full else self.previous.keys())) if full or pixels.get(pos,empty)!=self.previous.get(pos,empty)),key=lambda p:(p[1],p[0]))
        last=(-2,-2)
        for x,y in changed:
            ch,new_fg,new_bg=pixels.get((x,y),empty)
            if y!=last[1] or x!=last[0]+1: out.append(f'\x1b[{y+1};{x+1}H')
            if new_bg!=bg:
                out.append('\x1b[49m' if new_bg is None else '\x1b[48;2;%d;%d;%dm'%new_bg); bg=new_bg
            if new_fg is not None and new_fg!=fg:
                out.append('\x1b[38;2;%d;%d;%dm'%new_fg); fg=new_fg
            out.append(ch); last=(x,y)
        self.previous=pixels; self.size=(w,h); self.base=base
        out.append('\x1b[0m')
        if sync: out.append('\x1b[?2026l')
        return ''.join(out)

def ansi(w,h,cells,halo=1.0,water_base=(14,14,14),t=0):
    return TerminalRenderer().draw(w,h,cells,halo,water_base,False)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--count',type=int,default=6); p.add_argument('--fps',type=int,default=30); p.add_argument('--speed',type=float,default=1); p.add_argument('--no-glow',action='store_true'); p.add_argument('--seed',type=int,default=42); p.add_argument('--once',action='store_true',help='Print one frame and exit'); p.add_argument('--halo',type=float,default=1.0,help='Water glow intensity (0 disables it)'); p.add_argument('--water-bg',default='0e0e0e',help='Base water RGB as six hex digits (default 0e0e0e)'); p.add_argument('--no-sync',action='store_true',help='Disable synchronized terminal updates'); args=p.parse_args()
    try:
        raw=args.water_bg.lstrip('#')
        if len(raw)!=6: raise ValueError()
        water_base=tuple(int(raw[i:i+2],16) for i in (0,2,4))
    except ValueError: p.error('--water-bg requires six hexadecimal digits')
    if not 1<=args.count<=30 or not 1<=args.fps<=120 or args.speed<=0 or not math.isfinite(args.halo) or args.halo<0: p.error('count 1–30, fps 1–120, speed positive and halo nonnegative required')
    rng=random.Random(args.seed); js=[spawn(rng,i,args.count) for i in range(args.count)]; stars=[(rng.random(),rng.random(),rng.random()*6) for _ in range(48)]
    w,h=shutil.get_terminal_size((100,40)); layout(js,max(1,w-1),max(1,h-1),rng,True)
    if args.once:
        w,h=shutil.get_terminal_size((100,40)); print(ansi(w-1,h-1,render(w-1,h-1,0,js,stars,not args.no_glow),0 if args.no_glow else args.halo,water_base)); return
    if not sys.stdout.isatty(): p.error('Run in an interactive terminal or use --once')
    sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[2J'); sys.stdout.flush()
    start=prev=time.monotonic(); deadline=start; t=0.; renderer=TerminalRenderer()
    try:
        while True:
            now=time.monotonic(); dt=min(.15,now-prev)*args.speed; prev=now; t+=dt
            w,h=shutil.get_terminal_size(); w=max(1,w-1); h=max(1,h-1)
            steer,pace=avoid(js,w,h,t)
            for i,j in enumerate(js):
                advance(j,t,dt,steer[i],pace[i])
                if j.y< -max(.25, min(w*.115,h*.27)*j.size*2.6/h): 
                    js[i]=respawn(rng,i,js,w,h,t)
            sys.stdout.write(renderer.draw(w,h,render(w,h,t,js,stars,not args.no_glow),0 if args.no_glow else args.halo,water_base,not args.no_sync)); sys.stdout.flush()
            deadline+=1/args.fps
            after=time.monotonic()
            if deadline<after: deadline=after
            time.sleep(max(0,deadline-after))
    except KeyboardInterrupt: pass
    finally: sys.stdout.write('\x1b[?2026l\x1b[0m\x1b[?25h\x1b[?1049l'); sys.stdout.flush()
if __name__=='__main__': main()
