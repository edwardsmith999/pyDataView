
def minimalscript(scripttype, plottype, fdir, ppdir, fieldname, 
                  startrec, endrec, comp, norm, bins, binwidth):

    if scripttype.lower() == "python":

        script=r"""
import matplotlib.pyplot as plt
import numpy as np
import sys

ppdir = '{0}'
sys.path.append(ppdir)
import postproclib as ppl

normal ={6}
component={3}
startrec={4}
endrec={5}

#Get Post Proc Object
fdir = '{1}'
PPObj = ppl.All_PostProc(fdir)
print(PPObj)

#Get plotting object
plotObj = PPObj.plotlist['{2}']
""".format(ppdir, fdir, fieldname, str(comp), str(startrec), str(endrec), str(norm))

        if plottype == "Profile":
            script += r"""
#Get profile
x, y = plotObj.profile(axis=normal, 
       startrec=startrec, 
       endrec=endrec)

#Plot only normal component
fig, ax = plt.subplots(1,1)
ax.plot(x,y[:,component])
plt.show()
"""

        elif plottype == "Contour":
            script += r"""
#Get Contour
naxes = [0,1,2]
naxes.remove(normal)
bins = {0}
binwidth = {1}
binlimits = [None]*3
binlimits[normal] = (bins-binwidth, 
                 bins+binwidth+1) #Python +1 slicing

ax1, ax2, data = plotObj.contour(axes=naxes, 
                             startrec=startrec,
                             endrec=endrec,
                             binlimits=binlimits,
                             missingrec='returnzeros')

fig, ax = plt.subplots(1,1)
cmap = plt.cm.RdYlBu_r
colormesh = ax.pcolormesh(ax1, ax2, data[:,:,component], 
                                cmap=cmap)
plt.colorbar(colormesh)
plt.axis('tight')
plt.show()
""".format(str(bins), str(binwidth))

    elif scripttype.lower() == "matlab":
        
        script=r"""
clear variables classes
close all

ppdir = '{0}'
cd(ppdir)
ppmod = py.importlib.import_module("postproclib");

normal ={6}
component={3}
startrec={4}
endrec={5}
naxis = 0:2;
naxis(normal+1) = []; 

%Get Post Proc Object
fdir = '{1}'
PPObj = ppmod.All_PostProc(py.str(fdir));

%Get plotting object
fname = '{2}'
PObj = PPObj.plotlist{{py.str(fname)}};

""".format(ppdir, fdir, fieldname, str(comp), str(startrec), str(endrec), str(norm))

        if plottype == "Profile":
            script += r"""
%Get profile
a = PObj.profile(py.int(normal), py.int(startrec),py.int(endrec));
x = a{1}; y = a{2};
plot(x,y)

"""

        elif plottype == "Contour":
            script += r"""
bins = {0}
binwidth = {1}
bns = py.list({{py.int(bins-binwidth), py.int(bins+binwidth+1)}});
None = string(missing);
if (normal == 0)
    binlimits = py.list({{bns,None,None}});
elseif (normal == 1)
    binlimits = py.list({{None,bns,None}});
elseif (normal == 2)
    binlimits = py.list({{None,None,bns}});
end

a = PObj.contour(py.list({{py.int(naxis(1)),py.int(naxis(2))}}), ...
                py.int(startrec),py.int(endrec), ...
                pyargs('binlimits',binlimits, ...
                "missingrec","returnzeros"));
            
ax1 = np2mat(a{{1}});
ax2 = np2mat(a{{2}});
field = np2mat(a{{3}});

[C,h] =contourf(ax1, ax2, field(:,:,component+1), 40);
set(h,'LineColor','none');
colorbar()
""".format(str(bins), str(binwidth))

        script += r"""
function data = np2mat(nparray)
    ns = int32(py.array.array('i',nparray.shape));
    data = reshape(double(py.array.array('d', ...
            py.numpy.nditer(nparray, pyargs('order', 'C')))), ns);
    data=reshape(data,fliplr(ns));
    data=permute(data,[length(ns):-1:1]);
end
"""
    else:
        raise ValueError("scripttype should be python or matlab") 

    return script 