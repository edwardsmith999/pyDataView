## NAME: tricolor_scale
## 
## SYNOPSIS:
## Specify a customer colour schemes for the
## tricolor_scale used to define gradients
##

# load read file routine
source ./read_file.tcl
namespace import ::read_file::*


namespace eval ::custom_colorscale:: {
	namespace export tricolor_scale cmapfile_color_scale
}

#Define custom colour scales
proc lerpcolor { col1 col2 alpha } {
  set dc [vecsub $col2 $col1]
  set nc [vecadd $col1 [vecscale $dc $alpha]]
  return $nc  
}

proc coltogs { col } {
  foreach {r g b} $col {}
  set gray [expr ($r + $g + $b) / 3.0]
  return [list $gray $gray $gray]
}

proc ::custom_colorscale::tricolor_scale {} {
  display update off
  set mincolorid [expr [colorinfo num] - 1]
  set maxcolorid [expr [colorinfo max] - 1]
  set colrange [expr $maxcolorid - $mincolorid]
  set colhalf [expr $colrange / 2]
  for {set i $mincolorid} {$i < $maxcolorid} {incr i} {
    set colpcnt [expr ($i - $mincolorid) / double($colrange)]

    set R {1.921568661928176880e-01 2.117647081613540649e-01 5.843137502670288086e-01 }
    set W {9.737793234621987537e-01 9.898500606950446645e-01 7.972318345012722185e-01 }
    set B {7.239523413363717630e-01 7.381776274281801054e-02 1.505574837974381908e-01 }
    if { $colpcnt < 0.5 } {
      set nc [lerpcolor $R $W [expr $colpcnt * 2.0]]
    } else {
      set nc [lerpcolor $W $B [expr ($colpcnt-0.5) * 2.0]]
    }

    foreach {r g b} $nc {}
    puts "index: $i $r $g $b   -- $colpcnt"
    display update ui
    color change rgb $i $r $g $b 
  }
  display update on
}


proc ::custom_colorscale::cmapfile_color_scale {name} {
  display update off
  set mincolorid [expr [colorinfo num] - 1]
  set maxcolorid [expr [colorinfo max] - 1]
  set colrange [expr $maxcolorid - $mincolorid]
  set count 1024
  for {set i [expr $mincolorid]} {$i < [expr $maxcolorid]} {incr i} {
    set colpcnt [expr ($i - $mincolorid) / double($colrange)]
    set nc [read_file_in $name $count]
    foreach {r g b} $nc {}
    #puts "index: $count $i $r $g $b   -- $colpcnt"
    display update ui
    color change rgb $i $r $g $b 
    #Go through in reverse order (seems to prevents wrap around of colour)
    set count [expr $count-1]
  }
  display update on
}
