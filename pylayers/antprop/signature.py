#-*- coding:Utf-8 -*-
"""
Class Signatures
================

.. autosummary::
    :toctree: generated/

    Signatures.__init__
    Signatures.__repr__
    Signatures.__len__
    Signatures.num
    Signatures.info
    Signatures.save
    Signatures.load
    Signatures.sp
    Signatures.procone
    Signatures.propaths
    Signatures.propaths2
    Signatures.procone2
    Signatures.calsig
    Signatures.run
    Signatures.run1
    Signatures.run4
    Signatures.run5
    Signatures.run2
    Signatures.run3
    Signatures.meta
    Signatures.lineofcycle
    Signatures.cones
    Signatures.unfold
    Signatures.show
    Signatures.showi
    Signatures.rays

Class Signature
===============

.. autosummary::
    :toctree: generated/

    Signature.__init__
    Signature.__repr__
    Signature.info
    Signature.split
    Signature.ev2
    Signature.evf
    Signature.ev
    Signature.unfold
    Signature.evtx
    Signature.image
    Signature.backtrace
    Signature.sig2beam
    Signature.sig2ray

Utility functions
=================

.. autosummary::
    :toctree: generated/

    showsig
    gidl
    frontline
    edgeout2
    edgeout

"""
import doctest
import numpy as np
#import scipy as sp
import scipy.linalg as la
import pdb
import h5py
import copy
import time
import pickle
import logging
import networkx as nx
import shapely.geometry as shg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pylayers.gis.layout as layout
import pylayers.util.geomutil as geu
import pylayers.util.cone as cone
#import pylayers.util.graphutil as gph
import pylayers.util.pyutil as pyu
import pylayers.util.plotutil as plu
from pylayers.antprop.rays import Rays
from pylayers.util.project import *
import heapq
#from numba import autojit

def showsig(L,s,tx=[],rx=[]):
    """ show signature

    Parameters
    ----------

    L  : Layout
    s  :
    tx :
    rx :

    """
    L.display['thin']=True
    fig,ax = L.showGs()
    L.display['thin']=False
    L.display['edlabel']=True
    L.showGs(fig=fig,ax=ax,edlist=s,width=4)
    if tx !=[]:
        plt.plot(tx[0],tx[1],'x')
    if rx !=[]:
        plt.plot(rx[0],rx[1],'+')
    plt.title(str(s))
    plt.show()
    L.display['edlabel']=False


def gidl(g):
    """ gi without diffraction

   Returns
   -------

   gr

   """

    edlist=[]
    pos={}
    for n in g.nodes():
        if len(n)>1:
            edlist.append(n)
    gr=g.subgraph(edlist)
    dpos = {k:g.pos[k] for k in edlist}
    gr.pos=dpos
    return(gr)


def frontline(L,nc,v):
    """ determine cycle frontline

    This function calculates the scalar product of the normals of a cycle 
    and returns the indev of segments whith are facing the given direction v.
    scalar product < 0.

    Parameters
    ----------

    L : Layout
    nc : cycle number
    v : direction vector

    Returns
    -------

    nsegf : list

    Example
    -------

    >>> from pylayers.gis.layout import *
    >>> L = Layout()
    >>> L.dumpr()
    >>> v = np.array([1,1])
    >>> frontline(L,0,v)
    [3, 4]

    See Also
    --------

    run3

    """
    npt = filter(lambda x: x<0, L.Gt.node[nc]['polyg'].vnodes)  # points
    nseg = filter(lambda x: x>0, L.Gt.node[nc]['polyg'].vnodes) # segments
    pt  = map(lambda npt : [L.Gs.pos[npt][0],L.Gs.pos[npt][1]],npt)
    pt1 = np.array(pt)   # convert in ndarray
    n1 = geu.Lr2n(pt1.T) # get the normals of the cycle
    ps = np.sum(n1*v[:,np.newaxis],axis=0) # scalar product with vector v
    u = np.where(ps<0)[0]   # keep segment if scalar product <0
    nsegf = map(lambda n: nseg[n],u)
    return nsegf


def edgeout2(L,g):
    """ filter authorized Gi edges output

    Parameters
    ----------

    L : Layout
    g : Digraph Gi

    Notes
    -----

    Let assume a sequence (nstr0,nstr1,{nstr2A,nstr2B,...}) in a signature.
    This function checks that this sequence is feasible
    , whatever the type of nstr0 and nstr1.
    The feasible outputs from nstr0 to nstr1 are stored in an output field of
    edge (nstr0,nstr1)


    """

    # loop over all edges of Gi
    for e in g.edges():
        # extract  both termination interactions nodes
        i0 = e[0]
        i1 = e[1]

        nstr0 = i0[0]
        nstr1 = i1[0]

        # list of authorized outputs, initialized void
        output = []
        # nstr1 : segment number of final interaction
        if nstr1>0:
            pseg1 = L.seg2pts(nstr1).reshape(2,2).T
            cn = cone.Cone()
            if nstr0>0:
                pseg0 = L.seg2pts(nstr0).reshape(2,2).T
                # test if nstr0 and nstr1 are connected segments
                if (len(np.intersect1d(nx.neighbors(L.Gs,nstr0),nx.neighbors(L.Gs,nstr1)))==0):
                    # not connected
                    cn.from2segs(pseg0,pseg1)
                else:
                    # connected
                    cn.from2csegs(pseg0,pseg1)
            else:
                pt = np.array(L.Gs.pos[nstr0])
                cn.fromptseg(pt,pseg1)

            # list all potential successor of interaction i1
            i2 = nx.neighbors(g,i1)
            ipoints = filter(lambda x: x[0]<0 ,i2)
            #istup = filter(lambda x : type(eval(x))==tuple,i2)
            isegments = np.unique(map(lambda x : x[0]>0,i2))
            if len(isegments)>0:
                points = L.seg2pts(isegments)
                pta = points[0:2,:]
                phe = points[2:,:]
                #print points
                #print segments
                #cn.show()
                if len(i1)==3:
                    bs = cn.belong_seg(pta,phe)
                    #if bs.any():
                    #    plu.displot(pta[:,bs],phe[:,bs],color='g')
                    #if ~bs.any():
                    #    plu.displot(pta[:,~bs],phe[:,~bs],color='k')
                if len(i1)==2:
                    Mpta = geu.mirror(pta,pseg1[:,0],pseg1[:,1])
                    Mphe = geu.mirror(phe,pseg1[:,0],pseg1[:,1])
                    bs = cn.belong_seg(Mpta,Mphe)
                    #print i0,i1
                    #if ((i0 == (6, 0)) & (i1 == (7, 0))):
                    #    pdb.set_trace()
                    #if bs.any():
                    #    plu.displot(pta[:,bs],phe[:,bs],color='g')
                    #if ~bs.any():
                    #    plu.displot(pta[:,~bs],phe[:,~bs],color='m')
                    #    plt.show()
                    #    pdb.set_trace()

                isegkeep = isegments[bs]
                output = filter(lambda x : x[0] in isegkeep ,i2)
                # keep all segment above nstr1 and in Cone if T
                # keep all segment below nstr1 and in Cone if R

        g.add_edge(i0,i1,output=output)

    return(g)
def edgeout(L,g):
    """ filter authorized Gi edges output 

    Parameters
    ----------

    L : Layout
    g : Digraph Gi

    Notes 
    -----

    Let assume a sequence (nstr0,nstr1,{nstr2A,nstr2B,...}) in a signature.
    This function checks that this sequence is feasible
    , whatever the type of nstr0 and nstr1.
    The feasible outputs from nstr0 to nstr1 are stored in an output field of 
    edge (nstr0,nstr1)


    """

    # loop over all edges of Gi
    for e in g.edges():
        # extract  both termination interactions nodes
        i0 = eval(e[0])
        i1 = eval(e[1])
        try:
            nstr0 = i0[0]
        except:
            nstr0 = i0


        try:
            nstr1 = i1[0]
            # Transmission
            if len(i1)>2:
                typ=2
            # Reflexion    
            else :
                typ=1
        # Diffraction        
        except:
            nstr1 = i1
            typ = 3

        # list of authorized outputs, initialized void
        output = []
        # nstr1 : segment number of final interaction
        if nstr1>0:
            #cn = cone.Cone()
            #cn.from2segs(pseg0,pseg1)
            # segment unitary vector
            # l1 : unitary vector along structure segments  
            l1 = L.seguv(np.array([nstr1]))
            #
            # unitary vector along the ray (nstr0,nstr1)
            #
            p0 = np.array(L.Gs.pos[nstr0])
            p1 = np.array(L.Gs.pos[nstr1])
            v01  = p1-p0
            v01m = np.sqrt(np.dot(v01,v01))
            v01n = v01/v01m
            v10n = -v01n
            # next interaction
            # considering all neighbors of i1 in Gi 
            for i2 in nx.neighbors(g,str(i1)):

                i2 = eval(i2)
                if type(i2)==int:
                    nstr2 = i2
                else:
                    nstr2 = i2[0]
                p2 = np.array(L.Gs.pos[nstr2])
                v12 = p2-p1
                v12m = np.sqrt(np.dot(v12,v12))
                v12n = v12/v12m

                d1 = np.dot(v01n,l1)
                d2 = np.dot(l1,v12n)

                # if (reflexion is forward) or (reflexion return to its origin)
                if (d1*d2>=0) or (nstr0 == nstr2) and typ == 1:
                    output.append(str(i2))
#                elif d1*d2>=-0.2 and typ ==2:
                elif typ == 2 :
                    if abs(d1) <0.9 and abs(d2) <0.9 :
                        if d1*d2 >= -0.2:
                            output.append(str(i2))
                else:
                    pass
        g.add_edge(str(i0),str(i1),output=output)

    return(g)

class Signatures(PyLayers,dict):
    """ set of Signature given 2 Gt cycle (convex) indices

    Attributes
    ----------

    L : gis.Layout
    source : int
        source convex cycle
    target : int
        target convex cycle

    """

    def __init__(self,L,source,target,cutoff=3):
        """ object constructor

        Parameters
        ----------

        L : Layout
        source : int
            cycle number
        target : int
            cycle index
        cutoff : int
            limiting depth level in graph exploration (default 3)

        """
        self.L = L
        self.source = source
        self.target = target
        self.cutoff = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

    def __repr__(self):
        def fun1(x):
            if x==1:
                return('R')
            if x==2:
                return('T')
            if x==3:
                return('D')
        size = {}
        s = self.__class__.__name__ + '\n' + '----------'+'\n'
        #s = s + str(self.__sizeof__())+'\n'
        for k in self:
            size[k] = len(self[k])/2
        s = s + 'from cycle : '+ str(self.source) + ' to cycle ' + str(self.target)+'\n'
        for k in self:
            s = s + str(k) + ' : ' + str(size[k]) + '\n'
            a = np.swapaxes(self[k].reshape(size[k],2,k),0,2)
            # nl x 2 x nsig
            for i in range(k):
                s = s + '   '+ str(a[i,0,:]) + '\n'
                s = s + '   '+ str(a[i,1,:]) + '\n'

        return(s)

    def __len__(self):
        nsig = 0
        for k in self:
            size = len(self[k])/2
            nsig += size
        return(nsig)

    def num(self):
        """ determine the number of signatures
        """
        self.nsig = 0
        self.nint = 0
        for k in self:
            size = len(self[k])/2
            self.nsig += size
            self.nint += size*k

    def info(self):
        # print "Signatures for scenario defined by :"
        # print "Layout"
        # print "======"
        # L = self.L.info()
        # print "================================"
        # print "source : ", self.source
        # print "target : ", self.target
        size = {}
        print self.__class__.__name__ + '\n' + '----------'+'\n'
        #s = s + str(self.__sizeof__())+'\n'
        for k in self:
            size[k] = len(self[k])/2
        print 'from cycle : '+ str(self.source) + ' to cycle ' + str(self.target)+'\n'
        pyu.printout('Reflection',pyu.BLUE)
        print '  '
        pyu.printout('Transmission',pyu.GREEN)
        print '  '
        pyu.printout('Diffraction',pyu.RED)
        print '  \n'
        for k in self:
            print str(k) + ' : ' + str(size[k]) 
            a = np.swapaxes(self[k].reshape(size[k],2,k),0,2)
            # nl x 2 x nsig
            for i in range(k):

                nstr=a[i,0,:]
                typ=a[i,1,:]
                print '[',
                for n,t in zip(nstr,typ):
                    if t==1:
                        pyu.printout(str(n),pyu.BLUE)
                    if t==2:
                        pyu.printout(str(n),pyu.GREEN)
                    if t==3:
                        pyu.printout(str(n),pyu.RED)
                print ']'
            print'\n'
                # s = s + '   '+ str(a[i,0,:]) + '\n'

                # s = s + '   '+ str(a[i,1,:]) + '\n'

    def saveh5(self):
        """ save signatures in hdf5 format
        """

        filename=pyu.getlong(self.filename+'.h5',pstruc['DIRSIG'])
        f=h5py.File(filename,'w')

        # try/except to avoid loosing the h5 file if
        # read/write error
        try:
            f.attrs['L']=self.L.filename
            f.attrs['source']=self.source
            f.attrs['target']=self.target
            f.attrs['cutoff']=self.cutoff
            for k in self.keys():
                f.create_dataset(str(k),shape=np.shape(self[k]),data=self[k])
            f.close()
        except:
            f.close()
            raise NameError('Signature: issue when writting h5py file')

    def loadh5(self,filename=[]):
        """ load signatures hdf5 format
        """
        if filename == []:
            _filename = self.filename
        else :
            _filename = filename

        filename=pyu.getlong(_filename+'.h5',pstruc['DIRSIG'])

        # try/except to avoid loosing the h5 file if 
        # read/write error
        try:
            f=h5py.File(filename,'r')
            for k in f.keys():
                self.update({eval(k):f[k][:]})
            f.close()
        except:
            f.close()
            raise NameError('Signature: issue when reading h5py file')


        _fileL=pyu.getshort(filename).split('_')[0]+'.ini'
        self.L=layout.Layout(_fileL)
        try:
            self.L.dumpr()
        except:
            self.L.build()
            self.L.dumpw()


    def _saveh5(self,filenameh5,grpname):
        """ Save in hdf5 compliant with Links
        """


        filename=pyu.getlong(filenameh5,pstruc['DIRLNK'])
        # if grpname == '':
        #     grpname = str(self.source) +'_'+str(self.target) +'_'+ str(self.cutoff)
        try:
            # file management
            fh5=h5py.File(filename,'a')
            if not grpname in fh5['sig'].keys():
                fh5['sig'].create_group(grpname)
            else :
                raise NameError('sig/'+grpname +'already exists in '+filenameh5)
            f=fh5['sig/'+grpname]

            # write data
            f.attrs['L']=self.L.filename
            f.attrs['source']=self.source
            f.attrs['target']=self.target
            f.attrs['cutoff']=self.cutoff
            for k in self.keys():
                f.create_dataset(str(k),shape=np.shape(self[k]),data=self[k])
            fh5.close()
        except:
            fh5.close()
            raise NameError('Signature: issue when writting h5py file')


    def _loadh5(self,filenameh5,grpname):
        """ load signatures in hdf5 format compliant with class Links

        Parameters
        ----------

        filenameh5 : string
            filename of the h5py file (from Links Class)
        grpname : string
            groupname of the h5py file (from Links Class)


        See Also
        --------

        pylayers.simul.links

        """

        filename=pyu.getlong(filenameh5,pstruc['DIRLNK'])
        # if grpname =='':
        #     grpname = str(self.source) +'_'+str(self.target) +'_'+ str(self.cutoff)

        # try/except to avoid loosing the h5 file if
        # read/write error
        try:
            fh5=h5py.File(filename,'r')
            f=fh5['sig/'+grpname]
            for k in f.keys():
                self.update({eval(k):f[k][:]})
            Lname=f.attrs['L']
            fh5.close()
        except:
            fh5.close()
            raise NameError('Signature: issue when reading h5py file')

        self.L=layout.Layout(Lname)
        try:
            self.L.dumpr()
        except:
            self.L.build()
            self.L.dumpw()


    def save(self):
        """ save signatures
        """
        L=copy.deepcopy(self.L)
        del(self.L)
        filename=pyu.getlong(self.filename+'.h5',pstruc['DIRSIG'])
        with open(filename, 'wb') as handle:
          pickle.dump(self, handle)
        self.L=L

    def load(self,filename=[]):
        """ load signatures
        """


        if filename == []:
            _filename = self.filename
        else :
            _filename = filename

        filename=pyu.getlong(_filename,pstruc['DIRSIG'])
        try:
            handle=open(filename, 'rb')
            sitmp = pickle.load(handle)
        except:
            raise NameError(filename +' does not exist')


        # to load a dictionary, use update
        self.update(sitmp)


        _fileL=pyu.getshort(filename).split('_')[0]+'.ini'
        self.L=layout.Layout(_fileL)
        try:
            self.L.dumpr()
        except:
            self.L.build()
            self.L.dumpw()

    def sp(self,G, source, target, cutoff=None):
        """ algorithm for signature determination

        Parameters
        ----------

        G : Graph
        source : tuple or int
        target : tuple or int
        cutoff : int

        See Also
        --------

        pylayers.antprop.signature.run3

        """
        if cutoff < 1:
            return
        visited = [source]
        stack = [iter(G[source])]
        while stack:
            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.pop()
            elif len(visited) < cutoff:
                if child == target:
                    for i in range(len(self.ds[source])):
                        s=self.ds[target][i] + visited
                        self.ds[target].append(s)

                    # yield visited +[target]
                elif child not in visited:
                    visited.append(child)
                    stack.append(iter(G[child]))
            else: #len(visited) == cutoff:
                if child == target or target in children:
                    for i in range(len(self.ds[source])):
                        s=self.ds[target][i] + visited
                        self.ds[target].append(s)

                stack.pop()
                visited.pop()



    def procone(self,L, G, source, target, cutoff=1):
        """ seek all simple_path from source to target looking backward

        Parameters
        ----------

        L : Layout
        G : networkx Graph Gi
        source : tuple
            interaction (node of Gi)
        target : tuple
            interaction (node of Gi)
        cutoff : int

        Notes
        -----

        adapted from all_simple_path of networkx

        1- Determine all nodes connected to Gi

        """
        #print "source :",source
        #print "target :",target

        if cutoff < 1:
            return

        visited = [source]

        # stack is a list of iterators
        stack = [iter(G[source])]

        # while the list of iterators is not void
        while stack: #
            # children is the last iterator of stack
            children = stack[-1]
            # next child
            child = next(children, None)
            #print "child : ",child
            #print "visited :",visited
            if child is None  : # if no more child
                stack.pop()   # remove last iterator
                visited.pop() # remove from visited list
            elif len(visited) < cutoff: # if visited list length is less than cutoff
                if child == target:  # if child is the target point - YIELD A SIGNATURE
                    #print visited + [target]
                    yield visited + [target] # output signature
                else:
                #elif child not in visited: # else visit other node - CONTINUE APPEND CHILD
                    # getting signature until last point
                    diff  = np.where(np.array(visited)<0)[0]
                    if len(diff)==0:
                        brin = visited
                    else:
                        brin = visited[diff[-1]:]
                    # looking backward with a cone
                    if len(brin)>2:
                        # warning visited is also appended visited[-2] is the
                        # last node
                        brin.append(child)
                        s = Signature(brin)
                        s.evf(L)
                        ta,he = s.unfold()
                        cn = cone.Cone()
                        segchild = np.vstack((ta[:,-1],he[:,-1])).T
                        segvm1 = np.vstack((ta[:,-2],he[:,-2])).T
                        cn.from2segs(segchild,segvm1)
                        typ,proba = cn.belong_seg(ta[:,:-2],he[:,:-2])
                        #fig,ax = plu.displot(ta,he)
                        #fig,ax = cn.show(fig=fig,ax=ax)
                        #plt.show()
                        #pdb.set_trace()
                        if (typ==0).any():
                        # child no valid (do nothing)
                            visited.pop()
                        else:
                        # child valid (append child to visited and go forward)
                            stack.append(iter(G[visited[-2]][child]['output']))
                    else:
                        stack.append(iter(G[visited[-1]][child]['output']))
                        visited.append(child)

            else: #len(visited) == cutoff (visited list is too long)
                if child == target or target in children:
                    #print visited + [target]
                    yield visited + [target]
                stack.pop()
                visited.pop()


    def short_propath(self,G,source,target=None,dout={},cutoff=None,weight=False):
        """ updated dijkstra
        """
        if source==target:
            return ({source:0}, {source:[source]})
        dist = {}  # dictionary of final distances
        paths = {source:[source]}  # dictionary of paths
        seen = {source:0}
        fringe=[] # use heapq with (distance,label) tuples
        heapq.heappush(fringe,(0,source))
        firstloop=True
        while fringe:
            if not firstloop:
                oldv = v
            (d,v)=heapq.heappop(fringe)

            if v in dist:
                continue # already searched this node.
            dist[v] = d
            if v == target:
                break
            #for ignore,w,edgedata in G.edges_iter(v,data=True):
            #is about 30% slower than the following
            if firstloop:
                edata = iter(G[v].items())
            else:
                try:
                    edata = iter(G[oldv][v]['output'].items())
                except:
                    break
            for w,edgedata in edata:
                if weight :
                    if not firstloop:
                        vw_dist = dist[v] + edgedata 
                    else :
                        vw_dist = dist[v] #+ edgedata.get(weight,1) #<= proba should be add here
                else :
                    vw_dist = dist[v]
                if cutoff is not None:
                    if vw_dist>cutoff:
                        continue
                if w in dist:
                    if vw_dist < dist[w]:
                        raise ValueError('Contradictory paths found:',
                                         'negative weights?')
                elif w not in seen or vw_dist < seen[w]:
                    seen[w] = vw_dist
                    heapq.heappush(fringe,(vw_dist,w))
                    paths[w] = paths[v]+[w]
            firstloop=False


        if paths.has_key(target):
            if dout.has_key(len(paths[target])):
                dout[len(paths[target])].append([[p[0], len(p)] for p in paths[target]])
            else :
                dout[len(paths[target])]=[]
                dout[len(paths[target])].append([[p[0], len(p)] for p in paths[target]])

        return dout


    def propaths(self,G, source, target, cutoff=1,bt=False):
        """ seek all simple_path from source to target

        Parameters
        ----------

        G : networkx Graph Gi
        source : tuple
            interaction (node of Gi)
        target : tuple
            interaction (node of Gi)
        cutoff : int
        bt : bool
            allow backtrace (visite nodes already visited)

        Notes
        -----

        adapted from all_simple_path of networkx

        1- Determine all nodes connected to Gi

        """
        #print "source :",source
        #print "target :",target

        if cutoff < 1:
            return

        visited = [source]
        # stack is a list of iterators
        stack = [iter(G[source])]
        # lawp = list of airwall position in visited
        lawp = []

        # while the list of iterators is not void
        # import ipdb
        # ipdb.set_trace()
        while stack: #
            # children is the last iterator of stack

            children = stack[-1]
            # next child
            child = next(children, None)
            # update number of useful segments
            # if there is airwall in visited
            #

            if child is None  : # if no more child
                stack.pop()   # remove last iterator
                visited.pop() # remove from visited list
                try:
                    lawp.pop()
                except:
                    pass

            elif (len(visited) < (cutoff + sum(lawp))):# if visited list length is less than cutoff
                if child == target:  # if child is the target point
                    #print visited + [target]
                    yield visited + [target] # output signature

                elif (child not in visited) or (bt): # else visit other node
                    # only visit output nodes except if bt
                    #pdb.set_trace()
                    try:
                        dintpro = G[visited[-1]][child]['output']
                    except:
                        dintpro ={}

                    stack.append(iter(dintpro.keys()))
                    #stack.append(iter(G[visited[-1]][child]['output']))
                    visited.append(child)
                    # check if child (current segment) is an airwall
                    if child[0] in self.L.name['AIR']:
                        lawp.append(1)
                    else:
                        lawp.append(0)



            else: #len(visited) == cutoff (visited list is too long)
                if child == target or target in children:
                    #print visited + [target]
                    yield visited + [target]

                stack.pop()
                visited.pop()
                try:
                    lawp.pop()
                except:
                    pass

    def propaths3(self,Gi,source,target,cutoff=None):
        """ seek shortest path from source to target

        Parameters
        ----------

        Gi : graph of interactions
        source : source interaction
        target : target interaction
        cutoff : cutoff

        """

        level = 0
        nextlevel={source:Gi[source]}   # list of nodes to check at next level
        paths={source:[source]}         # paths dictionary  (paths to key from source)

        while nextlevel:
            thislevel = nextlevel
            nextlevel = {}
            for v in thislevel:
                for w in thislevel[v]:
                    # reach a node which is not in paths
                    if w not in paths:
                        paths[w]=paths[v]+[w]
                        nextlevel[w]= Gi[v][w]['output'].keys()
                    if w == target:
                        nstr = np.array(map(lambda x: x[0],paths[w]))
                        typ  = np.array(map(lambda x: len(w),paths[w]))
            level=level+1
            if (cutoff is not None and cutoff <= level):  break


    def propaths2(self,G, source, target,dout={}, cutoff=1,bt=False):
        """ seek all simple_path from source to target

        Parameters
        ----------

        G : networkx Graph Gi
        dout : dictionnary
            ouput dictionnary
        source : tuple
            interaction (node of Gi)
        target : tuple
            interaction (node of Gi)
        cutoff : int
        bt : bool
            allow backtrace (visite nodes already visited)

        Returns
        -------

        dout : dictionnary
            key : int
               number of interactions
            values : list

        Notes
        -----

        adapted from all_simple_path of networkx

        1- Determine all nodes connected to Gi

        """
        #print "source :",source
        #print "target :",target

        if cutoff < 1:
            return


        visited = [source]
        # stack is a list of iterators
        stack = [iter(G[source])]
        # lawp = list of airwall position in visited
        lawp = []

        # while the list of iterators is not void
        # import ipdb
        # ipdb.set_trace()
        while stack: #
            # children is the last iterator of stack

            children = stack[-1]
            # next child

            child = next(children, None)

            # update number of useful segments
            # if there is airwall in visited
            if child is None  : # if no more child
                stack.pop()   # remove last iterator
                visited.pop() # remove from visited list
                try:
                    lawp.pop()
                except:
                    pass

            elif (len(visited) < (cutoff + sum(lawp))):# if visited list length is less than cutoff
                if child == target:  # if child is the target point
                    #print visited + [target]
                    path = visited + [target]
                    try:
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    except:
                        dout[len(path)]=[]
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    #yield visited + [target] # output signature

                elif (child not in visited) or (bt): # else visit other node
                    # only visit output nodes except if bt
                    #pdb.set_trace()
                    try:
                        dintpro = G[visited[-1]][child]['output']
                    except:
                        dintpro ={}

                    stack.append(iter(dintpro.keys()))
                    #stack.append(iter(G[visited[-1]][child]['output']))
                    visited.append(child)
                    # check if child (current segment) is an airwall
                    # warning not efficient if many airwalls
                    if child[0] in self.L.name['AIR']:
                        lawp.append(1)
                    else:
                        lawp.append(0)



            else: #len(visited) == cutoff (visited list is too long)
                if child == target or target in children:
                    path = visited + [target]
                    try:
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    except:
                        #print "non existing : ",len(path)
                        dout[len(path)]=[]
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    #print visited + [target]
                    #yield visited + [target]

                stack.pop()
                visited.pop()
                try:
                    lawp.pop()
                except:
                    pass
        return dout


    def procone2(self,L,G, source, target,dout={}, cutoff=1):
        """ seek all simple_path from source to target looking backward

        Parameters
        ----------

        L : Layout
        G : networkx Graph Gi
        dout : dictionnary
            ouput dictionnary
        source : tuple
            interaction (node of Gi)
        target : tuple
            interaction (node of Gi)
        cutoff : int

        Notes
        -----

        adapted from all_simple_path of networkx

        1- Determine all nodes connected to Gi

        """
        #print "source :",source
        #print "target :",target

        if cutoff < 1:
            return

        visited = [source]

        # stack is a list of iterators
        stack = [iter(G[source])]

        # while the list of iterators is not void
        while stack: #
            # children is the last iterator of stack
            children = stack[-1]
            # next child
            child = next(children, None)
            #print "child : ",child
            #print "visited :",visited
            if child is None  : # if no more child
                stack.pop()   # remove last iterator
                visited.pop() # remove from visited list
            elif len(visited) < cutoff: # if visited list length is less than cutoff
                if child == target:  # if child is the target point - YIELD A SIGNATURE
                    #print visited + [target]
                    #yield visited + [target] # output signature
                    path = visited + [target]
                    try:
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    except:
                        dout[len(path)]=[]
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                else:
                #elif child not in visited: # else visit other node - CONTINUE APPEND CHILD
                    # getting signature until last point
                    diff  = np.where(np.array(visited)<0)[0]
                    if len(diff)==0:
                        brin = visited
                    else:
                        brin = visited[diff[-1]:]
                    # looking backward with a cone
                    if len(brin)>2:
                        # warning visited is also appended visited[-2] is the
                        # last node
                        brin.append(child)
                        s = Signature(brin)
                        s.evf(L)
                        cn = cone.Cone()
                        ta,he = s.unfold()
                        segchild = np.vstack((ta[:,-1],he[:,-1])).T
                        segvm1 = np.vstack((ta[:,-2],he[:,-2])).T
                        cn.from2segs(segchild,segvm1)
                        typ,proba = cn.belong_seg(ta[:,:-2],he[:,:-2],proba=False)

                        if (typ==0).any():
                        # child no valid (do nothing)
                            visited.pop()
                        else:
                        # child valid (append child to visited and go forward)
                            stack.append(iter(G[visited[-2]][child]['output']))
                    else:
                        stack.append(iter(G[visited[-1]][child]['output']))
                        visited.append(child)

            else: #len(visited) == cutoff (visited list is too long)
                if child == target or target in children:
                    #print visited + [target]
                    #yield visited + [target]
                    path = visited + [target]
                    try:
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                    except:
                        dout[len(path)]=[]
                        dout[len(path)].append([[p[0],len(p)] for p in path])
                stack.pop()
                visited.pop()
        return dout

    # def propaths(self,G, source, target, cutoff=1, cutprob =0.5):
    #     """ seek all simple_path from source to target

    #     Parameters
    #     ----------

    #     G : networkx Graph Gi
    #     source : tuple 
    #         interaction (node of Gi) 
    #     target : tuple 
    #         interaction (node of Gi) 
    #     cutoff : int

    #     Notes
    #     -----

    #     adapted from all_simple_path of networkx 

    #     1- Determine all nodes connected to Gi 

    #     """
    #     #print "source :",source
    #     #print "target :",target

    #     if cutoff < 1:
    #         return

    #     visited = [source]
    #     # stack is a list of iterators
    #     stack = [iter(G[source])]
    #     ps = [iter([1.0]*len((G[source])))] 
    #     # lawp = list of airwall position in visited
    #     lawp = []

    #     # while the list of iterators is not void
    #     # import ipdb
    #     # ipdb.set_trace()    
    #     while stack: #
    #         # children is the last iterator of stack

    #         children = stack[-1]
    #         pcd = ps[-1]
    #         # next child
    #         child = next(children, None)
    #         pc = next(pcd,None)
    #         # update number of useful segments
    #         # if there is airwall in visited
    #         # 
            
    #         if child is None  : # if no more child
    #             stack.pop()   # remove last iterator
    #             ps.pop()
    #             visited.pop() # remove from visited list
    #             try:
    #                 lawp.pop()
    #             except:
    #                 pass

    #         elif (pc>cutprob): # check proba
    #             if (len(visited) < (cutoff + sum(lawp))):# if visited list length is less than cutoff 
    #                 if child == target:  # if child is the target point
    #                     #print visited + [target]
    #                     yield visited + [target] # output signature
    #                 elif child not in visited: # else visit other node
    #                     # only visit output nodes
    #                     #pdb.set_trace()
    #                     try:
    #                         dintpro = G[visited[-1]][child]['output']
    #                     except:
    #                         dintpro ={}

    #                     # pnc : probability of next children
    #                     # pc : proba of current parent
    #                     # spnc : sum of proba of next children

    #                     # spnc = sum(dintpro.values())
    #                     pnc = [(v*pc) for v in dintpro.values()]

    #                     stack.append(iter(dintpro.keys()))
    #                     ps.append(iter(pnc))
    #                     #stack.append(iter(G[visited[-1]][child]['output']))
    #                     visited.append(child)
    #                     # check if child (current segment) is an airwall
    #                     if self.L.di[child][0] in self.L.name['AIR']:
    #                         lawp.append(1)
    #                     else:
    #                         lawp.append(0)


    #             else :
    #                 stack.pop()
    #                 ps.pop()
    #                 visited.pop()
    #                 lawp.pop()

    #         else: #len(visited) == cutoff (visited list is too long)
    #             if child == target or target in children:
    #                 #print visited + [target]
    #                 yield visited + [target]

    #             stack.pop()
    #             ps.pop()
    #             visited.pop()
    #             lawp.pop()

    def calsig(self,G,dia={},cutoff=None):
        """ calculates signature

        Parameters
        ----------

        G   : graph
        dia : dictionnary of interactions
        cutoff : integer

        """
        if cutoff < 1:
            return

        di=copy.deepcopy(dia)
        source = 'Tx'
        target = 'Rx'
        d={}

        visited = [source]
        stack = [iter(G[source])]

        out=[]

        while stack:
#            pdb.set_trace()
            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.pop()
                if len(out) !=0:
                    out.pop()
                    out.pop()
            elif len(visited) < cutoff:
                if child == target:
                    lot = len(out)
                    try:
                        d.update({lot:d[lot]+(out)})
                    except:
                        d[lot]=[]
                        d.update({lot:d[lot]+(out)})
#                    yield visited + [target]
                elif child not in visited:
                    visited.append(child)
                    out.extend(di[child])
                    stack.append(iter(G[child]))
            else: #len(visited) == cutoff:
                if child == target or target in children:
#                    yield visited + [target]
                    lot = len(out)
                    try:
                        d.update({lot:d[lot]+(out)})
                    except:
                        d[lot]=[]
                        d.update({lot:d[lot]+(out)})
                stack.pop()
                visited.pop()
                if len(out) !=0:
                    out.pop()
                    out.pop()
        return d

    def exist(self,seq):
        """ verifies if seq exists in signatures

        Parameters
        ----------

        seq : list or np.array()

        Returns
        -------

        boolean

        """
        if type(seq)==list:
            seq = np.array(seq)

        N = len(seq)
        sig = self[N]
        lf = filter(lambda x : (x==seq).all(),sig)
        if len(lf)>0:
            return True,lf
        else:
            return False


    def run(self,cutoff=1,dcut=2):
        """ run signature calculation

        Parameters
        ----------

        cutoff : int
        dcut : int

        """

        lcil=self.L.cycleinline(self.source,self.target)

        if len(lcil) <= 2:
            print 'run1'
            self.run1(cutoff=cutoff)
        else :
            print 'run2'
            self.run2(cutoff=cutoff,dcut=dcut)


    def run1(self,cutoff=2):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path

        Returns
        -------

        sigslist :  numpy.ndarray

        """

        self.cutoff   = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        try:
            self.L.dGi
        except:
            self.L.buildGi2()
        # all the vnodes >0  from the room
        #
        #NroomTx = self.L.pt2ro(tx)
        #NroomRx = self.L.pt2ro(rx)
        #print NroomTx,NroomRx

        #if not self.L.Gr.has_node(NroomTx) or not self.L.Gr.has_node(NroomRx):
        #    raise AttributeError('Tx or Rx is not in Gr')

        # list of interaction in roomTx
        # list of interaction in roomRx
        #ndt = self.L.Gt.node[self.L.Gr.node[NroomTx]['cycle']]['inter']
        #ndr = self.L.Gt.node[self.L.Gr.node[NroomRx]['cycle']]['inter']

        metasig = nx.neighbors(self.L.Gt,self.source)
        metasig = metasig + nx.neighbors(self.L.Gt,self.target)
        metasig = list(np.unique(np.array(metasig)))
        metasig = metasig + [self.source] + [self.target]

        #print "metasig",metasig

        # add cycles separated by air walls
        lca=[]
        for cy in metasig:
            try:
                lca.extend(self.L.dca[cy])
            except:
                pass
        metasig = metasig + lca
        metasig = list(np.unique(np.array(metasig)))

        lis = self.L.Gt.node[self.source]['inter']
        lit = self.L.Gt.node[self.target]['inter']

        # source
        #ndt1 = filter(lambda l: len(eval(l))>2,ndt) # Transmission
        #ndt2 = filter(lambda l: len(eval(l))<3,ndt) # Reflexion

        lisT = filter(lambda l: len(eval(l))>2,lis) # Transmission
        lisR = filter(lambda l: len(eval(l))<3,lis) # Reflexion

        # target
        # ndr1 = filter(lambda l: len(eval(l))>2,ndr) # Transmission
        # ndr2 = filter(lambda l: len(eval(l))<3,ndr) # Reflexion

        litT = filter(lambda l: len(eval(l))>2,lit) # Transmission
        litR = filter(lambda l: len(eval(l))<3,lit) # Reflexion

        # tx,rx : attaching rule
        #
        # tx attachs to out transmisision point
        # rx attachs to in transmission point

        #
        # WARNING : room number <> cycle number
        #

        #ncytx = self.L.Gr.node[NroomTx]['cycle']
        #ncyrx = self.L.Gr.node[NroomRx]['cycle']

        #ndt1 = filter(lambda l: eval(l)[2]<>ncytx,ndt1)
        #ndr1 = filter(lambda l: eval(l)[1]<>ncyrx,ndr1)

        lisT = filter(lambda l: eval(l)[2]<>self.source,lisT)
        litT = filter(lambda l: eval(l)[1]<>self.target,litT)

        #ndt = ndt1 + ndt2
        #ndr = ndr1 + ndr2
        lis  = lisT + lisR
        lit  = litT + litR

        #ntr = np.intersect1d(ndt, ndr)
#        li = np.intersect1d(lis, lit)

        li = []
        for ms in metasig:
            li = li + self.L.Gt.node[ms]['inter']
        li = list(np.unique(np.array(li)))

        dpos = {k:self.L.Gi.pos[k] for k in li}

        Gi = nx.subgraph(self.L.Gi,li)
        Gi.pos = dpos
#        for meta in metasig:
#        Gi = nx.DiGraph()
#        for cycle in metasig:
#            Gi = nx.compose(Gi,self.L.dGi[cycle])

#        # facultative update positions
#        Gi.pos = {}
#        for cycle in metasig:
#            Gi.pos.update(self.L.dGi[cycle].pos)
#        pdb.set_trace()
        #
        #
        #
        # remove diffractions from Gi
        Gi = gidl(Gi)
        # add 2nd order output to edges
        #Gi = edgeout(self.L,Gi)
        Gi = edgeout2(self.L,Gi)
        #pdb.set_trace()
        #for interaction source  in list of source interaction 
        for s in lis:
            #for target interaction in list of target interaction
            for t in lit:

                if (s != t):
                    #paths = list(nx.all_simple_paths(Gi,source=s,target=t,cutoff=cutoff))
                    #paths = list(self.all_simple_paths(Gi,source=s,target=t,cutoff=cutoff))
                    paths = list(self.propaths(Gi,source=s,target=t,cutoff=cutoff))

                    #paths = [nx.shortest_path(Gi,source=s,target=t)]
                else:
                    #paths = [[nt]]
                    paths = [[s]]
                ### supress the followinfg loops .
                for path in paths:

                    sigarr = np.array([],dtype=int).reshape(2, 0)
                    for interaction in path:

                        it = eval(interaction)
                        if type(it) == tuple:
                            if len(it)==2: #reflexion
                                sigarr = np.hstack((sigarr,
                                                np.array([[it[0]],[1]],dtype=int)))
                            if len(it)==3: #transmission
                                sigarr = np.hstack((sigarr,
                                                np.array([[it[0]],[2]],dtype=int)))
                        elif it < 0: #diffraction
                            sigarr = np.hstack((sigarr,
                                                np.array([[it],[3]],dtype=int)))
                    #print sigarr
                    try:
                        self[len(path)] = np.vstack((self[len(path)],sigarr))
                    except:
                        self[len(path)] = sigarr

    def run4(self,cutoff=2,algo='old',bt=False,progress=False):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path
        algo : string
            'old' | 'new'
        bt : bool
            backtrace (allow visit already visited nodes in simple path algorithm)
        progress : bool
            display the time passed in the loop


        Returns
        -------

        sigslist :  numpy.ndarray

        """

        self.cutoff   = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        # Determine meta signature
        # this limits the number of cycles

        #metasig = nx.neighbors(self.L.Gt,self.source)
        #metasig = metasig + nx.neighbors(self.L.Gt,self.target)
        #metasig = list(np.unique(np.array(metasig)))
        #metasig = metasig + [self.source] + [self.target]
        # add cycles separated by air walls
        #lca=[]
        #for cy in metasig:
        #    try:
        #        lca.extend(self.L.dca[cy])
        #    except:
        #        pass
        #metasig = metasig + lca
        #metasig = list(np.unique(np.array(metasig)))

        # list of interaction source
        lis = self.L.Gt.node[self.source]['inter']
        # list of interaction target
        lit = self.L.Gt.node[self.target]['inter']

        # source
        #ndt1 = filter(lambda l: len(eval(l))>2,ndt) # Transmission
        #ndt2 = filter(lambda l: len(eval(l))<3,ndt) # Reflexion

        lisT = filter(lambda l: len(l)>2,lis) # Transmission
        lisR = filter(lambda l: len(l)<3,lis) # Reflexion

        # target
        # ndr1 = filter(lambda l: len(eval(l))>2,ndr) # Transmission
        # ndr2 = filter(lambda l: len(eval(l))<3,ndr) # Reflexion

        litT = filter(lambda l: len(l)>2,lit) # Transmission
        litR = filter(lambda l: len(l)<3,lit) # Reflexion

        # tx,rx : attaching rule
        #
        # tx attachs to out transmisision point
        # rx attachs to in transmission point

        #
        # WARNING : room number <> cycle number
        #

        #ncytx = self.L.Gr.node[NroomTx]['cycle']
        #ncyrx = self.L.Gr.node[NroomRx]['cycle']

        #ndt1 = filter(lambda l: eval(l)[2]<>ncytx,ndt1)
        #ndr1 = filter(lambda l: eval(l)[1]<>ncyrx,ndr1)

        lisT = filter(lambda l: l[2]<>self.source,lisT)
        litT = filter(lambda l: l[1]<>self.target,litT)

        #ndt = ndt1 + ndt2
        #ndr = ndr1 + ndr2
        # list of interaction visible from source
        lis  = lisT + lisR
        # list of interaction visible from target
        lit  = litT + litR

        #ntr = np.intersect1d(ndt, ndr)
#        li = np.intersect1d(lis, lit)

        # list of all interactions
        #li = []
        #for ms in metasig:
        #    li = li + self.L.Gt.node[ms]['inter']
        #li = list(np.unique(np.array(li)))
        #
        # dictionnary interaction:position
        #dpos = {k:self.L.Gi.pos[k] for k in li}
        # extracting sub graph of Gi corresponding to metasiganture
        #Gi = nx.subgraph(self.L.Gi,li)
        #Gi.pos = dpos
        Gi = self.L.Gi
        Gi.pos = self.L.Gi.pos
#        for meta in metasig:
#        Gi = nx.DiGraph()
#        for cycle in metasig:
#            Gi = nx.compose(Gi,self.L.dGi[cycle])

#        # facultative update positions
#        Gi.pos = {}
#        for cycle in metasig:
#            Gi.pos.update(self.L.dGi[cycle].pos)
#        pdb.set_trace()
        #
        # TODO : This has to be changed for handling diffraction
        # 
        # remove diffractions from Gi
        Gi = gidl(Gi)
        # add 2nd order output to edges
        #Gi = edgeout(self.L,Gi)
        #Gi = edgeout2(self.L,Gi)
        #pdb.set_trace()
        lmax = len(lis)*len(lit)
        pe = 0
        tic = time.time()
        tic0 = tic
        #for interaction source  in list of source interaction
        for us,s in enumerate(lis):
            #for target interaction in list of target interaction
            for ut,t in enumerate(lit):

                if progress :
                    ratio = np.round((((us)*len(lis)+ut)/(1.*lmax))*10 )
                    if ratio != pe:
                        pe = ratio
                        toc = time.time()
                        print '~%d ' % (ratio*10),
                        print '%',
                        print '%6.3f %6.3f' % (toc-tic, toc-tic0)
                        tic = toc
                if (s != t):
                    #paths = list(nx.all_simple_paths(Gi,source=s,target=t,cutoff=cutoff))
                    #paths = list(self.all_simple_paths(Gi,source=s,target=t,cutoff=cutoff))
                    if algo=='new':
                        paths = list(self.procone(self.L,Gi,source=s,target=t,cutoff=cutoff))
                    else:
                        paths = list(self.propaths(Gi,source=s,target=t,cutoff=cutoff,bt=bt))

                    #paths = [nx.shortest_path(Gi,source=s,target=t)]
                else:
                    #paths = [[nt]]
                    paths = [[s]]
                ### suppress the following loops .
                for path in paths:

                    sigarr = np.array([],dtype=int).reshape(2, 0)
                    for interaction in path:
                        #print interaction + '->',
                        it = interaction
                        if len(it)==2: #reflexion
                            sigarr = np.hstack((sigarr,
                                            np.array([[it[0]],[1]],dtype=int)))
                        if len(it)==3: #transmission
                            sigarr = np.hstack((sigarr,
                                            np.array([[it[0]],[2]],dtype=int)))
                        if len(it)==1: #diffraction
                            sigarr = np.hstack((sigarr,
                                                np.array([[it],[3]],dtype=int)))
                    #print sigarr
                    #print ''
                    try:
                        self[len(path)] = np.vstack((self[len(path)],sigarr))
                    except:
                        self[len(path)] = sigarr


    def run5(self,cutoff=2,algo='old',bt=False,progress=False,diffraction=True):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path
        algo: string
            'old' : call propaths2
            'new' : call procone2
        bt : bool
            backtrace (allow to visit already visited nodes in simple path algorithm)
        progress : bool
            display the time passed in the loop


        Returns
        -------

        sigslist :  numpy.ndarray

        See Also
        --------

        pylayers.simul.link.Dlink.eval
        pylayers.antprop.signature.Signatures.propath2
        pylayers.antprop.signature.Signatures.procone2

        """

        self.cutoff   = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        # list of interactions visible from source
        lisT,lisR,lisD = self.L.intercy(self.source,typ='source')
        if diffraction:
            lis  = lisT + lisR + lisD
        else:
            lis  = lisT + lisR

        # list of interactions visible from target
        litT,litR,litD = self.L.intercy(self.target,typ='target')

        if diffraction:
           lit  = litT + litR + litD
        else:
           lit  = litT + litR
        #print "source,lis :",self.source,lis
        #print "target,lit :",self.target,lit


        Gi = self.L.Gi
        Gi.pos = self.L.Gi.pos
        #
        # remove diffractions from Gi
        if not diffraction:
            Gi = gidl(Gi)

        # initialize dout dictionnary
        dout = {}

        # progresss stuff...
        lmax = len(lis)*len(lit)
        pe = 0
        tic = time.time()
        tic0 = tic
        # lis=lis+lit
        # lit=lis+lit
        #for interaction source  in list of source interactions
        for us,s in enumerate(lis):
            #for target interaction in list of target interactions
            #print "---> ",s

            for ut,t in enumerate(lit):
                #print "   ---> ",t
                # progress bar
                if progress :

                    ratio = np.round((((us)*len(lit)+ut)/(1.*lmax))*10 )
                    if ratio > pe:
                        pe = ratio
                        toc = time.time()
                        print '~%d ' % (ratio*10),
                        print '%',
                        print '%6.3f %6.3f' % (toc-tic, toc-tic0)
                        tic = toc

                # if source and target interaction are different
                # and R | T
                #if ((type(eval(s))==tuple) & (s != t)):
                if (s != t):
                    if algo=='new':
                        dout = self.procone2(self.L,Gi,dout=dout,source=s,target=t,cutoff=cutoff)
                    elif algo == 'old' :
                        dout = self.propaths2(Gi,source=s,target=t,dout=dout,cutoff=cutoff,bt=bt)
                    elif algo == 'dij':
                        dout = self.short_propath(Gi,source=s,target=t,dout=dout,cutoff=cutoff)
                        # dout = self.short_propath(Gi,source=t,target=s,dout=dout,cutoff=cutoff)
                else:
                    try:
                        if [s[0],len(s)] not in dout[1]:
                            dout[1].append([s[0],len(s)])
                    except:
                        dout[1]=[]
                        dout[1].append([s[0],len(s)])

        for k in dout.keys():
            adout = np.array((dout[k]))
            shad  = np.shape(adout)
            # manage the case of signatures with only 1 interaction
            if k == 1:
                adout = adout.reshape(shad[0],1,shad[1])
                shad = np.shape(adout)
            # rehape (rays * 2 , interaction)
            # the 2 dimensions come from the signature definition :
            # 1st row = segment index
            # 2nd row = type of interaction
            self[k] = adout.swapaxes(1,2).reshape(shad[0]*shad[2],shad[1])





    def run7mt(self,cutoff=2,algo='old',bt=False,progress=False,diffraction=True,threshold=0.1):
        """ get signatures (in one list of arrays) between tx and rx
            multithreaded version

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path
        algo: string
            'old' : call propaths2
            'new' : call procone2
        bt : bool
            backtrace (allow to visit already visited nodes in simple path algorithm)
        progress : bool
            display the time passed in the loop


        Returns
        -------

        sigslist :  numpy.ndarray

        See Also
        --------

        pylayers.simul.link.Dlink.eval
        pylayers.antprop.signature.Signatures.propath2
        pylayers.antprop.signature.Signatures.procone2

        """

        self.cutoff   = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        # list of interactions visible from source
        lisT,lisR,lisD = self.L.intercy(self.source,typ='source')
        if diffraction:
            lis  = lisT + lisR + lisD
        else:
            lis  = lisT + lisR

        # list of interactions visible from target
        litT,litR,litD = self.L.intercy(self.target,typ='target')

        if diffraction:
           lit  = litT + litR + litD
        else:
           lit  = litT + litR
        #print "source,lis :",self.source,lis
        #print "target,lit :",self.target,lit


        Gi = self.L.Gi
        Gi.pos = self.L.Gi.pos
        #
        # remove diffractions from Gi
        if not diffraction:
            Gi = gidl(Gi)

        # initialize dout dictionnary
        dout = {}

        # progresss stuff...
        lmax = len(lis)*len(lit)
        pe = 0
        tic = time.time()
        tic0 = tic
        #for interaction source  in list of source interactions

        def pathfinder(dsig,s,t,Gi):
            visited = [s]
            # stack is a list of iterators
            stack = [iter(Gi[s])]
            # lawp = list of airwall position in visited
            lawp = []
            # while the list of iterators is not void
            # import ipdb
            # ipdb.set_trace()
            while stack: #
                # children is the last iterator of stack
                children = stack[-1]
                # next child

                child = next(children, None)

                # update number of useful segments
                # if there is airwall in visited
                if child is None  : # if no more child
                    stack.pop()   # remove last iterator
                    visited.pop() # remove from visited list
                    try:
                        lawp.pop()
                    except:
                        pass

                

                elif (len(visited) < (cutoff + sum(lawp))) and sum(lawp)<5  :# if visited list length is less than cutoff

                    if child == t:  # if child is the target point
                        #print visited + [target]
                        path = visited + [t]
                        nstr = np.array(map(lambda x: x[0],path))
                        typ  = np.array(map(lambda x: len(x),path))
                        try:
                            dsig[len(typ)]=np.vstack((dsig[len(typ)],nstr,typ))
                        except:
                            dsig[len(typ)]=np.vstack((nstr,typ))
                        #try:
                        #    dout[len(path)].append([[p[0],len(p)] for p in path])
                        #except:
                        #    dout[len(path)]=[]
                        #    dout[len(path)].append([[p[0],len(p)] for p in path])
                        #yield visited + [target] # output signature
                    elif (child not in visited) or (bt): # else visit other node
                        # only visit output nodes except if bt
                        #pdb.set_trace()
                        try:
                            nexti  = Gi[visited[-1]][child]['output'].keys()
                            #prob  = Gi[visited[-1]][child]['output'].values()
                            #nexti = map(lambda x:x[0]
                            #               ,filter(lambda x
                            #                       :x[1]>threshold,zip(out,prob)))
                        except:
                            nexti = []

                        stack.append(iter(nexti))
                        #stack.append(iter(G[visited[-1]][child]['output']))
                        visited.append(child)
                        # check if child (current segment) is an airwall
                        # warning not efficient if many airwalls
                        if child[0] in self.L.name['AIR']:
                            lawp.append(1)
                        else:
                            lawp.append(0)



                else: #len(visited) == cutoff (visited list is too long)
                    if child == t or t in children:
                        path = visited + [t]
                        nstr = np.array(map(lambda x: x[0],path))
                        typ  = np.array(map(lambda x: len(x),path))
                        try:
                            dsig[len(typ)]=np.vstack((dsig[len(path)],nstr,typ))
                        except:
                            #print "non existing : ",len(path)
                            dsig[len(typ)]=np.vstack((nstr,typ))
                        #print visited + [target]
                        #yield visited + [target]

                    stack.pop()
                    visited.pop()
                    try:
                        lawp.pop()
                    except:
                        pass


        # import multiprocessing as mpc
        import threading as thg

        # manager = mpc.Manager()
        # dsig = manager.dict()
        jobs = []
        for us,s in enumerate(lis):
            #for target interaction in list of target interactions
            #print "---> ",s

            for ut,t in enumerate(lit):
                #print "   ---> ",t
                # progress bar
                if progress :

                    ratio = np.round((((us)*len(lit)+ut)/(1.*lmax))*10 )
                    if ratio > pe:
                        pe = ratio
                        toc = time.time()
                        print '~%d ' % (ratio*10),
                        print '%',
                        print '%6.3f %6.3f' % (toc-tic, toc-tic0)
                        tic = toc

                # if source and target interaction are different
                # and R | T
                #if ((type(eval(s))==tuple) & (s != t)):
                if (s != t):
                    # p = mpc.Process(target=pathfinder, args=(dsig,s,t,Gi))
                    p = thg.Thread(target=pathfinder, args=(self,s,t,Gi))
                    jobs.append(p)
                    p.start()
                    p.join()
                else: # s==t
                    nstr = np.array([s[0]])
                    typ  = np.array([len(s)])
                    try:
                        self[1]=np.vstack((self[1],nstr,typ))
                    except:
                        #print "non existing : ",len(path)
                        self[1]=np.vstack((nstr,typ))








    def run7(self,cutoff=2,algo='old',bt=False,progress=False,diffraction=True,threshold=0.1):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path
        algo: string
            'old' : call propaths2
            'new' : call procone2
        bt : bool
            backtrace (allow to visit already visited nodes in simple path algorithm)
        progress : bool
            display the time passed in the loop


        Returns
        -------

        sigslist :  numpy.ndarray

        See Also
        --------

        pylayers.simul.link.Dlink.eval
        pylayers.antprop.signature.Signatures.propath2
        pylayers.antprop.signature.Signatures.procone2

        """

        self.cutoff   = cutoff
        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        # list of interactions visible from source
        lisT,lisR,lisD = self.L.intercy(self.source,typ='source')
        if diffraction:
            lis  = lisT + lisR + lisD
        else:
            lis  = lisT + lisR

        # list of interactions visible from target
        litT,litR,litD = self.L.intercy(self.target,typ='target')

        if diffraction:
           lit  = litT + litR + litD
        else:
           lit  = litT + litR
        #print "source,lis :",self.source,lis
        #print "target,lit :",self.target,lit


        Gi = self.L.Gi
        Gi.pos = self.L.Gi.pos
        #
        # remove diffractions from Gi
        if not diffraction:
            Gi = gidl(Gi)

        # initialize dout dictionnary
        dout = {}

        # progresss stuff...
        lmax = len(lis)*len(lit)
        pe = 0
        tic = time.time()
        tic0 = tic
        #for interaction source  in list of source interactions
        for us,s in enumerate(lis):
            #for target interaction in list of target interactions
            #print "---> ",s

            for ut,t in enumerate(lit):
                #print "   ---> ",t
                # progress bar
                if progress :

                    ratio = np.round((((us)*len(lit)+ut)/(1.*lmax))*10 )
                    if ratio > pe:
                        pe = ratio
                        toc = time.time()
                        print '~%d ' % (ratio*10),
                        print '%',
                        print '%6.3f %6.3f' % (toc-tic, toc-tic0)
                        tic = toc

                # if source and target interaction are different
                # and R | T
                #if ((type(eval(s))==tuple) & (s != t)):
                if (s != t):

                    visited = [s]
                    # stack is a list of iterators
                    stack = [iter(Gi[s])]
                    # lawp = list of airwall position in visited
                    lawp = []
                    # while the list of iterators is not void
                    # import ipdb
                    # ipdb.set_trace()
                    while stack: #
                        # children is the last iterator of stack
                        children = stack[-1]
                        # next child

                        child = next(children, None)

                        # update number of useful segments
                        # if there is airwall in visited
                        if child is None  : # if no more child
                            stack.pop()   # remove last iterator
                            visited.pop() # remove from visited list
                            try:
                                lawp.pop()
                            except:
                                pass

                        

                        elif (len(visited) < (cutoff + sum(lawp))) :# if visited list length is less than cutoff
                            if child == t:  # if child is the target point
                                #print visited + [target]
                                path = visited + [t]
                                nstr = np.array(map(lambda x: x[0],path))
                                typ  = np.array(map(lambda x: len(x),path))
                                try:
                                    self[len(typ)]=np.vstack((self[len(typ)],nstr,typ))
                                except:
                                    self[len(typ)]=np.vstack((nstr,typ))
                                #try:
                                #    dout[len(path)].append([[p[0],len(p)] for p in path])
                                #except:
                                #    dout[len(path)]=[]
                                #    dout[len(path)].append([[p[0],len(p)] for p in path])
                                #yield visited + [target] # output signature
                            elif (child not in visited) or (bt): # else visit other node
                                # only visit output nodes except if bt
                                #pdb.set_trace()
                                try:
                                    nexti  = Gi[visited[-1]][child]['output'].keys()
                                    # keyprob  = Gi[visited[-1]][child]['output'].items()
                                    # nexti = map(lambda x:x[0]
                                    #               ,filter(lambda x
                                    #                       :x[1]>threshold,keyprob))

                                except:
                                    nexti = []

                                stack.append(iter(nexti))
                                #stack.append(iter(G[visited[-1]][child]['output']))
                                visited.append(child)
                                # check if child (current segment) is an airwall
                                # warning not efficient if many airwalls
                                if child[0] in self.L.name['AIR']:
                                    lawp.append(1)
                                else:
                                    lawp.append(0)



                        else: #len(visited) == cutoff (visited list is too long)
                            if child == t or t in children:
                                path = visited + [t]
                                nstr = np.array(map(lambda x: x[0],path))
                                typ  = np.array(map(lambda x: len(x),path))
                                try:
                                    self[len(typ)]=np.vstack((self[len(path)],nstr,typ))
                                except:
                                    #print "non existing : ",len(path)
                                    self[len(typ)]=np.vstack((nstr,typ))
                                #print visited + [target]
                                #yield visited + [target]

                            stack.pop()
                            visited.pop()
                            try:
                                lawp.pop()
                            except:
                                pass

                else: # s==t
                    nstr = np.array([s[0]])
                    typ  = np.array([len(s)])
                    try:
                        self[1]=np.vstack((self[1],nstr,typ))
                    except:
                        #print "non existing : ",len(path)
                        self[1]=np.vstack((nstr,typ))

    def run6(self,bt=False,progress=False,diffraction=True,cutoff=8):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

        cutoff : int
            limit the exploration of all_simple_path
        bt : bool
            backtrace (allow to visit already visited nodes in simple path algorithm)
        progress : bool
            display the time passed in the loop


        Returns
        -------

        sigslist :  numpy.ndarray

        See Also
        --------

        pylayers.simul.link.Dlink.eval
        pylayers.antprop.signature.Signatures.propath2
        pylayers.antprop.signature.Signatures.procone2

        """

        self.filename = self.L.filename.split('.')[0] +'_' + str(self.source) +'_' + str(self.target) +'_' + str(self.cutoff) +'.sig'

        # list of interactions visible from source
        lisT,lisR,lisD = self.L.intercy(self.source,typ='source')
        if diffraction:
            lis  = lisT + lisR + lisD
        else:
            lis  = lisT + lisR

        # list of interactions visible from target
        litT,litR,litD = self.L.intercy(self.target,typ='target')

        if diffraction:
           lit  = litT + litR + litD
        else:
           lit  = litT + litR
        print "source,lis :",self.source,lis
        print "target,lit :",self.target,lit


        Gi = self.L.Gi
        Gi.pos = self.L.Gi.pos
        #
        # remove diffractions from Gi
        if not diffraction:
            Gi = gidl(Gi)

        lmax = len(lis)*len(lit)
        pe = 0
        tic = time.time()
        tic0 = tic
        #for interaction source  in list of source interactions
        for us,s in enumerate(lis):
            #for target interaction in list of target interactions
            #print "---> ",s

            for ut,t in enumerate(lit):
                #print "   ---> ",t
                # progress bar
                if progress :

                    ratio = np.round((((us)*len(lit)+ut)/(1.*lmax))*10 )
                    if ratio > pe:
                        pe = ratio
                        toc = time.time()
                        print '~%d ' % (ratio*10),
                        print '%',
                        print '%6.3f %6.3f' % (toc-tic, toc-tic0)
                        tic = toc

                # if source and target interaction are different
                # and R | T
                #if ((type(eval(s))==tuple) & (s != t)):
                if (s != t):
                    level = 0
                    nextlevel={s:Gi[s]}   # list of nodes to check at next level
                    paths={s:[s]}         # paths dictionary  (paths to key from source)

                    getout = False
                    while nextlevel:
                        thislevel = nextlevel
                        nextlevel = {}
                        for v in thislevel:
                            for w in thislevel[v]:
                                # reach a node which is not in paths
                                paths = paths[v]+[w]
                                out  = Gi[v][w]['output'].keys()
                                prob = Gi[v][w]['output'].values()
                                nextlevel[w] = map(lambda x:x[0]
                                                   ,filter(lambda x
                                                           :x[1]>0.6,zip(out,prob)))
                                # get to target
                                if w == t:
                                    nstr = np.array(map(lambda x: x[0],paths[w]))
                                    typ  = np.array(map(lambda x: len(x),paths[w]))
                                    getout = True
                                    #del(paths[w])
                                    try:
                                        self[len(typ)]=np.vstack((self[len(typ)],nstr,typ))
                                    except:
                                        self[len(typ)]=np.vstack((nstr,typ))
                        level=level+1
                        if (cutoff is not None and cutoff >= level):  break

                else:
                    pass
                    #try:
                    #    if [s[0],len(s)] not in dout[1]:
                    #        dout[1].append([s[0],len(s)])
                    #except:
                    #    dout[1]=[]
                    #    dout[1].append([s[0],len(s)])

    def run2(self,cutoff=1,dcut=2):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

            cutoff : limit the exploration of all_simple_path

        Returns
        -------

            sigslist = numpy.ndarray

        """
#        try:
#            self.L.dGi
#        except:
#            self.L.buildGi2()

        # all the vnodes >0  from the room
        #
        #NroomTx = self.L.pt2ro(tx)
        #NroomRx = self.L.pt2ro(rx)
        #print NroomTx,NroomRx

        #if not self.L.Gr.has_node(NroomTx) or not self.L.Gr.has_node(NroomRx):
        #    raise AttributeError('Tx or Rx is not in Gr')

        # list of interaction in roomTx
        # list of interaction in roomRx
        #ndt = self.L.Gt.node[self.L.Gr.node[NroomTx]['cycle']]['inter']
        #ndr = self.L.Gt.node[self.L.Gr.node[NroomRx]['cycle']]['inter']


#        lisT = filter(lambda l: len(eval(l))>2,lis) # Transmission
#        lisR = filter(lambda l: len(eval(l))<3,lis) # Reflexion

#        # target
#        # ndr1 = filter(lambda l: len(eval(l))>2,ndr) # Transmission
#        # ndr2 = filter(lambda l: len(eval(l))<3,ndr) # Reflexion

#        litT = filter(lambda l: len(eval(l))>2,lit) # Transmission
#        litR = filter(lambda l: len(eval(l))<3,lit) # Reflexion

#        # tx,rx : attaching rule
#        #
#        # tx attachs to out transmisision point
#        # rx attachs to in transmission point

#        #
#        # WARNING : room number <> cycle number
#        #

#        #ncytx = self.L.Gr.node[NroomTx]['cycle']
#        #ncyrx = self.L.Gr.node[NroomRx]['cycle']

#        #ndt1 = filter(lambda l: eval(l)[2]<>ncytx,ndt1)
#        #ndr1 = filter(lambda l: eval(l)[1]<>ncyrx,ndr1)

#        lisT = filter(lambda l: eval(l)[2]<>self.source,lisT)
#        litT = filter(lambda l: eval(l)[1]<>self.target,litT)

#        #ndt = ndt1 + ndt2
#        #ndr = ndr1 + ndr2
#        lis  = lisT + lisR
#        lit  = litT + litR

#        #ntr = np.intersect1d(ndt, ndr)
#        li = np.intersect1d(lis, lit)


#        for meta in metasig:
#            Gi = nx.DiGraph()
#            for cycle in meta:
#                Gi = nx.compose(Gi,self.L.dGi[cycle])
#            # facultative update positions
#            Gi.pos = {}
#            for cycle in meta:
#                Gi.pos.update(self.L.dGi[cycle].pos)
#            #
#            #
#            #
#        metasig=self.lineofcycle(cs,ct)

############################################################
##
##      1. the sequence of cycle between cycle source cs and
##      cycle target ct are obtained via cycleinline method
##
##      2. all cycles adjscent at least to one of the previously
##      obtained cycles are appended to the list lca (list of cycle around)
##
##      3. It is then required to add all cycles
##      connected to the previous ones via an air wall.
##
##      lca is used to build the sliding graph of interactions
##      it is important that lcil remains ordered this is not the case
##      for lca



        cs = self.source
        ct = self.target
        lcil=self.L.cycleinline(cs,ct)
        lca = [] # list of cycle around
        for cy in lcil:
            ncy = nx.neighbors(self.L.Gt,cy)
            lca = lca+ncy
        lca = list(np.unique(np.array(lca)))
        lca = lcil
        lcair=[]
        for cy in lca:
            try:
                lcair.extend(self.L.dca[cy])
            except:
                pass
        lca = lca + lcair
        lca = list(np.unique(np.array(lca)))
        #
        # extract list of interactions from list of cycles lca
        #
        li = []
        for ms in lca:
            li = li + self.L.Gt.node[ms]['inter']
        # enforce unicity of interactions in list li
        li = list(np.unique(np.array(li)))

        # extract dictionnary of interactions position
        dpos = {k:self.L.Gi.pos[k] for k in li}

        # build the subgraph of L.Gi with only the selected interactions
        Gi = nx.subgraph(self.L.Gi,li)
        Gi.pos = dpos

        Gf = nx.DiGraph()
        Gf.pos = {}
        # remove diffractions points from Gi
        Gi = gidl(Gi)
        # add 2nd order output to edges
        Gi = edgeout(self.L,Gi)
        #for interaction source  in list of source interaction

############################################################
#        filter list of interactions in termination cycles

        # list of interactions belonging to source
        lis = self.L.Gt.node[lcil[0]]['inter']

        # list of interactions belonging to target
        lit = self.L.Gt.node[lcil[-1]]['inter']

        # filter lis remove transmission coming from outside
        lli   = []
        lisR  = filter(lambda l: len(eval(l))==2,lis)
        lisT  = filter(lambda l: len(eval(l))==3,lis)
        lisTo = filter(lambda l: eval(l)[2]<>cs,lisT)
        lli = lisR + lisTo
        # for li in lis:
        #     ei = eval(li)
        #     if len(ei)==2:
        #        lli.append(li)
        #    if len(ei)==3:
        #        if ei[2]<>cs:
        #           lli.append(li)
        # filter lit remove transmission going outside
        llt = []
        litR  = filter(lambda l: len(eval(l))==2,lit)
        litT  = filter(lambda l: len(eval(l))==3,lit)
        litTi = filter(lambda l: eval(l)[2]==ct,litT)
        llt = litR + litTi
        #for li in lit:
        #    ei = eval(li)
        #    if len(ei)==2:
        #        llt.append(li)
        #    if len(ei)==3:
        #        if ei[2]==ct:
        #           llt.append(li)
        lis = lli
        lit = llt


#################################################
#       propaths (a.k.a. all simple path) per adjacent cycles along cycles in line
#       Obtaining Gf: filtred graph of Gi with Gc ( rename Gt in Gc )

        for ic in np.arange(len(lcil)-2):
            lsource = []
            ltarget = []
            linter = self.L.Gt.node[lcil[ic]]['inter']
            # determine list of sources
            if ic>0:
                ls = self.L.Gt[lcil[ic]][lcil[ic+1]]['segment']
                for source in ls:
                    lsource.append(str((source, lcil[ic], lcil[ic+1])))
            else:
                lsource = lis

            # determine list of targets
            if ic+2 < len(lcil)-1:
            #if ic+3 < len(lcil)-1:
                lt = self.L.Gt[lcil[ic+1]][lcil[ic+2]]['segment']
                #lt = self.L.Gt[lcil[ic+2]][lcil[ic+3]]['segment']
                for target in lt:
                    ltarget.append(str((target , lcil[ic+1], lcil[ic+2])))
                    #ltarget.append(str((target , lcil[ic+2], lcil[ic+3])))
            else:
                ltarget = lit

            lt   = filter(lambda l: len(eval(l))==3,linter)
            #lti = filter(lambda l: eval(l)[2]==lcil[ic+1],lt)
            lto = filter(lambda l: eval(l)[2]<>lcil[ic],lt)
            ltom = filter(lambda l: eval(l)[2]!=lcil[ic-1],lto)
            ltomp = filter(lambda l: eval(l)[2]!=lcil[ic+1],ltom)

            lsource = lsource + ltomp
            #pdb.set_trace()
            for s in lsource :
                #print s
                for t in ltarget:
                    #print t
                    paths = list(self.propaths(Gi,source=s,target=t,cutoff=cutoff))
                    for path in paths:
                        itm1 = path[0]
                        if itm1 not in Gf.node.keys():
                            Gf.add_node(itm1)
                            Gf.pos[itm1]=self.L.Gi.pos[itm1]
                        for it in path[1:]:
                            if it not in Gf.node.keys():
                                Gf.add_node(it)
                                Gf.pos[it]=self.L.Gi.pos[it]
                            Gf.add_edge(itm1,it)
                            itm1 = it
#                        else:
#                            #paths = [[nt]]
#                            paths = [[s]]


################################################################
#       Obtain position of centroid of cycles source and target


        poly1 = self.L.Gt.node[cs]['polyg']
        cp1 = poly1.centroid.xy

        poly2 = self.L.Gt.node[ct]['polyg']
        cp2 = poly2.centroid.xy
        pcs = np.array([cp1[0][0],cp1[1][0]])
        pct = np.array([cp2[0][0],cp2[1][0]])

        Gf.add_node('Tx')
        Gf.pos['Tx']=tuple(pcs[:2])

        for i in self.L.Gt.node[cs]['inter']:
            if i in  Gf.nodes():
                Gf.add_edge('Tx',i)

        Gf.add_node('Rx')
        Gf.pos['Rx']=tuple(pct[:2])

        for i in self.L.Gt.node[ct]['inter']:
            if i in  Gf.nodes():
                Gf.add_edge(i,'Rx')
        # a =[ 0,  1,  2,  1,  4,  1,  6,  1,  8,  1, 10, 1]
        # aa = np.array(a)
        # X=aa.reshape((2,3,2)) # r x i x 2
        # Y=X.swapaxes(0,2) # 2 x i x r



        self.Gf = Gf
        print 'signatures'
        co = nx.dijkstra_path_length(Gf,'Tx','Rx')
        sig = self.calsig(Gf,dia=self.L.di,cutoff=co+dcut)


        for k in sig:
            ns = len(sig[k])
            nbi = k/2
            nr = ns/k
            self[nbi]=(np.array(sig[k]).reshape(nr,nbi,2)).swapaxes(0,2)


        d={}

        for k in self :
            a= self[k]
            nbr = np.shape((a[0]))[1]
            d[k]=np.zeros((2*nbr,k),dtype=int)
            for r in range(nbr):
                for i in range(k):
                    d[k][2*r,i]=a[0,i,r]
                    d[k][2*r+1,i]=a[1,i,r]
        self.update(d)

    def run3(self,cutoff=1,dcut=2):
        """ get signatures (in one list of arrays) between tx and rx

        Parameters
        ----------

            cutoff : limit the exploration of all_simple_path

        Returns
        -------

            sigslist = numpy.ndarray

        """

############################################################
##
##      1. the sequence of cycle between cycle source cs and
##      cycle target ct are obtained via cycleinline method
##
##      2. all cycles adjscent at least to one of the previously
##      obtained cycles are appended to the list lca (list of cycle around)
##
##      3. It is then required to add all cycles
##      connected to the previous ones via an air wall.
##
##      lca is used to build the sliding graph of interactions
##      it is important that lcil remains ordered this is not the case
##      for lca

        # cs : cycle source
        cs = self.source
        # ct : cycle target
        ct = self.target
        polys = self.L.Gt.node[cs]['polyg']
        # cps : centroid point source
        cps = polys.centroid.xy
        polyt = self.L.Gt.node[ct]['polyg']
        # cpt : centroid point target
        cpt = polyt.centroid.xy
        ps = np.array([cps[0][0],cps[1][0]])
        pt = np.array([cpt[0][0],cpt[1][0]])
        v = pt-ps
        mv = np.sqrt(np.sum(v*v,axis=0))
        vn = v/mv
        lcil = self.L.cycleinline(cs,ct)

        # dac : dictionary of adjascent cycles
        dac = {}
        # dfl : dictionnary of fronlines
        dfl = {}

        for cy in lcil:
            dfl[cy] = []

            nghb = nx.neighbors(self.L.Gt,cy)
            dac[cy] = nghb
            poly1 = self.L.Gt.node[cy]['polyg']
            cp1 = poly1.centroid.xy
            p1 = np.array([cp1[0][0],cp1[1][0]])

            for cya in nghb:
                if cy == 13:
                    pdb.set_trace()
                poly2 = self.L.Gt.node[cya]['polyg']
                cp2 = poly2.centroid.xy
                p2 = np.array([cp2[0][0],cp2[1][0]])
                vp = p2-p1
                m2 = np.sqrt(np.sum((p2-p1)*(p2-p1),axis=0))
                vpn = vp/m2
                dp = np.dot(vpn,vn)
                # if dot(vn,vpn) >0 cycle cya is ahead
                if dp>0:
                    lsegso = frontline(self.L,cy,vn)
                    for s in lsegso:
                        cyb = filter(lambda n : n <> cy,self.L.Gs.node[s]['ncycles'])
                        if cyb<>[]:
                            dfl[cy].append(str((s,cy,cyb[0])))
            dfl[cy]=np.unique(dfl[cy]).tolist()
        # # list of interactions belonging to source
        # lis = self.L.Gt.node[lcil[0]]['inter']

        # # list of interactions belonging to target
        # lit = self.L.Gt.node[lcil[-1]]['inter']

        # # filter lis remove incoming transmission
        # lli   = []
        # lisR  = filter(lambda l: len(eval(l))==2,lis)
        # lisT  = filter(lambda l: len(eval(l))==3,lis)
        # lisTo = filter(lambda l: eval(l)[2]<>cs,lisT)
        # lis = lisR + lisTo

        # # filter lit remove outgoing transmission
        # llt = []
        # litR  = filter(lambda l: len(eval(l))==2,lit)
        # litT  = filter(lambda l: len(eval(l))==3,lit)
        # litTi = filter(lambda l: eval(l)[2]==ct,litT)
        # lit = litR + litT

        self.ds={}

        for icy in range(len(lcil)-1):

            io = dfl[lcil[icy]]
            io_ = dfl[lcil[icy+1]]
            print io
            print io_
            if icy == 0:
                [self.ds.update({k:[[k]]}) for k in io]

            # remove keys which are not in front line
            # kds = self.ds.keys()
            # for k in kds :
            #     if k not in io:
            #         self.ds.pop(k)

            for j in io_:
                self.ds[j]=[[]]
                for i in io:
                    self.sp(self.L.Gi,i,j,cutoff=2)
            # [self.ds.pop(k) for k in io]

                    # ds[j]
                    # if len(a) == 1:
                    #     if len(ds[j]) <> 0:
                    #         pdb.set_trace()
                    #         [ds[j][k].extend(a[0][:-1]) for k in range(len(ds[j]))]
                    #     else :
                    #         ds[j]=a[0][:-1]
                    # elif len(a)> 1:
                    #     if len(ds[j]) <> 0:
                    #         [[ds[j][k].extend(a[l][:-1]) for k in range(len(ds[j]))] for l in range(len(a))]
                    #     else :
                    #         ds[j]=a[:-1]


            # remove segments which separate two cycles.
            # TODO: See if it worth to implement
            #lsegs = filter(lambda x : x not in interseg,lsegs)
        # add adjascent air cycles
        #lcair=[]
        #for cy in lcil:
        #    try:
        #        lcair.extend(self.L.dca[cy])
        #    except:
        #        pass
        #lca = lca + lcair
        #lca = list(np.unique(np.array(lca)))

        #
        # Reduction of Gi
        #

        #
        # extract list of interactions from list of cycles lca
        #

        li = []
        for cy in dac:
            for cya in dac[cy]:
                li = li + self.L.Gt.node[cya]['inter']
        # enforce unicity of interactions in list li
        li = list(np.unique(np.array(li)))

        # extract dictionnary of interactions position
        dpos = {k:self.L.Gi.pos[k] for k in li}

        # build the subgraph of L.Gi with only the selected interactions
        Gi = nx.subgraph(self.L.Gi,li)
        Gi.pos = dpos

        # remove diffractions points from Gi
        Gi = gidl(Gi)
        # add 2nd order output to edges
        Gi = edgeout(self.L,Gi)
        #for interaction source  in list of source interaction

############################################################
#        filter list of interactions in termination cycles

        # list of interactions belonging to source
        lis = self.L.Gt.node[lcil[0]]['inter']

        # list of interactions belonging to target
        lit = self.L.Gt.node[lcil[-1]]['inter']

        # filter lis remove incoming transmission
        lli   = []
        lisR  = filter(lambda l: len(eval(l))==2,lis)
        lisT  = filter(lambda l: len(eval(l))==3,lis)
        lisTo = filter(lambda l: eval(l)[2]<>cs,lisT)
        lis = lisR + lisTo

        # filter lit remove outgoing transmission
        llt = []
        litR  = filter(lambda l: len(eval(l))==2,lit)
        litT  = filter(lambda l: len(eval(l))==3,lit)
        litTi = filter(lambda l: eval(l)[2]==ct,litT)
        lit = litR + litTi

#################################################
#       propaths (a.k.a. all simple path) per adjacent cycles along cycles in line
#       Obtaining Gf: filtred graph of Gi with Gc ( rename Gt in Gc )

        #
        # Gf : filtered graph
        #
        Gf = nx.DiGraph()
        Gf.pos = {}
        ncycles = len(lcil)

        ltarget = []
        lsource = []
        for ic in np.arange(ncycles-1):

            # determine list of sources and targets
            # The famous so called saute mouton algorithm
            if ic==0:
                lsource = lis
                ltarget = dfl[lcil[0]]
            elif ic==ncycles-2:
                lsource = ltarget
                ltarget = lit
            else:
                lsource = ltarget
                ltarget = dfl[lcil[ic]]

            for s in lsource :
                #print s
                for t in ltarget:
                    #print t
                    paths = list(self.propaths(Gi,source=s,target=t,cutoff=cutoff))

                    for path in paths:
                        itm1 = path[0]
                        if itm1 not in Gf.node.keys():
                            Gf.add_node(itm1)
                            Gf.pos[itm1]=self.L.Gi.pos[itm1]
                        for it in path[1:]:
                            if it not in Gf.node.keys():
                                Gf.add_node(it)
                                Gf.pos[it]=self.L.Gi.pos[it]
                            Gf.add_edge(itm1,it)
                            itm1 = it


################################################################
#       Obtain position of centroid of cycles source and target

        poly1 = self.L.Gt.node[cs]['polyg']
        cp1 = poly1.centroid.xy

        poly2 = self.L.Gt.node[ct]['polyg']
        cp2 = poly2.centroid.xy
        pcs = np.array([cp1[0][0],cp1[1][0]])
        pct = np.array([cp2[0][0],cp2[1][0]])

        Gf.add_node('Tx')
        Gf.pos['Tx']=tuple(pcs[:2])

        for i in self.L.Gt.node[cs]['inter']:
            if i in  Gf.nodes():
                Gf.add_edge('Tx',i)

        Gf.add_node('Rx')
        Gf.pos['Rx']=tuple(pct[:2])

        for i in self.L.Gt.node[ct]['inter']:
            if i in  Gf.nodes():
                Gf.add_edge(i,'Rx')
        while True:
            culdesac = filter(lambda n: len(nx.neighbors(Gf,n))==0,Gf.nodes())
            culdesac.remove('Rx')
            if len(culdesac)>0:
                Gf.remove_nodes_from(culdesac)
                print culdesac
            else:
                break
        # a =[ 0,  1,  2,  1,  4,  1,  6,  1,  8,  1, 10, 1]
        # aa = np.array(a)
        # X=aa.reshape((2,3,2)) # r x i x 2
        # Y=X.swapaxes(0,2) # 2 x i x r
        self.Gf = Gf
        print 'signatures'
        co = nx.dijkstra_path_length(Gf,'Tx','Rx')
        #pdb.set_trace()
        sig = self.calsig(Gf,dia=self.L.di,cutoff=co+dcut)


        for k in sig:
            ns = len(sig[k])
            nbi = k/2
            nr = ns/k
            self[nbi]=(np.array(sig[k]).reshape(nr,nbi,2)).swapaxes(0,2)


        d={}

        for k in self :
            a= self[k]
            nbr = np.shape((a[0]))[1]
            d[k]=np.zeros((2*nbr,k),dtype=int)
            for r in range(nbr):
                for i in range(k):
                    d[k][2*r,i]=a[0,i,r]
                    d[k][2*r+1,i]=a[1,i,r]
        self.update(d)



    def meta(self):
        G = self.L.Gt
        # metasig = list(nx.all_simple_paths(self.L.Gt,source=self.source,target=self.target,cutoff=cutoff))
        #for cutoff in range(1,5):
        metasig = nx.shortest_path(G,source=self.source,target=self.target)
        for c in metasig:
            try :
                n = np.hstack((n,np.array(G.neighbors(c))))
            except:
                n = np.array(G.neighbors(c))
        n = np.unique(n)
        for d in n:
            try :
                n = np.hstack((n,np.array(G.neighbors(d))))
            except:
                n = np.array(G.neighbors(d))

        return np.unique(n)


    def lineofcycle(self,cs=[],ct=[]):
        """ shortest path between 2 cycle

        Parameters
        ----------

        cs : list
        ct : list

        """
        if cs == []:
            cs = self.source
        if ct == []:
            ct = self.target
        return nx.shortest_path(self.L.Gt,source=cs,target=ct)

    def cones(self,L,i=0,s=0,fig=[],ax=[],figsize=(10,10)):
        """ display cones of an unfolded signature

        Parameters
        ----------

        L : Layout
        i : int
            the interaction block
        s : int
            the signature number in the block
        fig :
        ax  :
        figsize :

        """
        if fig == []:
            fig= plt.figure()
            ax = fig.add_subplot(111)
        elif ax ==[]:
            ax = fig.add_subplot(111)


        pta,phe = self.unfold(L,i=i,s=s)

        # create a global array or tahe segments

        seg = np.vstack((pta,phe))
        lensi = np.shape(seg)[1]

        for s in range(1,lensi):
            pseg0 = seg[:,s-1].reshape(2,2).T
            pseg1 = seg[:,s].reshape(2,2).T
            #
            # create the cone seg0 seg1
            #
            cn = cone.Cone()
            cn.from2segs(pseg0,pseg1)
            fig,ax = cn.show(fig = fig,ax = ax,figsize = figsize)

        return (fig,ax)


    def unfold(self,L,i=0,s=0):
        """ unfold a given signature

        return 2 np.ndarray of pta and phe "aligned"
        (reflexion interaction are mirrored)

        Parameters
        ----------

        L : Layout
        i : int
            the interaction block
        s : int
            the signature number in the block

        Returns
        -------

        pta,phe

        See Also
        --------

        Signature.unfold

        """

        si = Signature(self[i][(2*s):(2*s)+2])
        si.ev(L)
        pta,phe = si.unfold()

        return pta,phe

    def show(self,L,**kwargs):
        """  plot signatures within the simulated environment

        Parameters
        ----------

        L : Layout
        i : list or -1 (default = all groups)
            list of interaction group numbers
        s : list or -1 (default = all sig)
            list of indices of signature in interaction group
        ctx : cycle of tx (optional)
        crx : cycle of rx (optional)
        graph : type of graph to be displayed
        color : string
        alphasig : float
        widthsig : float
        colsig : string
        ms : int
        ctx  : int
        crx :int



        """
        defaults = {'i':-1,
                   's':-1,
                   'fig':[],
                   'ax':[],
                   'graph':'s',
                    'color':'black',
                    'alphasig':1,
                    'widthsig':0.1,
                    'colsig':'black',
                    'ms':5,
                    'ctx':-1,
                    'crx':-1
                   }

        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value

        # display layout
        fig,ax = L.showG(**kwargs)


        if kwargs['ctx']!=-1:
            Tpoly = self.L.Gt.node[kwargs['ctx']]['polyg']
            Tpoly.coul='r'
            Tpoly.plot(fig=fig,ax=ax,color='r')

        if kwargs['crx']!=-1:
            Rpoly = self.L.Gt.node[kwargs['crx']]['polyg']
            Rpoly.plot(fig=fig,ax=ax,color='g')

        # i=-1 all rays
        # else block of interactions i
        if kwargs['i']==-1:
            lgrint = self.keys()
        else:
            lgrint = [kwargs['i']]


        for i in lgrint:
            if kwargs['s']==-1:
                lsig = range(len(self[i])/2)
            else:
                lsig = [kwargs['s']]
            for j in lsig:
                sig = map(lambda x: self.L.Gs.pos[x],self[i][2*j])
                siga = np.array(sig)
                # sig = np.hstack((self.pTx[0:2].reshape((2, 1)),
                #                  np.hstack((self[i]['pt'][0:2, :, j],
                #                  self.pRx[0:2].reshape((2, 1))))
                #                  ))
                ax.plot(siga[:,0], siga[:,1],
                        alpha=kwargs['alphasig'],color=kwargs['colsig'],linewidth=kwargs['widthsig'])
                ax.axis('off')
        return(fig,ax)

    def showi(self,uni=0,us=0):
        """ interactive show

        press n to visit signatures sequentially

        Parameters
        ----------

        uni : index of interaction dictionnary keys
        us : signature index

        """
        plt.ion()
        fig = plt.figure()

        nit = self.keys()
        ni = nit[uni]
        ust = len(self[ni])/2

        polyS = self.L.Gt.node[self.source]['polyg']
        cp1 = polyS.centroid.xy

        polyT = self.L.Gt.node[self.target]['polyg']
        cp2 = polyT.centroid.xy

        ptx = np.array([cp1[0][0],cp1[1][0]])
        prx = np.array([cp2[0][0],cp2[1][0]])

        st='a'

        while st != 'q':
            inter=[]
            ax = fig.add_subplot(111)
            fig,ax=self.L.showG(fig=fig,ax=ax,graph='s')
            title = '# interaction :', ni, 'signature #',us,'/',ust
            ax.set_title(title)

            line = ptx
            # draw terminal points (centroid of source and target cycle)

            ax.plot(ptx[0],prx[1],'xr')
            ax.plot(prx[0],prx[1],'xb')

            if ni not in self.keys():
                print "incorrect number of interactions"
            pos={}

            try:
                for u in self[ni][us*2]:
                    pos.update({u:self.L.Gs.pos[u]})
                    line = np.vstack((line,np.array((self.L.Gs.pos[u]))))
                nx.draw_networkx_nodes(self.L.Gs,pos=pos,nodelist=pos.keys(),node_color='r',ax=ax)

                for ii in self[ni][(us*2)+1]:
                    if ii == 1:
                        inter.append('R')
                    if ii == 2:
                        inter.append('T')
                    if ii == 3:
                        inter.append('D')
            except:
                print "signature index out of bounds of signature"

            line = np.vstack((line,prx))
            ax.plot(line[:,0],line[:,1])
            plt.draw()
            print inter
            st = raw_input()
            ax.cla()
            if st == 'n':
                if us+2 <= ust:
                    us=us+2

                else:
                    uni = uni+1
                    try:
                        ni = nit[uni]
                        ust = len(self[ni])/2
                        us=0
                    except:
                        uni=0
                        ni=nit[uni]
                        us = 0
            else:
                print 'press n for next signature'

    # def raysmt(self,ptx=0,prx=1):
    #     """ from signatures dict to 2D rays
    #         mutithread
            
    #     Parameters
    #     ----------

    #     ptx : numpy.array or int
    #         Tx coordinates is the center of gravity of the cycle number if
    #         type(tx)=int
    #     prx :  numpy.array or int
    #         Rx coordinates is the center of gravity of the cycle number if
    #         type(rx)=int

    #     Returns
    #     -------

    #     rays : Rays

    #     Notes
    #     -----

    #     In the same time the signature of the ray is stored in the Rays object

    #     Todo : Find the best memory implemntation

    #     See Also
    #     --------

    #     Signature.sig2ray

    #     """

    #     if type(ptx)==int:
    #         ptx = np.array(self.L.Gt.pos[ptx])
    #     if type(prx)==int:
    #         prx = np.array(self.L.Gt.pos[prx])

    #     rays = Rays(ptx,prx)

    #     #
    #     # detect LOS situation
    #     #
    #     #
    #     # cycle on a line between 2 cycles
    #     # lc  = self.L.cycleinline(self.source,self.target)

    #     #
    #     # if source and target in the same merged cycle
    #     # and ptx != prx
    #     #
    #     los = shg.LineString(((ptx[0], ptx[1]), (prx[0], prx[1])))

    #     # convex cycle of each point
    #     cyptx = self.L.pt2cy(ptx)
    #     cyprx = self.L.pt2cy(prx)

    #     # merged cycle of each point
    #     polyctx = self.L.Gt.node[cyptx]['polyg']
    #     polycrx = self.L.Gt.node[cyprx]['polyg']

    #     dtxrx = np.sum((ptx-prx)*(ptx-prx))
    #     if dtxrx>1e-15:
    #         if cyptx==cyprx:
    #             if polyctx.contains(los):
    #                 rays.los = True
    #             else:
    #                 rays.los = False

    #     # k : Loop on interaction group
    #     #   l : loop on signature
    #     # --->
    #     #  this part should be a generator
    #     #

    #     def rayproc(tsig,rays):

    #         shsig = np.shape(tsig)
    #         for l in range(shsig[0]/2):
    #             sig = tsig[2*l:2*l+2,:]
    #             ns0 = sig[0,0]
    #             nse = sig[0,-1]
    #             validtx = True
    #             validrx = True

    #             if (ns0<0):
    #                 pD = self.L.Gs.pos[ns0]
    #                 TxD = shg.LineString(((ptx[0], ptx[1]), (pD[0], pD[1])))
    #                 seg = polyctx.intersection(TxD)
    #                 validtx = seg.almost_equals(TxD,decimal=4)
    #                 if not validtx:
    #                     print ns0

    #             if (nse<0):
    #                 pD = self.L.Gs.pos[nse]
    #                 DRx = shg.LineString(((pD[0], pD[1]), (prx[0], prx[1])))
    #                 validrx = polyctx.contains(DRx)
    #                 if not validrx:
    #                     print nse

    #             if validtx & validrx:
    #                 #    print sig
    #                 #    print pD
    #                 s  = Signature(sig)
    #                 #
    #                 # Transform signature into a ray
    #                 # --> sig2ray

    #                 isray,Yi  = s.sig2ray(self.L, ptx[:2], prx[:2])

    #                 if isray:
    #                     Yi = np.fliplr(Yi)
    #                     if k in rays.keys():
    #                         Yi3d = np.vstack((Yi[:, 1:-1], np.zeros((1, k))))
    #                         Yi3d = Yi3d.reshape(3, k, 1)
    #                         rays[k]['pt'] = np.dstack(( rays[k]['pt'], Yi3d))
    #                         rays[k]['sig'] = np.dstack(( rays[k]['sig'],
    #                                                     sig.reshape(2, k, 1)))
    #                     else:
    #                         rays[k] = {'pt': np.zeros((3, k, 1)),
    #                                    'sig': np.zeros((2, k, 1),dtype=int)}
    #                         rays[k]['pt'][0:2, :, 0] = Yi[:, 1:-1]
    #                         rays[k]['sig'][:, :, 0] = sig


    #     import threading as thg
    #     jobs = []

    #     for k in self:
    #         # get signature block with k interactions
    #         tsig = self[k]
    #         p = thg.Thread(target=rayproc, args=(tsig,rays))
    #         jobs.append(p)
    #         p.start()
    #         p.join()

    #     rays.nb_origin_sig = len(self)
    #     rays.origin_sig_name = self.filename
    #     return rays

    def rays(self,ptx=0,prx=1):
        """ from signatures dict to 2D rays

        Parameters
        ----------

        ptx : numpy.array or int
            Tx coordinates is the center of gravity of the cycle number if
            type(tx)=int
        prx :  numpy.array or int
            Rx coordinates is the center of gravity of the cycle number if
            type(rx)=int

        Returns
        -------

        rays : Rays

        Notes
        -----

        In the same time the signature of the ray is stored in the Rays object

        Todo : Find the best memory implemntation

        See Also
        --------

        Signature.sig2ray

        """

        if type(ptx)==int:
            ptx = np.array(self.L.Gt.pos[ptx])
        if type(prx)==int:
            prx = np.array(self.L.Gt.pos[prx])

        rays = Rays(ptx,prx)

        #
        # detect LOS situation
        #
        #
        # cycle on a line between 2 cycles
        # lc  = self.L.cycleinline(self.source,self.target)

        #
        # if source and target in the same merged cycle
        # and ptx != prx
        #
        los = shg.LineString(((ptx[0], ptx[1]), (prx[0], prx[1])))

        # convex cycle of each point
        cyptx = self.L.pt2cy(ptx)
        cyprx = self.L.pt2cy(prx)

        # merged cycle of each point
        polyctx = self.L.Gt.node[cyptx]['polyg']
        polycrx = self.L.Gt.node[cyprx]['polyg']

        dtxrx = np.sum((ptx-prx)*(ptx-prx))
        if dtxrx>1e-15:
            if cyptx==cyprx:
                if polyctx.contains(los):
                    rays.los = True
                else:
                    rays.los = False

        # k : Loop on interaction group
        #   l : loop on signature
        # --->
        #  this part should be a generator
        #
        for k in self:
            # print 'block#',k
            # if k ==3:
            #     import ipdb
            #     ipdb.set_trace()
            # get signature block with k interactions
            tsig = self[k]
            shsig = np.shape(tsig)
            for l in range(shsig[0]/2):
                sig = tsig[2*l:2*l+2,:]
                ns0 = sig[0,0]
                nse = sig[0,-1]
                validtx = True
                validrx = True

                if (ns0<0):
                    pD = self.L.Gs.pos[ns0]
                    TxD = shg.LineString(((ptx[0], ptx[1]), (pD[0], pD[1])))
                    seg = polyctx.intersection(TxD)
                    validtx = seg.almost_equals(TxD,decimal=4)
                    if not validtx:
                        print ns0

                if (nse<0):
                    pD = self.L.Gs.pos[nse]
                    DRx = shg.LineString(((pD[0], pD[1]), (prx[0], prx[1])))
                    validrx = polyctx.contains(DRx)
                    if not validrx:
                        print nse

                if validtx & validrx:
                    #    print sig
                    #    print pD
                    s  = Signature(sig)
                    #
                    # Transform signature into a ray
                    # --> sig2ray

                    isray,Yi  = s.sig2ray(self.L, ptx[:2], prx[:2])

                    if isray:
                        Yi = np.fliplr(Yi)
                        if k in rays.keys():
                            Yi3d = np.vstack((Yi[:, 1:-1], np.zeros((1, k))))
                            Yi3d = Yi3d.reshape(3, k, 1)
                            rays[k]['pt'] = np.dstack(( rays[k]['pt'], Yi3d))
                            rays[k]['sig'] = np.dstack(( rays[k]['sig'],
                                                        sig.reshape(2, k, 1)))
                        else:

                            rays[k] = {'pt': np.zeros((3, k, 1)),
                                       'sig': np.zeros((2, k, 1),dtype=int)}
                            rays[k]['pt'][0:2, :, 0] = Yi[:, 1:-1]
                            rays[k]['sig'][:, :, 0] = sig

        rays.nb_origin_sig = len(self)
        rays.origin_sig_name = self.filename
        return rays


    def raysv(self,ptx=0,prx=1):
    
        """ from signatures dict to 2D rays Vectorized version 

        Parameters
        ----------

        ptx : numpy.array or int
            Tx coordinates is the center of gravity of the cycle number if
            type(tx)=int
        prx :  numpy.array or int
            Rx coordinates is the center of gravity of the cycle number if
            type(rx)=int

        Returns
        -------

        rays : Rays

        Notes
        -----

        This is a vectorized version of Signatures.rays.
        This implementation take advantage of the np.ndarray
        and calculate images and backtrace for block of signatures.
        A block of signature gather all signatures with the same number of interaction.

        For mathematical details see :

        @phdthesis{amiot:tel-00971809,
          TITLE = {{Design of simulation platform joigning site specific radio propagation and human mobility for localization applications}},
          AUTHOR = {Amiot, Nicolas},
          URL = {https://tel.archives-ouvertes.fr/tel-00971809},
          NUMBER = {2013REN1S125},
          SCHOOL = {{Universit{\'e} Rennes 1}},
          YEAR = {2013},
          MONTH = Dec,
          KEYWORDS = {Electromagnetic wave propagation simulation ; Human mobility simulation ; Wireless localization methods ; Position estimation methods in wireless networks ; Vectorized computation ; Ray-tracing ; Ultra wide band ; Simulateur de propagation {\'e}lectromagn{\'e}tique ; Simulateur de mobilit{\'e} humaine ; M{\'e}thodes de localisation sans fils ; M{\'e}thodes d'estimation de la position dans les r{\'e}seaux sans fils ; Calcul informatique vectoris{\'e} ; Outil de trac{\'e} de rayons ; Ultra large bande},
          TYPE = {Theses},
          HAL_ID = {tel-00971809},
          HAL_VERSION = {v1},
        }

        See Also
        --------

        Signatures.image
        Signatures.backtrace

        """
        if type(ptx)==int:
            ptx = np.array(self.L.Gt.pos[ptx])
        
        if type(prx)==int:
            prx = np.array(self.L.Gt.pos[prx])
        

        if len(ptx) == 2:
            ptx= np.r_[ptx,0.5]
        if len(ptx) == 2:
            prx= np.r_[prx,0.5]

        rays = Rays(ptx,prx)

        M = self.image(ptx)
        R = self.backtrace(ptx,prx,M)
        rays.update(R)
        rays.nb_origin_sig = len(self)
        rays.origin_sig_name = self.filename
        return rays

    def backtrace(self, tx, rx, M):
        ''' Warning :
            This is an attempt to vectorize the backtrace process.
            Despite it has been tested on few cases with succes, 
            this is quite new need to be validated !!!


            Parameters
            ----------

                tx : ndarray
                    position of tx (2,)
                rx : ndarray
                    position of tx (2,)
                M : dict
                    position of intermediate point from self.image()

            Return
            -------

                rayp : dict 
                key = number_of_interactions 
                value =ndarray positions of interactions for creating rays

            Notes
            -----
            dictionnary of intermediate coordinated :
            key = number_of_interactions 
            value = nd array M with shape : (2,nb_signatures,nb_interactions)
            and 2 represent x and y coordinates
            

        '''

        if len(tx) > 2:
            tx = tx[:2]
        if len(rx) > 2:
            rx = rx[:2]

        rayp={}
        # loop on number of interactions
        for ninter in self.keys():
            signatures = copy.deepcopy(self[ninter])
            # get segment ids of signature with 4 interactions
            seg = signatures[::2]
            nsig = len(seg)
            # determine positions of points limiting the semgments 
            # 1 get index in L.tahe
            # 2 get associated position in L.pt

            # utahe (2 pt indexes,nb_signatures,nb_interactions)
            utahe = self.L.tahe[:,seg-1]

            # pt : (xycoord (2),pt indexes (2),nb_signatures,nb_interactions)
            pt = self.L.pt[:,utahe]
            #shape =
            # 0 : (x,y) coordinates x=0,y=1
            # 1 : 2 points (linking the semgnet) a=0,b=1
            # 2 : nb of found signatures/segments
            # 3 : nb interaction
            # how to do this into a while loop
            p=rx

            # creating W matrix required in eq (2.70) thesis Nicolas AMIOT
            # Warning W is rolled after and becomes (nsig,4,4)
            W=np.zeros((4,4,nsig))
            I=np.eye(2)[:,:,np.newaxis]*np.ones((nsig))
            W[:2,:2,...] = I
            W[2:4,:2,...] = I

            # once rolled :
            # W (nsig,4,4)
            W = np.rollaxis(W,-1)


            kinter=ninter-1

            ptr = pt
            Mr = copy.deepcopy(M)

            epsilon = 1e-2
            rayp_i = np.zeros((3,nsig,ninter))
            # rayp_i[:2,:,-1]=rx[:,None]
            # backtrace process
            while kinter > -1:
                # Initilization, using the Tx position
                if kinter == ninter-1:
                    p_min_m = p[:,np.newaxis]-Mr[ninter][:,:,kinter]
                else :
                    p_min_m = pvalid[:].T-Mr[ninter][:,:,kinter]

                a_min_b = ptr[:,0,:,kinter]-ptr[:,1,:,kinter]

                # Creating W from  eq (2.71)
                # a_min_b <=> a_{Lh-l}-b_{Lh-l}
                # p_min_m <=> \tilde{p}_{Lh}-\tilde{b}_{Lh-l}

                # W (nsig,4,4)
                # p_min_m (2,nsig)
                # a_min_b (2,nsig)
                W[...,:2,2] = p_min_m.T 
                W[...,2:,3] = a_min_b.T

                # create 2nd member from eq (2.72)
                if kinter == ninter-1:
                    y= np.concatenate((p[:,np.newaxis]*np.ones((nsig)),ptr[:,0,:,kinter]))
                else: 
                    y= np.concatenate((pvalid.T,ptr[:,0,:,kinter]))

                # y once transposed :
                # y (nsig,4)
                y=y.T

                # search and remove point with singular matrix
                invalid_sig=np.where(abs(np.linalg.det(W))<1e-15)

                W = np.delete(W,invalid_sig,axis=0)
                y = np.delete(y,invalid_sig,axis=0)
                ptr = np.delete(ptr,invalid_sig,axis=2)
                Mr[ninter] = np.delete(Mr[ninter],invalid_sig,axis=1)
                rayp_i = np.delete(rayp_i,invalid_sig,axis=1)

                # remove signatures
                usig = np.repeat(invalid_sig[0],2)
                usig[::2]=usig[::2]*2
                usig[1::2]=usig[1::2]*2+1
                signatures = np.delete(signatures,usig,axis=0)


                
                psolved = np.linalg.solve(W,y)

                # np.linalg.solve and sp.linalg.solve don't give the exact same answer
                # one approximate the result from the lower value and the other form the upper
                # alternatively, it can be used :
                # lw=len(W) 
                # psolved = np.empty((lw,4))
                # for zz in xrange(lw):
                #     psolved[zz] = la.solve(W[zz],y[zz])



                # valid ray is : 0 < \alpha < 1 and 0< \beta < 1
                # alpha
                uvalidA= psolved[:,2]>0.
                uvalidB= psolved[:,2]<1.
                # beta
                uvalidC= psolved[:,3] >= epsilon
                uvalidD= psolved[:,3] <=1.-epsilon
                uvalid = np.where(uvalidA & uvalidB & uvalidC & uvalidD)[0]
                
                pvalid = psolved[uvalid,:2]

                # keep only valid rays for ptr and Mr 
                Mr[ninter]=Mr[ninter][:,uvalid,:]
                ptr=ptr[:,:,uvalid,:]
                W = W[uvalid,:,:]

                # remove signatures
                usigv = np.repeat(uvalid,2)
                usigv[::2]=usigv[::2]*2
                usigv[1::2]=usigv[1::2]*2+1
                signatures = signatures[usigv,:]
                

                rayp_i[:2,uvalid,kinter] = pvalid.T
                rayp_i = rayp_i[:,uvalid,:]

                # if no more rays are valid , then quit block 
                # (kinter <0 is the exit while condition)
                if len(uvalid) > 0 :
                    kinter=kinter-1
                else : 
                    kinter = -2

            # rayp_i[:2,:,0]=tx[:,None]
            if len(uvalid) !=0:
                sir1=signatures[::2].T.reshape(ninter,len(usigv)/2)
                sir2=signatures[1::2].T.reshape(ninter,len(usigv)/2)
                sig = np.empty((2,ninter,len(usigv)/2))
                sig[0,:,:]=sir1
                sig[1,:,:]=sir2
                rayp_i=np.swapaxes(rayp_i,1,2)
                rayp.update({ninter:{'pt':rayp_i,'sig':sig.astype('int')}})
        return rayp

    def image(self,tx):
        ''' Warning :
            This is an attempt to vectorize the image process.
            Despite it has been tested on few cases with succes, 
            this is quite new need to be validated !!!


            Parameters
            ----------

                tx : ndarray
                    position of tx (2,)

            Return
            -------

                M : dictionnary

            dictionnary of intermediate coordinated :
            key = number_of_interactions 
            value = nd array M with shape : (2,nb_signatures,nb_interactions)
            and 2 represent x and y coordinates
            

        '''
        if len(tx) > 2:
            tx = tx[:2]

        dM={}
        for ninter in self.keys():

            # get segment ids of signature with ninter interactions
            seg = self[ninter][::2]
            nsig = len(seg)
            # determine positions of points limiting the semgments 
            # 1 get index in L.tahe
            # 2 get associated position in L.pt

            # utahe (2 pt indexes,nb_signatures,nb_interactions)
            utahe = self.L.tahe[:,seg-1]




            # pt : (xycoord (2),pt indexes (2),nb_signatures,nb_interactions)
            pt = self.L.pt[:,utahe]

            # pt shape =
            # 0 : (x,y) coordinates x=0,y=1
            # 1 : 2 points (linking the semgnet) a=0,b=1
            # 2 : nb of found signatures/segments
            # 3 : nb interaction

            ############
            # formula 2.61 -> 2.64 N.AMIOT thesis
            ############
            den = ((pt[0,0,:,:]-pt[0,1,:,:])**2+(pt[1,0,:,:]-pt[1,1,:,:])**2)

            a = ((pt[0,0,:,:]-pt[0,1,:,:])**2-(pt[1,0,:,:]-pt[1,1,:,:])**2)
            a=a/(1.*den)

            b = 2*(pt[0,1,:,:]-pt[0,0,:,:])*(pt[1,1,:,:]-pt[1,0,:,:])
            b=b/(1.*den)

            c= 2*(pt[0,0,:,:]*(pt[1,0,:,:]-pt[1,1,:,:])**2+pt[1,0,:,:]*(pt[0,1,:,:]-pt[0,0,:,:])*(pt[1,0,:,:]-pt[1,1,:,:]))
            c = c/(1.*den)

            d= 2*(pt[0,0,:,:]*(pt[1,0,:,:]-pt[1,1,:,:])*(pt[0,1,:,:]-pt[0,0,:,:])+pt[1,0,:,:]*(pt[0,1,:,:]-pt[0,0,:,:])**2)
            d= d/(1.*den)

            # get segment ids of signature with ninter interactions
            ityp = self[ninter][1::2]
            uT = np.where(ityp[:,1:]==3)
            uR = np.where(ityp[:,1:]==2)
            uD=np.where(ityp[:,1:]==1)

            # create matrix AM which is used to create marix A from eq. 2.65 
            AM = np.eye(2*ninter)[:,:,np.newaxis]*np.ones(nsig)

            # Reflexion MAtrix K (2.59)  
            K=np.array([[a,-b],[-b,-a]])
            # translation vector v (2.60)
            v =np.array(([c,d]))

            ############
            # Create matrix A (2.66) which is fill by blocks
            ############

            

            blocks=np.zeros((2,2,nsig,ninter-1))

            # Reflexion block
            blocks[:,:,uR[0],uR[1]]=-K[:,:,uR[0],uR[1]+1]
            # Transmission block
            blocks[:,:,uT[0],uT[1]]=-np.eye(2)[:,:,np.newaxis]*np.ones((len(uT[0])))
            # Diff block
            blocks[:,:,uD[0],uD[1]]=0.

            # fill the AM mda on the diagonal below the mda diagonal....
            A=pyu.fill_block_diagMDA(AM,blocks,2,-1)

            # The 2nd member y is firslty completly fill, without taking into account that the 1st line differst from others.
            # 1. find which interaction and signature are R|T|D => create a masked array
            # 2. repeat is created because to each signature/interaction correspond a 2x1 column. Repeat allow to have the correct size to fill y
            # 3. fill the 1st line of y to take into consideration that difference.

            # y is the 2nd memeber from from (2.65) and will be filled following (2.67)
            y = np.zeros((2 * ninter,nsig))

            #######
            # Determine where y has to be filed with R|T|D
            #####
            # find the position where there is T|R|D. non continuous => need mask array
            uTf = np.where(ityp==3)
            uRf = np.where(ityp==2)
            uDf =np.where(ityp==1)

            # postiion in signature <=> 2 lines in y . need to repeat to get the correct size
            uRy2=np.repeat(uRf[0],2)
            uRy1=np.repeat(uRf[1],2)
            uRy1=2*uRy1
            uRy1[1::2]=uRy1[::2]+1

            uDy2=np.repeat(uDf[0],2)
            uDy1=np.repeat(uDf[1],2)
            uDy1=2*uDy1
            uDy1[1::2]=uDy1[::2]+1
            try:
                y[uRy1,uRy2]=v[:,uRf[0],uRf[1]].ravel(order='F')
            except: 
                pass #print 'no R'
            try:
                pass
                #uT1mr = np.repeat(uT1m.mask,2,axis=1).T
                # nothing to do. shoould be a zero vector , already initialized by y
            except:
                pass #print 'no T'
            try:
                # NEVER TESTED !!!!!!!!!!!
                y[uDy1,uDy2]=a[uDf]
            except:
                print "signatures.image diffraction line 3672 Not yet tested !"

                pass #print 'no D'

            ######    
            #FIRST LINE specific processing of (2.67)
            ######
            uT0 = np.where(ityp[:,0]==3)[0]
            uR0 = np.where(ityp[:,0]==2)[0]
            uD0 =np.where(ityp[:,0]==1)[0]

            # reflexion 0 (2.67)
            r0 = np.einsum('ijk,j->jk',K[:,:,uR0,0],tx)+v[:,uR0,0]
            # trnasmission 0 (2.67)
            t0 = tx[:,np.newaxis]*np.ones(len(uT0))
            # diff 0 (2.67)
            d0 = a[uD0,0]
            # first line
            y[0:2,uR0]=r0
            y[0:2,uT0]=t0
            y[0:2,uD0]=d0

            # reshape for compliant size with linalg
            A=np.rollaxis(A,-1)
            y=np.rollaxis(y,-1)

            m=np.linalg.solve(A, y)
            M=np.array((m[:,0::2],m[:,1::2]))

            dM.update({ninter:M})
        return dM


class Signature(object):
    """ class Signature

    Attributes
    ----------

    seq : list  of interaction point (edges (>0)  or vertices (<0) [int]
    typ : list of interaction type 1-R 2-T 3-D  [int] 
    pa  : tail point of interaction segmenti (2xN) ndarray
    pb  : head point of interaction segment  (2xN) ndarray
    pc  : center point of interaction segment (2xN) ndarray

    """
    def __init__(self, sig):
        """ object constructor

        Parameters
        ----------

        sig : nd.array or list of interactions

        >>> seq = np.array([[1,5,1],[1,1,1]])
        >>> s = Signature(seq)

        """

        def typinter(l):
            try:
                l = eval(l)
            except:
                pass
            return(len(l))

        def seginter(l):
            try:
                l = eval(l)
            except:
                pass
            return l[0]

        if type(sig)==np.ndarray:
            self.seq = sig[0, :]
            self.typ = sig[1, :]

        if type(sig)==list:
            self.seq = map(seginter,sig)
            self.typ = map(typinter,sig)

    def __repr__(self):
        s = ''
        s = s + str(self.seq) + '\n' 
        s = s + str(self.typ) + '\n'
        return s

    def info(self):
        for k in self.__dict__.keys():
            print k, ':', self.__dict__[k]

    def ev2(self, L):
        """  evaluation of Signature

        Parameters
        ----------

        L : Layout

        Notes
        -----

        This function converts the sequence of interactions into numpy arrays
        which contains coordinates of segments extremities involved in the
        signature. At that level the coordinates of extremities (tx and rx) is
        not known yet.

        members data

        pa  tail of segment  (2xN)
        pb  head of segment  (2xN)
        pc  the center of segment (2xN)

        norm normal to the segment if segment
        in case the interaction is a point the normal is undefined and then
        set to 0

        """
        def seqpointa(k,L=L):
            if k>0:
                ta, he = L.Gs.neighbors(k)
                pa = np.array(L.Gs.pos[ta]).reshape(2,1)
                pb = np.array(L.Gs.pos[he]).reshape(2,1)
                pc = np.array(L.Gs.pos[k]).reshape(2,1)
                nor1 = L.Gs.node[k]['norm']
                norm = np.array([nor1[0], nor1[1]]).reshape(2,1)
            else:
                pa = np.array(L.Gs.pos[k]).reshape(2,1)
                pb = pa
                pc = pc
                norm = np.array([0, 0]).reshape(2,1)
            return(np.vstack((pa,pb,pc,norm)))

        v = np.array(map(seqpointa,self.seq))

        self.pa = v[:,0:2,:]
        self.pb = v[:,2:4,:]
        self.pc = v[:,4:6,:]
        self.norm = v[:,6:,:]


    def evf(self, L):
        """  evaluation of Signature (fast version)

        Parameters
        ----------

        L : Layout

        Notes
        -----

        This function converts the sequence of interactions into numpy arrays
        which contains coordinates of segments extremities involved in the 
        signature. 

        members data 

        pa  tail of segment  (2xN) 
        pb  head of segment  (2xN)  


        """

        N = len(self.seq)
        self.pa = np.empty((2, N))  # tail
        self.pb = np.empty((2, N))  # head

        for n in range(N):
            k = self.seq[n]
            if k > 0:  # segment
                ta, he = L.Gs.neighbors(k)
                self.pa[:, n] = np.array(L.Gs.pos[ta])
                self.pb[:, n] = np.array(L.Gs.pos[he])
            else:      # node
                pa = np.array(L.Gs.pos[k])
                self.pa[:, n] = pa
                self.pb[:, n] = pa

    def ev(self, L):
        """  evaluation of Signature

        Parameters
        ----------

        L : Layout

        Notes
        -----

        This function converts the sequence of interactions into numpy arrays
        which contains coordinates of segments extremities involved in the
        signature.

        At that stage coordinates of extremities (tx and rx) is
        not known yet

        members data

        pa  tail of segment  (2xN)
        pb  head of segment  (2xN)
        pc  the center of segment (2xN)

        norm normal to the segment if segment
        in case the interaction is a point the normal is undefined and then
        set to 0.

        """

        # TODO : use map and filter instead of for loop

        N = len(self.seq)
        self.pa = np.empty((2, N))  # tail
        self.pb = np.empty((2, N))  # head
        self.pc = np.empty((2, N))  # center
        self.norm = np.empty((2, N))

        for n in range(N):
            k = self.seq[n]
            if k > 0:  # segment
                ta, he = L.Gs.neighbors(k)
                norm1 = np.array(L.Gs.node[k]['norm'])
                norm = np.array([norm1[0], norm1[1]])
                self.pa[:, n] = np.array(L.Gs.pos[ta])
                self.pb[:, n] = np.array(L.Gs.pos[he])
                self.pc[:, n] = np.array(L.Gs.pos[k])
                self.norm[:, n] = norm
            else:      # node
                pa = np.array(L.Gs.pos[k])
                norm = np.array([0, 0])
                self.pa[:, n] = pa
                self.pb[:, n] = pa
                self.pc[:, n] = pa
                self.norm[:, n] = norm

    def unfold(self):
        """ unfold a given signature

        returns 2 np.ndarray of pta and phe "aligned"
        reflexion interactions are mirrored

        Returns
        -------

        pta : np.array
        phe : np.array

        """

        lensi = len(self.seq)
        pta = np.empty((2,lensi))
        phe = np.empty((2,lensi))

        pta[:,0] = self.pa[:,0]
        phe[:,0] = self.pb[:,0]

        mirror=[]

        for i in range(1,lensi):

            pam = self.pa[:,i].reshape(2,1)
            pbm = self.pb[:,i].reshape(2,1)

            if self.typ[i] == 2: # R
                for m in mirror:
                    pam = geu.mirror(pam,pta[:,m],phe[:,m])
                    pbm = geu.mirror(pbm,pta[:,m],phe[:,m])
                pta[:,i] = pam.reshape(2)
                phe[:,i] = pbm.reshape(2)
                mirror.append(i)

            elif self.typ[i] == 3 : # T
                for m in mirror:
                    pam = geu.mirror(pam,pta[:,m],phe[:,m])
                    pbm = geu.mirror(pbm,pta[:,m],phe[:,m])
                pta[:,i] = pam.reshape(2)
                phe[:,i] = pbm.reshape(2)

            elif self.typ[i] == 1 : # D
                pass
                # TODO not implemented yet

        return pta,phe

    def evtx(self, L, tx, rx):
        """ evaluate transmitter

        Parameters
        ----------

        L  : Layout
        tx : np.array (2xN)
        rx : np.array (2xM)

        DEPRECATED

        """
        self.pa = tx.reshape(2, 1)
        self.pb = tx.reshape(2, 1)
        self.pc = tx.reshape(2, 1)
        self.typ = np.array([0])
        for k in self.seq:
            if k > 0:
                ta, he = L.Gs.neighbors(k)
                norm1 = L.Gs.node[k]['norm']
                norm = np.array([norm1[0], norm1[1]]).reshape(2, 1)
                pa = np.array(L.Gs.pos[ta]).reshape(2, 1)
                pb = np.array(L.Gs.pos[he]).reshape(2, 1)
                pc = np.array(L.Gs.pos[k]).reshape(2, 1)
                self.pa = np.hstack((self.pa, pa))
                self.pb = np.hstack((self.pb, pb))
                self.pc = np.hstack((self.pc, pc))
                try:
                    self.norm = np.hstack((self.norm, norm))
                except:
                    self.norm = norm
                self.typ = np.hstack((self.typ, np.array([1])))
            else:
                pa = np.array(L.Gs.pos[k]).reshape(2, 1)
                norm = np.array([0, 0]).reshape(2, 1)
                self.pa = np.hstack((self.pa, pa))
                self.pb = np.hstack((self.pb, pa))
                self.pc = np.hstack((self.pc, pa))
                try:
                    self.norm = np.hstack((self.norm, norm))
                except:
                    self.norm = norm
                self.typ = np.hstack((self.typ, np.array([3])))
        self.pa = np.hstack((self.pa, rx.reshape(2, 1)))
        self.pb = np.hstack((self.pb, rx.reshape(2, 1)))
        self.pc = np.hstack((self.pc, rx.reshape(2, 1)))
        self.typ = np.hstack((self.typ, np.array([0])))
        #
        #  vecteur entre deux points adjascents de la signature
        #
        self.v = s.pc[:, 1:] - s.pc[:, :-1]
        self.vn = self.v / np.sqrt(sum(self.v * self.v, axis=0))
        u1 = sum(self.norm * self.vn[:, 0:-1], axis=0)
        u2 = sum(self.norm * self.vn[:, 1:], axis=0)
        self.typ = np.sign(u1 * u2)
        #return(vn)
        #return(typ)


    def image(self, tx):
        """ compute the tx's images with respect to the signature segments

        Parameters
        ----------

        tx : numpy.ndarray

        Returns
        -------

        M : numpy.ndarray

        """

        pa = self.pa
        pb = self.pb
        pab = pb - pa
        alpha = np.sum(pab * pab, axis=0)
        zalpha = np.where(alpha == 0.)
        alpha[zalpha] = 1.

        a = 1 - (2. / alpha) * (pa[1, :] - pb[1, :]) ** 2
        b = (2. / alpha) * (pb[0, :] - pa[0, :]) * (pa[1, :] - pb[1, :])
        c = (2. / alpha) * (pa[0, :] * (pa[1, :] - pb[1, :]) ** 2 +
                            pa[1, :] * (pa[1, :] - pb[1, :]) *
                            (pb[0, :] - pa[0, :]))
        d = (2. / alpha) * (pa[1, :] * (pb[0, :] - pa[0, :]) ** 2 +
                            pa[0, :] * (pa[1, :] - pb[1, :]) *
                            (pb[0, :] - pa[0, :]))

        typ = self.typ
        # number of interactions
        N = np.shape(pa)[1]

        S = np.zeros((N, 2, 2))
        S[:, 0, 0] = -a
        S[:, 0, 1] = b
        S[:, 1, 0] = b
        S[:, 1, 1] = a
        blocks = np.zeros((N - 1, 2, 2))
        A = np.eye(N * 2)

        # detect diffraction
        usig = np.nonzero(typ[1:] == 1)[0]
        if len(usig) > 0:
            blocks[usig, :, :] = np.zeros((2, 2))
        # detect transmission
        tsig = np.nonzero(typ[1:] == 3)[0]
        if len(tsig) > 0:
            #blocks[tsig, :, :] = np.zeros((2, 2))
            blocks[tsig, :, :] = -np.eye(2)
        # detect reflexion
        rsig = np.nonzero(typ[1:] == 2)[0]
        if len(rsig) > 0:
            blocks[rsig, :, :] = S[rsig + 1, :, :]

        A = pyu.fill_block_diag(A, blocks, 2, -1)

        y = np.zeros(2 * N)
        if typ[0] == 2:
            vc0 = np.array([c[0], d[0]])
            v0 = np.dot(-S[0, :, :], tx) + vc0
        if typ[0] == 3:
            v0 = tx
        if typ[0] == 1:
            v0 = pa[:, 0]

        y[0:2] = v0
        for i in range(len(typ[1:])):
            if typ[i + 1] == 2:
                y[2 * (i + 1):2 * (i + 1) + 2] = np.array([c[i + 1], d[i + 1]])
            if typ[i + 1] == 3:
                #y[2 * (i + 1):2 * (i + 1) + 2] = y[2*i:2*i+2]
                y[2 * (i + 1):2 * (i + 1) + 2] = np.array([0,0]) 
            if typ[i + 1] == 1:
                y[2 * (i + 1):2 * (i + 1) + 2] = pa[:, i + 1]

        x = la.solve(A, y)
        M = np.vstack((x[0::2], x[1::2]))

        return M

    def backtrace(self, tx, rx, M):
        """ backtrace given image, tx, and rx

        Parameters
        ----------

        tx :  ndarray (2x1)
              transmitter
        rx :  ndarray (2x1)
              receiver
        M  :  ndarray (2xN)
              N image points obtained using self.image method

        Returns
        -------

        isvalid : bool
            True if the backtrace ends successfully

        Y : ndarray (2 x (N+2))
            sequence of points corresponding to the seek ray

        Examples
        --------

        .. plot::
            :include-source:

            >>> import matplotlib.pyplot as plt
            >>> import numpy as np
            >>> from pylayers.gis.layout import *
            >>> from pylayers.antprop.signature import *
            >>> L = Layout()
            >>> L.dumpr()
            >>> seq = np.array([[1,5,1],[1,1,1]])
            >>> s = Signature(seq)
            >>> tx = np.array([4,-1])
            >>> rx = np.array([1,1])
            >>> s.ev(L)
            >>> M = s.image(tx)
            >>> isvalid,Y = s.backtrace(tx,rx,M)
            >>> fig = plt.figure()
            >>> ax = fig.add_subplot(111)
            >>> l1 = ax.plot(tx[0],tx[1],'or')
            >>> l2 = ax.plot(rx[0],rx[1],'og')
            >>> l3 = ax.plot(M[0,:],M[1,:],'ob')
            >>> l4 = ax.plot(Y[0,:],Y[1,:],'xk')
            >>> ray = np.hstack((np.hstack((tx.reshape(2,1),Y)),rx.reshape(2,1)))
            >>> l5 = ax.plot(ray[0,:],ray[1,:],color='#999999',alpha=0.6,linewidth=0.6)
            >>> fig,ax = L.showG('s',fig=fig,ax=ax)
            >>> plt.show()

        Notes
        -----

        For mathematical details see :

        @INPROCEEDINGS{6546704,
        author={Laaraiedh, Mohamed and Amiot, Nicolas and Uguen, Bernard},
        booktitle={Antennas and Propagation (EuCAP), 2013 7th European Conference on},
        title={Efficient ray tracing tool for UWB propagation and
               localization modeling},
        year={2013},
        pages={2307-2311},}

        """
        #import ipdb
        #pdb.set_trace()
        #import pdb
        pa = self.pa
        pb = self.pb
        typ = self.typ

        N = np.shape(pa)[1]
        I2 = np.eye(2)
        z0 = np.zeros((2, 1))

        pkm1 = rx.reshape(2, 1)
        Y = pkm1
        k = 0          # interaction counter
        beta = .5      # to enter into the loop
        isvalid = True # signature is asumed being valid by default
        epsilon = 1e-2

        # while (((beta <= 1) & (beta >= 0)) & (k < N)):
        while (((beta <= 1-epsilon) & (beta >= epsilon)) & (k < N)):
            #if int(typ[k]) != 1: # not a diffraction (surprisingly it works)
            if int(typ[N-(k+1)]) != 1: # not a diffraction
                # Formula (25) of paper Eucap 2013
                l0 = np.hstack((I2, pkm1 - M[:, N - (k + 1)].reshape(2, 1), z0))
                l1 = np.hstack((I2, z0,
                                pa[:, N - (k + 1)].reshape(2, 1) -
                                pb[:, N - (k + 1)].reshape(2, 1)
                                ))
                # print pkm1 
                # import ipdb
                # ipdb.set_trace()
                T = np.vstack((l0, l1))
                yk = np.hstack((pkm1[:, 0].T, pa[:, N - (k + 1)].T))

                deT = np.linalg.det(T)

                if abs(deT) < 1e-15:
                    return(False,(k,None,None))
                xk = la.solve(T, yk)
                pkm1 = xk[0:2].reshape(2, 1)
                gk = xk[2::]
                alpha = gk[0]
                beta = gk[1]
                Y = np.hstack((Y, pkm1))
            else:
                alpha = 0.5 # dummy necessary for the test below
                # fixing #210
                #Y = np.hstack((Y, pa[:, k].reshape((2, 1))))
                #pkm1 = pa[:, k].reshape((2, 1))
                Y = np.hstack((Y, pa[:, N-(k+1)].reshape((2, 1))))
                pkm1 = pa[:, N-(k+1)].reshape((2, 1))
            k = k + 1
        if ((k == N) & ((beta > 0) & (beta < 1)) & ((alpha > 0) & (alpha < 1))):
            Y = np.hstack((Y, tx.reshape(2, 1)))
            return isvalid,Y
        else:
            isvalid = False
            return isvalid,(k,alpha,beta)


    def sig2beam(self, L, p, mode='incremental'):
        """ signature to beam

        Parameters
        ----------

        L : Layout
        p : point
        mode : string

        """
        try:
            L.Gr
        except:
            L.build()

        # ev transforms a sequence of segment into numpy arrays (points)
        # necessary for image calculation
        self.ev(L)
        # calculates images from pTx
        M = self.image(p)

    def sig2ray(self, L, pTx, pRx, mode='incremental'):
        """ convert a signature to a 2D ray

        Parameters
        ----------

        L : Layout
        pTx : ndarray
            2D transmitter position
        pRx : ndarray
            2D receiver position
        mod : if mod=='incremental' a set of alternative signatures is return

        Returns
        -------

        Y : ndarray (2x(N+2))

        See Also
        --------

        Signature.image
        Signature.backtrace

        """
        #try:
        #    L.Gr
        #except:
        #    L.build()

        # ev transforms a sequence of segment into numpy arrays (points)
        # necessary for image calculation
        self.ev(L)
        # calculates images from pTx
        M = self.image(pTx)
        #print self
        #if np.array_equal(self.seq,np.array([5,7,4])):
        #    pdb.set_trace()
        isvalid,Y = self.backtrace(pTx, pRx, M)
        #print isvalid,Y
        #
        # If incremental mode this function returns an alternative signature
        # in case the signature do not yield a valid ray.
        #
        isray = True
        if mode=='incremental':
            if isvalid:
                return isray,Y
            else:
                isray=False
                # something to do here
                return isray,None
        else:
            if isvalid:
                return isray,Y
            else:
                isray=False
                return isray,None

# def get_sigslist(self, tx, rx):
#        """
#        get signatures (in one list of arrays) between tx and rx
#        Parameters
#        ----------
#            tx : numpy.ndarray
#            rx : numpy.ndarray
#        Returns
#        -------
#            sigslist = numpy.ndarray
#        """
#        try:
#            self.L.Gi
#        except:
#            self.L.build()
#        # all the vnodes >0  from the room
#        #
#        NroomTx = self.L.pt2ro(tx)
#        NroomRx = self.L.pt2ro(rx)
#        print NroomTx,NroomRx
#
#        if not self.L.Gr.has_node(NroomTx) or not self.L.Gr.has_node(NroomRx):
#            raise AttributeError('Tx or Rx is not in Gr')
#
#        #list of interaction 
#        ndt = self.L.Gt.node[self.L.Gr.node[NroomTx]['cycle']]['inter']
#        ndr = self.L.Gt.node[self.L.Gr.node[NroomRx]['cycle']]['inter']
#
#        ndt1 = filter(lambda l: len(eval(l))>2,ndt)
#        ndt2 = filter(lambda l: len(eval(l))<3,ndt)
#        ndr1 = filter(lambda l: len(eval(l))>2,ndr)
#        ndr2 = filter(lambda l: len(eval(l))<3,ndr)
#
#        print ndt1
#        print ndr1
#        ndt1 = filter(lambda l: eval(l)[2]<>NroomTx,ndt1)
#        ndr1 = filter(lambda l: eval(l)[1]<>NroomRx,ndr1)
#
#        ndt = ndt1 + ndt2
#        ndr = ndr1 + ndr2
#
#        ntr = np.intersect1d(ndt, ndr)
#        sigslist = []
#
#        for nt in ndt:
#            print nt
#            for nr in ndr:
#                addpath = False
#                print nr
#                if (nt != nr):
#                    try:
#                        path = nx.dijkstra_path(self.L.Gi, nt, nr)
#                        #paths = nx.all_simple_paths(self.L.Gi,source=nt,target=nr)
#                        addpath = True
#                        showsig(self.L,path,tx,rx)
#                    except:
#                        pass
#                if addpath:
#                    sigarr = np.array([]).reshape(2, 0)
#                    for interaction in path:
#                        it = eval(interaction)
#                        if type(it) == tuple:
#                            if len(it)==2: #reflexion
#                                sigarr = np.hstack((sigarr,
#                                                np.array([[it[0]],[1]])))
#                            if len(it)==3: #transmission
#                                sigarr = np.hstack((sigarr,
#                                                np.array([[it[0]], [2]])))
#                        elif it < 0: #diffraction
#                            sigarr = np.hstack((sigarr,
#                                                np.array([[it], [3]])))
#                    sigslist.append(sigarr)
#
#        return sigslist
#
#    def update_sigslist(self):
#        """
#        get signatures taking into account reverberations
#
#        Returns
#        -------
#            sigslist: numpy.ndarry
#
#        Notes
#        -----
#        This is a preliminary function need more investigations
#
#        """
#        pTx = self.pTx
#        pRx = self.pRx
#        NroomTx = self.L.pt2ro(pTx)
#        NroomRx = self.L.pt2ro(pRx)
#        if NroomTx == NroomRx:
#            sigslist = self.get_sigslist(pTx, pRx)
#        else:
#            sigslist = []
#            sigtx = self.get_sigslist(pTx, pTx)
#            sigrx = self.get_sigslist(pRx, pRx)
#            sigtxrx = self.get_sigslist(pTx, pRx)
#            sigslist = sigslist + sigtxrx
#            for sigtr in sigtxrx:
#                for sigt in sigtx:
#                    if (sigt[:, -1] == sigtr[:, 0]).all():
#                        if np.shape(sigtr)[1] == 1 or np.shape(sigt)[1] == 1:
#                            pass
#                        else:
#                            sigslist.append(np.hstack((sigt, sigtr[:, 1:])))
#                for sigr in sigrx:
#                    if (sigr[:, 0] == sigtr[:, -1]).all():
#                        if np.shape(sigtr)[1] == 1 or np.shape(sigr)[1] == 1:
#                            pass
#                        else:
#                            sigslist.append(np.hstack((sigtr, sigr[:, 1:])))
#
#        return sigslist
#
#    def image_ceilfloor(self, tx, pa, pb):
#        """
#        Compute the images of tx with respect to ceil or floor
#        Parameters
#        ----------
#            tx : numpy.ndarray
#            pa : numpy.ndarray
#            pb : numpy.ndarray
#        Returns
#        -------
#            M : numpy.ndarray
#        """
#
#        pab = pb - pa
#        alpha = np.sum(pab * pab, axis=0)
#        zalpha = np.where(alpha == 0.)
#        alpha[zalpha] = 1.
#
#        a = 1 - (2. / alpha) * (pa[1, :] - pb[1, :]) ** 2
#        b = (2. / alpha) * (pb[0, :] - pa[0, :]) * (pa[1, :] - pb[1, :])
#        c = (2. / alpha) * (pa[0, :] * (pa[1, :] - pb[1, :]) ** 2 +
#                            pa[1, :] * (pa[1, :] - pb[1, :]) *
#                            (pb[0, :] - pa[0, :]))
#        d = (2. / alpha) * (pa[1, :] * (pb[0, :] - pa[0, :]) ** 2 +
#                            pa[0, :] * (pa[1, :] - pb[1, :]) *
#                            (pb[0, :] - pa[0, :]))
#
#        S = np.zeros((1, 2, 2))
#        S[:, 0, 0] = -a
#        S[:, 0, 1] = b
#        S[:, 1, 0] = b
#        S[:, 1, 1] = a
#        A = np.eye(2)
#
#        vc0 = np.array([c[0], d[0]])
#        y = np.dot(-S[0, :, :], tx) + vc0
#
#        x = la.solve(A, y)
#        M = np.vstack((x[0::2], x[1::2]))
#        return M
#
#    def backtrace_ceilfloor(self, tx, rx, pa, pb, M):
#        """
#        backtracing step: given the image, tx, and rx, this function
#        traces the 2D ray.
#
#        Parameters
#        ----------
#            tx :  numpy.ndarray
#                  transmitter
#            rx :  numpy.ndarray
#                  receiver
#            M  :  numpy.ndarray
#                  images obtained using image()
#
#        Returns
#        -------
#            Y : numpy.ndarray
#                2D ray
#
#
#        """
#        N = np.shape(pa)[1]
#        I2 = np.eye(2)
#        z0 = np.zeros((2, 1))
#
#        pkm1 = rx.reshape(2, 1)
#        Y = pkm1
#        k = 0
#        beta = .5
#        cpt = 0
#        while (((beta <= 1) & (beta >= 0)) & (k < N)):
#            l0 = np.hstack((I2, pkm1 - M[:, N - (k + 1)].reshape(2, 1), z0
#                            ))
#            l1 = np.hstack((I2, z0,
#                            pa[:, N - (k + 1)].reshape(2, 1) -
#                            pb[:, N - (k + 1)].reshape(2, 1)
#                            ))
#
#            T = np.vstack((l0, l1))
#            yk = np.hstack((pkm1[:, 0].T, pa[:, N - (k + 1)].T))
#            deT = np.linalg.det(T)
#            if abs(deT) < 1e-15:
#                return(None)
#            xk = la.solve(T, yk)
#            pkm1 = xk[0:2].reshape(2, 1)
#            gk = xk[2::]
#            alpha = gk[0]
#            beta = gk[1]
#            Y = np.hstack((Y, pkm1))
#            k += 1
#        if ((k == N) & ((beta > 0) & (beta < 1))):  # & ((alpha > 0) & (alpha < 1))):
#            Y = np.hstack((Y, tx.reshape(2, 1)))
#            return(Y)
#        else:
#            return(None)
#   def sigs2rays(self, sigslist):
#        """ from signatures list to 2D rays
#
#        Parameters
#        ----------
#
#            sigslist : list
#
#        Returns
#        -------
#
#            rays : dict
#
#        """
#        rays = {}
#        for sig in sigslist:
#            s = Signature(sig)
#            Yi = s.sig2ray(self.L, self.pTx[:2], self.pRx[:2])
#            if Yi is not None:
#                #pdb.set_trace()
#                Yi = np.fliplr(Yi)
#                nint = len(sig[0, :])
#                if str(nint) in rays.keys():
#                    Yi3d = np.vstack((Yi[:, 1:-1], np.zeros((1, nint))))
#                    Yi3d = Yi3d.reshape(3, nint, 1)
#                    rays[str(nint)]['pt'] = np.dstack((
#                                                      rays[str(nint)]['pt'], Yi3d))
#                    rays[str(nint)]['sig'] = np.dstack((
#                                                       rays[str(nint)]['sig'],
#                                                       sig.reshape(2, nint, 1)))
#                else:
#                    rays[str(nint)] = {'pt': np.zeros((3, nint, 1)),
#                                       'sig': np.zeros((2, nint, 1))}
#                    rays[str(nint)]['pt'][0:2, :, 0] = Yi[:, 1:-1]
#                    rays[str(nint)]['sig'][:, :, 0] = sig
#        return rays


if __name__ == "__main__":
    plt.ion()
    print "testing pylayers/antprop/signature.py"
    doctest.testmod()
    print "-------------------------------------"
