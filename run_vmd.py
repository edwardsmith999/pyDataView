import sys
import argparse
import os

import sys
sys.path.insert(0, "../../pyDataView/")
import postproclib as ppl
from misclib import Chdir

class MockHeader(object):

    def __init__(self):
        self.vmd_skip = 0
        self.vmd_start = 0
        self.vmd_end = 0
        self.Nsteps = 0
        self.tplot = 0
        self.delta_t = 0
        self.initialstep = 0

class MockRaw(object):

    def __init__(self, fdir):
        self.fdir = fdir
        try:
            self.header = ppl.MDHeaderData(fdir)
        except IOError:
            self.header = MockHeader()      

class dummyField(ppl.Field):

    """
        Dummy field object
    """

    dtype = 'd'
    nperbin = 1
    fname = ''
    plotfreq = 1

    def __init__(self, fdir):
        self.Raw = MockRaw(fdir)


def prepare_vmd_files(args):

    """
        Copy tcl files for postprocessing
        and reformat vmd temp files 
    """

    fobj = dummyField(args['fdir'])
    vmdobj = ppl.VMDFields(fobj, args['fdir'])
    vmdobj.copy_tclfiles() #Create VMD vol_data folder and copy vmd driver scripts
    vmdobj.reformat()  
    

def run_vmd(parent_parser=argparse.ArgumentParser(add_help=False)):

    def print_fieldlist():
        outstr = 'Type of field to overlay with vmd \n'
        try:
            ppObj = ppl.All_PostProc('../src/results/')
            outstr = outstr + str(ppObj)
        except:
            print(' \n')
            pass

        outstr = outstr + '\n N.B. Make sure to include quotes if there is a space in field name \n'
        return outstr

    #Keyword arguments
    parser = argparse.ArgumentParser(description='run_vmd vs. master jay -- Runs VMD with overlayed field',
                                     parents=[parent_parser])

    try:
        argns, unknown = parser.parse_known_args()
        print('Using directory defined as ', argns.fdir)
    except AttributeError:
        parser.add_argument('-d','--fdir',dest='fdir', nargs='?', 
                            help='Directory with vmd file and field files',     
                            default=None)

    parser.add_argument('-f', '--field', dest='field', 
                        help=print_fieldlist(), default=None)
    parser.add_argument('-c', '--comp', dest='comp', 
                        help='Component name', default=None)
    parser.add_argument('-l', '--clims', dest='clims', 
                        help='Colour limits', default=None)
    parser.add_argument('-p', '--poly',help='Polymer flag',
                        action='store_const', const=True)
    parser.add_argument('-m', '--mie',help='Mie types flag',
                        action='store_const', const=True)
    args = vars(parser.parse_args())

    #Static arguments
    if args['fdir'] == None:
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        args['fdir'] = scriptdir + '/../src/results/'
    if args['field'] == None:
        print("No field type specified -- using default value of no field")
        args['field'] = None
        component = 0
    if(len(sys.argv) < 2 or sys.argv[1] in ['--help', '-help', '-h']):
        ppObj = ppl.All_PostProc(args['fdir'])
        print("Available field types include")
        print(ppObj)
        sys.exit()
    if args['comp'] == None:
        print("No components direction specified, setting default = 0")
        args['comp'] = 0

    print(args['clims'], type(args['clims']))
    if args['clims'] == None:
        print("No colour limits specified -- using defaults min/max")
        clims = None
    else:
        clims = [float(i) for i in args['clims'].replace("[","").replace("]","").split(",")]
    #Polymer case, no field at the moment
    if args['poly']:
        if args['field'] != None:
            print("Can't overlay field and polymers")
        prepare_vmd_files(args)

        #Open vmd 
        with Chdir(args['fdir']):
            #Build vmd polymer file 
            ppl.build_psf()
            ppl.concat_files()

            #Call polymer script
            command = "vmd -e ./vmd/load_polymer.vmd"
            os.system(command)
            sys.exit()

    if args['mie']:
        if args['field'] != None:
            print("Can't overlay field and mie molecules")
        prepare_vmd_files(args)

        with Chdir(args['fdir']):

            #Call mie script
            command = "vmd -e ./vmd/load_miepsf.vmd"
            os.system(command)
            sys.exit()

    #Plane field case
    if args['field'] == None:
        prepare_vmd_files(args)

        #Open vmd 
        with Chdir(args['fdir']):
            command = "vmd " + "./vmd_out.dcd"
            os.system(command)

    #Overlayed field case
    else:
        try:
            ppObj = ppl.All_PostProc(args['fdir'])
            fobj = ppObj.plotlist[args['field']]
        except KeyError:
            print("Field not recognised -- available field types include:")
            print(ppObj)
            sys.exit()
        except:
            raise

        vmdobj = ppl.VMDFields(fobj, args['fdir'])
        vmdobj.copy_tclfiles() #Create VMD vol_data folder and copy vmd driver scripts
        vmdobj.reformat()
        vmdobj.write_vmd_header()
        vmdobj.write_vmd_intervals()
        vmdobj.write_dx_range(component=args['comp'], clims=clims)
        vmdobj.writecolormap('RdYlBu')

        #Open vmd 
        with Chdir(args['fdir'] + './vmd/'):
            command = "vmd -e " + "./plot_MD_field.vmd"
            os.system(command)

if __name__ == "__main__":
    run_vmd()
