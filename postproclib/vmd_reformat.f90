!--------------------------------------------------------------------------------------------
!Re-format the file into binary with header used by .dcd file format

! This routine required only the number of molecules as a command line argument
! A python routine (vmd_reformat.py) should have been supplied to retreive this information
! from the header file for you. If not - you can get it from globalnp in simulation_header

!Written by Edward Smith & David Trevelyan

!--------------------------------------------------------------------------------------

module reformat_mod

contains

pure function strtod(s)
  real(kind=8) :: strtod
  character(len=*), intent(in) :: s
  character(len=32) :: fmt
  integer :: dot
  dot = index(s, ".")
  if(dot < 1) then
     write(fmt, '("(F",I0,".0)")') len_trim(s)
  else
     write(fmt, '("(F",I0,".",I0,")")') len_trim(s), len_trim(s)-dot
  end if
  read(s,fmt) strtod

end function strtod

!--------------------------------------------------------------------------------------
subroutine read_header(folder, np, domain)
	implicit none

	integer, intent(out)	:: np
	double precision, dimension(3), intent(out)	:: domain

    integer                 :: returncount = 4
    integer                 :: pos1, pos2, ierr
	real(kind(0.d0))        :: temp_num
	character(40)           :: temp_string1, temp_string2
	character(17)			:: filename
	character(217)			:: header_file
	character(200)			:: folder
    character(200)          :: line

	write (header_file,'(2a)') trim(folder), '/simulation_header'
	open(2,file=header_file,form='formatted', access='stream')
    print*, "Reading header information from ", header_file

	do 
		read(2,'(a)') line
        pos1 = index(line, ";")
        temp_string1 = line(1:pos1-1)
        pos2 = index(line(pos1+1:), ";") + pos1
        temp_string2 = line(pos1+1:pos2-1)
        read(line(pos2+1:), *, iostat=ierr) temp_num
        if (ierr .ne. 0) cycle !Error handle, skip this
		if (trim(adjustl(temp_string2)).eq.'globalnp') then
			np = int(temp_num)
			print*, "globalnp = ", np
            returncount = returncount - 1
		end if

		if (trim(adjustl(temp_string2)).eq.'globaldomain(1)') then
            domain(1) = temp_num
			print*, "Domain(1) = ", domain(1)
            returncount = returncount - 1
		end if

		if (trim(adjustl(temp_string2)).eq.'globaldomain(2)') then
			domain(2) = temp_num
			print*, "Domain(2) = ", domain(2)
            returncount = returncount - 1
		end if

		if (trim(adjustl(temp_string2)).eq.'globaldomain(3)') then
			domain(3) = temp_num
			print*, "Domain(3) = ", domain(3)
            returncount = returncount - 1
		end if

        if (returncount .eq. 0) exit

	end do

	close(2,status='keep')

end subroutine read_header

!--------------------------------------------------------------------------------------
subroutine read_final_state(np)
	implicit none

	integer, intent(out)	:: np

	character(20)			:: initial_microstate_file
 	integer(kind=selected_int_kind(18)) header_pos, end_pos ! 8 byte integer for header address

	initial_microstate_file = './../results/final_state'

	open(2,file=initial_microstate_file,form='unformatted', access='stream',position='append')

    inquire(2,POS=end_pos) 				! go the end of file
    read(2,pos=end_pos-8) header_pos 	! header start is in the last 8 bytes
    header_pos = header_pos +1 			! for compatibility with MPI IO we store header_pos - 1 in final state 

	read(2,pos=header_pos) np

	close(2,status='keep')

end subroutine read_final_state

!--------------------------------------------------------------------------------------
!Subroutine used to get size of file
subroutine get_file_size(filename,file_size)
	implicit none

	integer, parameter :: LongInt = selected_int_kind (18)
	integer(kind=LongInt),intent(out) :: file_size

	integer							:: unit_no
	integer,dimension(13)			:: SArray(13)
	logical							:: op
	character(len=*), intent(in)	:: filename

	! simpler version using inquire
	inquire(file=filename,size=file_size)

	!Check if unit number is used and assign unique number
	!do unit_no = 1,1000
	!	inquire(unit_no,opened=op)
	!	if (op .eqv. .false.) exit
	!enddo

	!Use Fstat to obtain size of file ## MAY BE COMPATABILITY ISSUE ##
	!open (unit=unit_no, file=filename)
	!call FStat(unit_no, SArray)
	!close(unit_no,status="keep")

	!file_size = SArray(8)

end subroutine get_file_size

!--------------------------------------------------------------------------------------
!Header added by David Trevelyan, DCD file format from:
!http://www.ks.uiuc.edu/Research/vmd/plugins/molfile/dcdplugin.html
!Information at the above url is a little misleading in places, comments below try to clarify. 

subroutine reformat_dcd(folder,filename,vmd_sets,np,domain,angle,delta_t_in,initialstep_in,tplot_in)
	implicit none

	character(len=*), intent(in)		:: folder,filename

	integer, intent(in)					:: vmd_sets
	integer, intent(in)					:: np		!--Number of atoms
	double precision, intent(in)		:: domain(3), angle(3)

	integer, intent(in),optional		:: initialstep_in,tplot_in
	double precision,intent(in),optional:: delta_t_in	!--Timestep between frames

    logical                         :: NEWFORMAT    !Flag to write new NAMD format (supports unitcell) or old X-PLOR
    integer                         :: NAMDVERSION  !Version integer for NAMD
	integer							:: initialstep,tplot

	double precision				:: delta_t	!--Timestep between frames
	integer							:: n, i			!--Dummy variables
	integer                         :: plot_mod
	integer							:: NSET			!--Number of frames
	integer							:: ISTRT		!--Starting frame
	integer							:: NSAVC		!--Number of frames per coordinate save
	integer							:: NATOMNFREAT		!--Number of fixed atoms
	integer							:: NTITLE		!--Number of 80-character strings in title (set as 2)
	integer							:: NATOM		!--Number of atoms
	integer							:: UNITCELL		!--Write unitcell data
	integer, parameter 				:: LongInt = selected_int_kind (18)
	integer(kind=LongInt)			:: bufsize, starti, endi
	integer, dimension (5)			:: FIVEZ		!--According to documentation, five zeros, but first is actually NSET
	integer, dimension (8)			:: EIGHTZ		!--Nine zeros
	character(len=4)				:: HDR			!--Header string, value 'CORD'
	character(len=80), dimension(2)	:: TITLE	        !--Title(s)
	real 							:: time_start, time_end
	real,allocatable,dimension(:)   :: Xbuf, Ybuf, Zbuf	!--Buffers used to copy from direct access to binary
	integer            				:: DELTAf		!--Timestep between frames
	double precision				:: DELTA		!--Timestep between frames
	character(256)					:: filename_out

	!Set defaults - I'm not convinced these do anything anyway
	if (.not. present(delta_t_in)) then
		delta_t = 0.005d0
	else 
		delta_t = delta_t_in
	endif
	if (.not. present(initialstep_in)) then
		initialstep = 0
	else 
		initialstep = initialstep_in
	endif
	if (.not. present(tplot_in)) then
		tplot = 1
	else
		tplot = tplot_in
	endif

	print*, 'Initialising trajectory file reformat to *.dcd. For large'
	print*, 'systems or long runs this may take some time...' 
	
	call cpu_time(time_start)

	!Set header information	
	HDR			=	'CORD'				!header text
	NSET		=	vmd_sets			!number of recorded frames
	ISTRT		=	initialstep			!the starting timestep
	NSAVC		=	tplot				!number of timesteps between dcd frame saves
	FIVEZ(1)	=	NSET				!not sure why
	FIVEZ(2:5)	=	0					!buffer zeros
	NATOMNFREAT	=	0					!number of fixed atoms?
	DELTA		=	delta_t				!delta_t (x-plor is double, charmm is real)
    DELTAf      =   DELTA               !Real version for charm
	EIGHTZ(:)	=	0					!buffer zeros
	NTITLE		=	2					!number of 80-character strings in title
	TITLE(1)	=	'  Simulation record file '	!
	TITLE(2)    =	'   Written in serial or parallel   '	!
	NATOM		=	np			!number of particles
    UNITCELL    =   1           !Write unit cell data
    NAMDVERSION =   22          !Anything non-zero works here

	!Get size of arrays required to store data
	bufsize = NSET*np
	allocate(Xbuf(bufsize))
	allocate(Ybuf(bufsize))
	allocate(Zbuf(bufsize))

	!Read position information from file
	!RECORD LENGTH IS 1 WHICH IN FORTRAN IS A 4 BYTE BLOCKS (REAL, INT BUT NOT DP) 	
	open (unit=17, file=filename,access='stream')
    
	!Open unit 6 (stdout) with fortran carriage control 
	open (unit=6)  
	plot_mod = max(1,NSET/100)
	write(*,'(a)') ' VMD reformat read completion:  '

	!Read temp trajectory file
	do i=1,NSET
		starti = np*(i-1)+1
		endi   = np*i
		read(17) Xbuf(starti:endi)
		read(17) Ybuf(starti:endi)
		read(17) Zbuf(starti:endi)
		if (mod(i,plot_mod) .eq. 0) then
			call progress(100*i/NSET)
		end if
	enddo

	close(17)

	!Open binary .dcd file and write header information	
	write (filename_out,'(2a)') trim(folder), "vmd_out.dcd"	
	open(unit=3, file=trim(filename_out),status='replace', form="unformatted")

    !Note here, FORTRAN writes the header size of the first call to write as the first record in the file.
    !DCD plugin checks to ensure this is 84. The size is 84 if we have 21 single precision numbers (4 bytes * 21)
    !Where last is NAMD version No. or 19 single precision numbers and DELTA which is double in X-PLOR
    NEWFORMAT = .true.
    if (NEWFORMAT) then
    	write(3) HDR, NSET, ISTRT, NSAVC, FIVEZ, NATOMNFREAT, DELTAf, UNITCELL, EIGHTZ, NAMDVERSION
    else 
    	write(3) HDR, NSET, ISTRT, NSAVC, FIVEZ, NATOMNFREAT, DELTA, UNITCELL, EIGHTZ
    endif
	write(3) NTITLE, TITLE(1), TITLE(2)
	write(3) NATOM

	write(*,'(a)') ' VMD reformat write completion: '
	do i=1,NSET
		starti = (i-1)*np+1
		endi   = i*np
        if (UNITCELL .eq. 1) then
		    write(3) domain(1), angle(1), domain(2), angle(2), angle(3), domain(3)
        endif
		write(3) Xbuf(starti:endi)
		write(3) Ybuf(starti:endi)
		write(3) Zbuf(starti:endi)
		if (mod(i,plot_mod) .eq. 0) then
			call progress(100*i/NSET)
		end if
	enddo

	close(3,status='keep')

	deallocate(Xbuf)
	deallocate(Ybuf)
	deallocate(Zbuf)

	call cpu_time(time_end)

 	print '(a,g10.2,a)', ' Reformatted to *.dcd in', time_end - time_start, ' seconds.'

end subroutine reformat_dcd

!--------------------------------------------------------------------------------------
!Print progress bar to screen
subroutine progress(j)  
implicit none  

	integer(kind=4)   :: j,k,bark
	character(len=78) :: bar

	bar(1:7) = " ???% |"
	do k=8,77
	bar(k:k) = " "
	end do
	bar(78:78) = "|"

	write(unit=bar(2:4),fmt="(i3)") j

	bark = int(dble(j)*70.d0/100.d0)

	do k=1,bark
	bar(7+k:7+k)=char(2) 
	enddo  

	! print the progress bar.  
	write(unit=6,fmt="(a1,a1,a78)") '+',char(13), bar  

	return  

end subroutine progress 

end module reformat_mod


!====================================================================================
program vmd_reformat
	use reformat_mod
	implicit none

	integer, parameter 		:: LongInt = selected_int_kind (18)
	integer(kind=LongInt) 	:: file_size
	integer					:: np, vmd_outflag,vmd_steps,datasize
	character(40) 			:: npstring
	character(256) 			:: folder,filestring,filename,filepath, inputmsg

    double precision, dimension(3)        :: domain, angles

    !Cubic unit cell, can't see a reason to go beyond this
    angles = (/90.d0, 90.d0, 90.d0 /)

	!Set Constants
    inputmsg = 'Input should be in the form ./vmd_reformat.exe [folder] [filename] &
                [no. of particles] [xdomainsize] [ydomainsize] [zdomainsize]'
	call get_command_argument(1,filestring)
	if (filestring .eq. '') then
		print*, inputmsg
		stop "Error - No input argument supplied for folder"
	endif
    folder = trim(filestring)

	call get_command_argument(2,filestring)
	if (filestring .eq. '') then
		print*, inputmsg
		print*, 'Assuming vmd_temp.dcd and attempting to read simultation_header'
        call read_header(folder, np, domain)
    else
        filename = trim(filestring)
	    write (filepath,'(2a)') trim(folder), trim(filename)
	endif
    datasize = 4

	!Get paramters required from input line
	call get_command_argument(3,npstring)
	if (npstring .eq. '') then
		print*, inputmsg
		print*, 'Attempting to read simultation_header for globabnp and domain'
        call read_header(folder, np, domain)
    else
        ! Convert string to a numeric value
        read (npstring,'(i10)') np
	endif

	!Get paramters required from input line
	call get_command_argument(4,npstring)
	if (npstring .eq. '') then
		print*, inputmsg
		print*, 'Attempting to read simultation_header for domain'
        call read_header(folder, np, domain)
    else
        ! Convert string to a numeric value
        domain(1) = strtod(npstring)
    	call get_command_argument(5,npstring)
        domain(2) = strtod(npstring)
    	call get_command_argument(6,npstring)
        domain(3) = strtod(npstring)
	endif


    ! Calculate number of steps using filesize
	call get_file_size(filepath,file_size)
	vmd_steps = file_size/(datasize*3*np)
	print'(3(a,i8),a, a, 3f10.5)', ' Number of molecules = ', np, & 
					    ' Number of steps = ', vmd_steps,  & 
						' Filesize ', file_size/(1024**2), ' Mb ', &
					    ' domain = ', domain


	!Reformat recorded positions into the correct form for VMD .dcd format
	vmd_outflag = 1
	select case (vmd_outflag)
	case(0)
	case(1)
		call reformat_dcd(folder,filepath,vmd_steps,np,domain,angles)
	case(2)
		!call reformat_dcd_sl
	case(3)
		!call reformat_dcd
		!call reformat_dcd_halo
	case(4)
		!call reformat_dcd_true
	case default
	end select 

	!if (vmd_outflag.ne.0 .and. potential_flag.eq.1) call build_psf

end program

!====================================================================================
