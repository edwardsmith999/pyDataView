## NAME: color_scale_bar
## 
## SYNOPSIS:
##   color_scale_bar draws a color bar on the screen to show all of the
##   current colors (colorid 17~1040). It also shows labels beside the 
##   color bar to show the range of the mapped values.
##
## VERSION: 2.0
##    Uses VMD version:  VMD Version 1.7 or greater
##    Ease of use: 2. need to understand some Tcl and a bit about how VMD
##                 works
## 
## PROCEDURES:
##      color_scale bar
## 
## DESCRIPTION:
##      To draw a color scale bar with length=1.5, width=0.25, the range of
##      mapped values is 0~128, and you want 8 labels.
##      color_scale_bar 1.5  0.25  0  128 8
## 
## COMMENTS: The size of the bar also depends on the zoom scale.
## 
## AUTHOR:
##      Wuwei Liang (gtg088c@prism.gatech.edu)
## 
##      New version 2 built on Wuwei Liang's code, by Dan Wright 
##                  <dtwright@uiuc.edu>
##
##      Last update v2.1 on Dan Wright's version 2 on Wuwei Liang's code
##                  by Pepe Romo  <jmanuel@ipicyt.edu.mx>
## 
## CHANGES:
##      * draws the bar in a new molecule
##      * has defaults for all parameters so nothing has to be entered manually
##      * functions moved into a seperate namespace
##      * has a delete function (just deletes the seperate mol for now)
##      * fixed position so it remains visible when the scene is rotated
##
## CHANGES 2:
##      * Searches the Min and Max through all the FRAMES in each Mol
##
## USAGE:
## Run the following in the console window:
## 
## 1) 'source color_scale_bar_new.tcl'
## 2) 'namespace import ::ColorBar::*'
## 3) run 'color_scale_bar' to create the bar with default parameters;
##    run 'delete_color_scale_bar' to remove it from the display


# This function draws a color bar to show the color scale
# length = the length of the color bar
# width = the width of the color bar
# min = the minimum value to be mapped
# max = the maximum mapped value
# label_num = the number of labels to be displayed

namespace eval ::ColorBar_v2:: {
	variable bar_mol
	namespace export color_scale_bar_v2 delete_color_scale_bar_v2
}

proc ::ColorBar_v2::color_scale_bar_v2 {{length 0.5} {width 0.05} {auto_scale 1} {fixed 1} {min 0} {max 100} {label_num 5} } {

	variable bar_mol
	
	display update off
	#display resetview

	# Create a seperate molid to draw in, so it's possible for the user to 
	# delete the bar.
	#
	# So that the draw cmds will work right, must save top mol and set top
	# to our new created mol, then set it back later.
	set numframes [molinfo top get numframes]
	set old_top [molinfo top]
	set bar_mol [mol new]
	mol top $bar_mol

	# If a fixed bar was requested...
	if {$fixed == 1} {
		mol fix $bar_mol
	}

	# If auto_scale was requested, go through all the mols and find the min/max
	# scale ranges for setting the bar.
	if {$auto_scale == 1} {
		set min 999
		set max -99
		foreach m [molinfo list] {
			if {$m != $bar_mol} {
			    for {set i 0} {$i<$numframes} {incr i 1} {
				molinfo $m set frame $i
				set minmax [split [mol scaleminmax $m 0]]
				set aux [molinfo $m get frame]
                                #puts "mol $m frame $aux  minmax $minmax i $i"
				if {$min > [lindex $minmax 0]} {
					set min [lindex $minmax 0]
				}
				if {$max < [lindex $minmax 1]} {
					set max [lindex $minmax 1]
				}
			    }
			}
		}
	}
	#puts "Final MinMax --> $min $max"


	# We want to draw relative to the location of the top mol so that the bar 
	# will always show up nicely.
	set center [molinfo $old_top get center]
	set center [regsub -all {[{}]} $center ""]
	set center [split $center]

	#puts "[lindex $center 0]"
	
	# draw the color bar
	set start_y [expr [lindex $center 1] - (0.5 * $length)]
	#set start_y [expr (-0.5 * $length)-1.2]
	set use_x [expr 1+[lindex $center 0]-0.25]
	#set use_x -1.0
	set use_z [lindex $center 2]
	#set use_z 0
	set step [expr $length / 1024.0]

	#puts "x: $use_x y: $start_y z: $use_z"

	for {set colorid 17 } { $colorid <= 1040 } {incr colorid 1 } {
		draw color $colorid
		set cur_y [ expr $start_y + ($colorid - 17) * $step ]
		draw line "$use_x $cur_y $use_z"  "[expr $use_x+$width] $cur_y $use_z"
	}

	# draw the labels
	set coord_x [expr (1.2*$width)+$use_x];
	set step_size [expr $length / $label_num]
	set color_step [expr 1024.0/$label_num]
	set value_step [expr ($max - $min ) / double ($label_num)]
	
	for {set i 0} {$i <= $label_num } { incr i 1} {
		set cur_color_id black   
		#  set cur_color_id  IS THE COLOR OF THE LABELS!!
		draw color $cur_color_id
		set coord_y [expr $start_y+$i * $step_size ]
		set cur_text [expr $min + $i * $value_step ]

		draw text  " $coord_x $coord_y $use_z"  [format %6.2f  $cur_text]
	}


	# re-set top
	mol top $old_top
	display update on
}

proc ::ColorBar_v2::delete_color_scale_bar_v2 { } {
	variable bar_mol

	mol delete $bar_mol
}

