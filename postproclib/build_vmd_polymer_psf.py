#! usr/bin/env python
import os
import glob
import sys
import numpy as np
import subprocess as sp
from operator import itemgetter

def progress_bar(fraction):
    i = int(fraction*65)
    sys.stdout.write('\r')
    sys.stdout.write("[%-65s] %6.3f%%" % ('='*i, 100*fraction))
    sys.stdout.flush()

def write_bonds(pairs_list):
    nbonds = len(pairs_list)
    f = open('polymer_topol.bonds','w')
    f.write("\n{0:8d}".format(nbonds) + ' !NBOND: bonds\n')
    line = ''
    count = 0 
    for pair in pairs_list:
        count += 1
        line += "{0:>8d}{1:>8d}".format(pair[0],pair[1])
        if (count%4 == 0):
            f.write(line+'\n')
            line = ''; 
    # If necessary write final line
    if (count%4 != 0):
        f.write(line+'\n')
    f.close()

def concat_files():
    sp.call('cat polymer_topol.header polymer_topol.bonds > polymer_topol.psf',
                shell=True)


def read_monomers(fdir="./", filename='monomers'):

    # Concat list of all monomers, from all ranks,
    # store everything in RAM if poss
    data = []
    rankfiles = glob.glob(fdir + filename + '_*')
    for rankfile in rankfiles:
        print('Getting info from file ' + str(rankfile) + ' of ' + 
              str(len(rankfiles)))
        with open(rankfile,'r') as f:
            data = data + [list(map(int,line.split())) for line in f]

    # Sort the data into chains (second column is chainID)
    print('Sorting monomers into chains...')
    data.sort(key=itemgetter(1))
    data = np.array(data)

    return data

def build_psf():

    data = read_monomers()

    if data.size == 0:
        return

    # Loop over chainIDs and determine bond pairs
    chainID = data[0,1]
    maxchainID = data[-1,1]
    pairs = [] # List of bond pairs
    count = 0

    if maxchainID == 0:
        print('No polymers in fluid -- exiting')
        return 

    print('Finding bond pairs in all chains...')
    while True:

        # chain is a list of all monomers with the same chainID
        chain = data[np.where(data[:,1]==chainID)]
        # keep track of where we are in the data
        lastindex = np.where(data[:,1]==chainID)[0][-1]
        print(chainID, np.array(chain)[:,0], lastindex)
        if (chainID%100 == 0):
            progress_bar(float(chainID)/float(maxchainID))

        if (chainID != 0):

            for monomer in chain:
                globID = monomer[0]
                scID = monomer[2]
                bflag = monomer[-4:]
                bstring = "{3:031b}{2:031b}{1:031b}{0:031b}".format(
                          bflag[0],bflag[1],bflag[2],bflag[3])[::-1]
                barray = np.array(list(map(int,list(bstring))))
                bscIDs = np.where(barray==1)[0] + 1
                try:
                    bglobIDs = ([chain[np.where(chain[:,2]==b)][0][0] 
                                 for b in bscIDs])
                    for ID in bglobIDs:
                        pairs.append(sorted([globID,ID]))
                except:
                    print('Failed to find all subchainIDs ' + str(bscIDs) + 
                          ' for chain ID ' + str(chainID))
                    #raise

        try:
            chainID = data[lastindex+1][1]
        except IndexError:
            break

    # Remove duplicate entries by converting to a set and then back to a list
    pairs_set = set(tuple(p) for p in pairs)   
    pairs_list = list(map(list,pairs_set))

    # Write the list to polymer_topol.bonds
    write_bonds(pairs_list)

if __name__ == "__main__":
    build_psf()
    # Ask user if they want to concat
    print('Do you wish to concatenate polymer_topol.header and \n'+
          'polymer_topol.bonds to make polymer_topol.psf? (y/n)') 
    ans = input()
    if (ans in ['y','Y','yes','Yes','YES']):
        concat_files()
