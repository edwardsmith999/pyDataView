## NAME: read_file
## 
## SYNOPSIS:
## Read the file specified by the name passed into function
##

namespace eval ::read_file:: {
	namespace export read_file_in
}

proc ::read_file::read_file_in {name req_line} {

set i 0
set f [open $name r]
while {[gets $f line] >= 0} {
    #puts [string length $line]
	set i [expr $i+1]
	set out($i) $line
	#puts $out($i)
}
close $f
return $out($req_line)
}
