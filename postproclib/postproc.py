class PostProc:

    def __str__(self):
        string =  ('\nAvailable outputs in ' + self.resultsdir + ' include:\n\n')
        string += ('\t{0:^24s}\t{1:>10s}\n'.format('field', 'records'))
        #string += ('\t{0:^24s}\t{1:^10s}\n'.format('-'*24, '-'*10))
        for key,field in sorted(self.plotlist.items()):
            line = '\t{0:<24s}=\t{1:>10d},\n'.format(key, field.maxrec)
            string += line
        return string 
