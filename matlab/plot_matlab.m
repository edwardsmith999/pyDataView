clear variables classes
close all
cd("../")
ppmod = py.importlib.import_module('postproclib');
%py.importlib.reload(ppmod);

%MATLAB indexing 1=x, 2=y, 3=z
normal = 3;
naxis = 0:2;
naxis(normal) = []; 
component = 1;

startrec = 300;
endrec = 300;

%Some issues with windows backslashes, also make sure ends with a forward slash
%fdir='\\wsl$\Ubuntu-18.04\home\es205\\codes\flowmol_et_al\flowmol\runs\results'
%fdir = py.os.path.normpath("C:\Users\Ed\Documents\code\pyDataView-python3\pyDataView-python3\results/");
fdir = './results/';
fname = "rho";

%Create Postproc object and one for required datatype
PPObj = ppmod.All_PostProc(py.str(fdir));
PObj = PPObj.plotlist{py.str(fname)};

%General low level read code
ndarray = PObj.read(py.int(startrec), py.int(endrec));
data = np2mat(ndarray);

%Plot as an image
figure()
imagesc(data(:,:,1,1,component)')
colorbar()

%Setup Meshgrid for contour plot
g = PObj.grid;
x = double(g{1});
y = double(g{2});
z = double(g{3});
[X,Y,Z] = meshgrid(x,y,z);

%Plot contour against grid
figure()
contourf(X(:,:,1), Y(:,:,1), data(:,:,1,1,component)')
colorbar()
  
%Get Profile
a = PObj.profile(py.int(normal-1), py.int(startrec),py.int(endrec));
x = a{1};
y = a{2};
plot(x,y)

%Get contour
a = PObj.contour(py.list({py.int(naxis(1)),py.int(naxis(2))}), ...
                    py.int(startrec),py.int(endrec));
                
ax1 = np2mat(a{1});
ax2 = np2mat(a{2});
field = np2mat(a{3});

figure()
[C,h] =contourf(ax1, ax2, field, 40);
set(h,'LineColor','none');
colorbar()

figure()
surf(ax1, ax2, field)
colorbar()

% Solution from
% mathworks.com/matlabcentral/answers/157347-convert-python-numpy-array-to-double      
function data = np2mat(nparray)
    ns = int32(py.array.array('i',nparray.shape));
    %data = reshape(double(py.array.array('d', ...
    %                py.numpy.nditer(nparray))), ns);
    data = reshape(double(py.array.array('d', ...
                py.numpy.nditer(nparray, pyargs('order', 'C')))), ns);
    data=reshape(data,fliplr(ns));
    data=permute(data,[length(ns):-1:1]);
end
